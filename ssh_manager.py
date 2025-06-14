"""
SSH Connection Management for SSH Log Collector
Handles SSH connections, authentication, and SFTP operations.
"""

import os
import stat
import socket
import logging
import paramiko
from pathlib import Path
import fnmatch
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from rich.console import Console

# Import module copy file mới
from file_copy import copy_with_paramiko

console = Console()
logger = logging.getLogger(__name__)

class SSHConnection:
    """Manages SSH/SFTP connections to remote servers"""
    
    def __init__(self, server_config: Dict[str, Any]):
        self.config = server_config
        self.ssh_client = None
        self.sftp_client = None
        self.connected = False
        
    def connect(self) -> bool:
        """Establish SSH connection to the server"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Prepare connection parameters with optimized settings
            connect_params = {
                'hostname': self.config['host'],
                'port': self.config.get('port', 22),
                'username': self.config['username'],
                'timeout': self.config.get('timeout', 30),
                'banner_timeout': 60,  # Increase banner timeout
                'auth_timeout': 60,    # Increase auth timeout
                'sock': None,          # Use default socket
                'gss_auth': False,     # Disable GSS authentication
                'gss_kex': False,      # Disable GSS key exchange
                'disabled_algorithms': {
                    'kex': ['diffie-hellman-group1-sha1'],  # Disable weak algorithms
                    'cipher': ['blowfish-cbc', '3des-cbc']
                }
            }
            
            # Handle authentication
            if self.config.get('key_file'):
                # SSH key authentication
                key_file = os.path.expanduser(self.config['key_file'])
                if not os.path.exists(key_file):
                    console.print(f"[red]SSH key file not found: {key_file}[/red]")
                    return False
                
                try:
                    passphrase = self.config.get('passphrase')
                    if key_file.endswith('.pem'):
                        pkey = paramiko.RSAKey.from_private_key_file(key_file, password=passphrase)
                    else:
                        # Try different key types
                        for key_class in [paramiko.RSAKey, paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                            try:
                                pkey = key_class.from_private_key_file(key_file, password=passphrase)
                                break
                            except Exception:
                                continue
                        else:
                            console.print(f"[red]Unable to load SSH key: {key_file}[/red]")
                            return False
                    
                    connect_params['pkey'] = pkey
                    
                except Exception as e:
                    console.print(f"[red]Error loading SSH key: {e}[/red]")
                    return False
            
            elif self.config.get('password'):
                # Password authentication
                connect_params['password'] = self.config['password']
            else:
                console.print(f"[red]No authentication method configured for {self.config['name']}[/red]")
                return False
            
            # Connect to server
            self.ssh_client.connect(**connect_params)
            
            # Create SFTP client with optimized settings
            self.sftp_client = self.ssh_client.open_sftp()
            
            # Configure SFTP for better stability
            transport = self.ssh_client.get_transport()
            if transport:
                # Set keepalive to prevent connection drops
                transport.set_keepalive(30)
                # Increase window size for better performance
                transport.default_window_size = 2097152  # 2MB window
                transport.packetizer.REKEY_BYTES = pow(2, 40)
                transport.packetizer.REKEY_PACKETS = pow(2, 40)
            
            self.connected = True
            logger.info(f"Successfully connected to {self.config['name']} ({self.config['host']})")
            return True
            
        except paramiko.AuthenticationException:
            console.print(f"[red]Authentication failed for {self.config['name']}[/red]")
            return False
        except paramiko.SSHException as e:
            console.print(f"[red]SSH connection error for {self.config['name']}: {e}[/red]")
            return False
        except socket.timeout:
            console.print(f"[red]Connection timeout for {self.config['name']}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Connection error for {self.config['name']}: {e}[/red]")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None
            
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            
            self.connected = False
            logger.info(f"Disconnected from {self.config['name']}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.config['name']}: {e}")
    
    def list_files(self, directory_path: str, file_pattern: str = "*", 
                   recursive: bool = False, time_filter: Optional[datetime] = None, 
                   time_filter_end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """List files in directory matching criteria"""
        if not self.connected or not self.sftp_client:
            raise Exception("Not connected to server")
        
        files = []
        
        try:
            self._list_files_recursive(directory_path, file_pattern, recursive, time_filter, files, time_filter_end)
        except Exception as e:
            logger.error(f"Error listing files in {directory_path}: {e}")
            raise
        
        return files
    
    def _list_files_recursive(self, path: str, pattern: str, recursive: bool, 
                            time_filter: Optional[datetime], files: List[Dict[str, Any]], 
                            time_filter_end: Optional[datetime] = None):
        """Recursively list files matching criteria"""
        try:
            for item in self.sftp_client.listdir_attr(path):
                item_path = f"{path}/{item.filename}".replace('//', '/')
                
                if stat.S_ISDIR(item.st_mode):
                    # Directory
                    if recursive:
                        self._list_files_recursive(item_path, pattern, recursive, time_filter, files, time_filter_end)
                else:
                    # File
                    if fnmatch.fnmatch(item.filename, pattern):
                        # Kiểm tra bộ lọc thời gian
                        file_mtime = datetime.fromtimestamp(item.st_mtime)
                        logger = logging.getLogger(__name__)
                        
                        logger.debug(f"File: {item.filename}, Path: {item_path}")
                        logger.debug(f"  - File mtime: {file_mtime} ({file_mtime.strftime('%d/%m/%Y %H:%M:%S')})")
                        
                        # Bộ lọc ngày đơn (các file được sửa đổi sau ngày này)
                        if time_filter:
                            logger.debug(f"  - Time filter: {time_filter} ({time_filter.strftime('%d/%m/%Y %H:%M:%S')})")
                            if file_mtime < time_filter:
                                # logger.debug(f"  - SKIP: File quá cũ (mtime < time_filter)")
                                continue
                        
                        # Bộ lọc khoảng ngày (các file được sửa đổi giữa ngày bắt đầu và kết thúc)
                        if time_filter_end:
                            logger.debug(f"  - Time filter end: {time_filter_end} ({time_filter_end.strftime('%d/%m/%Y %H:%M:%S')})")
                            if file_mtime > time_filter_end:
                                # logger.debug(f"  - SKIP: File quá mới (mtime > time_filter_end)")
                                continue
                        
                        logger.debug(f"  - ACCEPTED: File nằm trong khoảng thời gian lọc")
                        
                        files.append({
                            'path': item_path,
                            'name': item.filename,
                            'size': item.st_size,
                            'mtime': file_mtime,
                            'mode': item.st_mode
                        })
        
        except PermissionError:
            logger.warning(f"Permission denied accessing {path}")
        except Exception as e:
            logger.error(f"Error accessing {path}: {e}")
    
    def download_file(self, remote_path: str, local_path: str, progress_callback=None, max_retries: int = 3, chunk_size: int = 32768) -> bool:
        """
        Copy file từ server về máy local
        
        Tham số đầu vào:
          - remote_path: Đường dẫn file trên server
          - local_path: Đường dẫn file để lưu ở local
          - progress_callback: Hàm callback báo tiến độ (không dùng với SCP)
          - max_retries: Số lần thử lại tối đa
          - chunk_size: Không sử dụng với cơ chế copy
          
        Tham số đầu ra:
          - bool: True nếu copy thành công, False nếu có lỗi
        
        Khi nào gọi hàm:
          - Được gọi từ FileTransferManager để copy file từ server
        """
        if not self.connected:
            raise Exception("Not connected to server")
        
        # Đảm bảo thư mục local tồn tại
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Tạo thông tin server để dùng với module copy
        server_info = {
            'host': self.config['host'],
            'port': self.config.get('port', 22),
            'username': self.config['username'],
            'password': self.config.get('password')
            # Đã bỏ key_file vì chỉ dùng user/pass
        }
        
        logger.info(f"Bắt đầu copy file {remote_path} về {local_path}")
        
        # Thử copy file với nhiều cách khác nhau
        for attempt in range(max_retries):
            try:
                # Chỉ dùng Paramiko SFTP với xử lý lỗi nâng cao
                # Dùng xác thực user/pass
                if self.config.get('password'):
                    logger.info(f"Thử copy file với Paramiko SFTP nâng cao (lần {attempt+1}/{max_retries})")
                    if copy_with_paramiko(server_info, remote_path, local_path, progress_callback):
                        return True
                        
                # Phương pháp dự phòng: Sử dụng SFTP cũ (legacy) nếu cách trên không được
                else:
                    logger.info(f"Thử download file thủ công với SFTP (lần {attempt+1}/{max_retries})")
                    if not self.sftp_client:
                        self.sftp_client = self.ssh_client.open_sftp()
                    
                    # Download file bình thường qua SFTP
                    self.sftp_client.get(remote_path, local_path)
                    logger.info(f"Đã copy file {remote_path} về {local_path} qua SFTP")
                    return True
                    
            except Exception as e:
                logger.warning(f"Lỗi khi copy lần {attempt+1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    # Chờ và thử lại
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Chờ {wait_time} giây trước khi thử lại...")
                    time.sleep(wait_time)
                    
                    # Thử kết nối lại
                    logger.info("Khởi tạo lại kết nối SSH...")
                    self.disconnect()
                    time.sleep(1)
                    
                    if self.connect():
                        logger.info("Kết nối lại thành công")
                    else:
                        logger.error("Không thể kết nối lại")
                else:
                    logger.error(f"Đã thử tất cả các phương pháp, không thể copy file: {e}")
                    return False
        
        return False
    
    def _is_large_file(self, remote_path: str) -> bool:
        """Check if file is large (>10MB) and needs chunked download"""
        try:
            stat_info = self.sftp_client.stat(remote_path)
            file_size = stat_info.st_size
            return file_size > 10 * 1024 * 1024  # 10MB threshold
        except:
            return False
    
    def get_file_stat(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get file statistics"""
        if not self.connected or not self.sftp_client:
            return None
        
        try:
            stat_info = self.sftp_client.stat(remote_path)
            return {
                'size': stat_info.st_size,
                'mtime': datetime.fromtimestamp(stat_info.st_mtime),
                'mode': stat_info.st_mode
            }
        except Exception as e:
            logger.error(f"Error getting file stat for {remote_path}: {e}")
            return None

class SSHManager:
    """Manages multiple SSH connections"""
    
    def __init__(self):
        self.connections: Dict[str, SSHConnection] = {}
    
    def create_connection(self, server_name: str, server_config: Dict[str, Any]) -> SSHConnection:
        """Create and store SSH connection"""
        connection = SSHConnection(server_config)
        self.connections[server_name] = connection
        return connection
    
    def get_connection(self, server_name: str) -> Optional[SSHConnection]:
        """Get existing connection"""
        return self.connections.get(server_name)
    
    def disconnect_all(self):
        """Disconnect all SSH connections"""
        for connection in self.connections.values():
            connection.disconnect()
        self.connections.clear()
    
    def __del__(self):
        """Cleanup connections on object destruction"""
        self.disconnect_all()
