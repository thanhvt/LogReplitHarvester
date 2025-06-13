"""
Module hỗ trợ copy file từ server về máy local thông qua SCP
Đơn giản, nhanh chóng, và tránh lỗi 'Garbage packet received'
"""

import os
import subprocess
import logging
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)

def copy_with_paramiko(
    server_info: dict,
    remote_path: str,
    local_path: str,
    progress_callback: Optional[Callable] = None
) -> bool:
    """
    Copy file bằng Paramiko SFTP với xử lý lỗi nâng cao
    Sử dụng cho cả key file và password authentication
    
    Tham số đầu vào:
      - server_info: Thông tin server (host, port, username, password hoặc key_file)
      - remote_path: Đường dẫn file trên server
      - local_path: Đường dẫn file để lưu ở local
      - progress_callback: Hàm callback báo tiến độ tải
      
    Tham số đầu ra:
      - bool: True nếu copy thành công, False nếu có lỗi
    """
    import paramiko
    
    # Đảm bảo thư mục đích tồn tại
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    # Biến theo dõi để xử lý lỗi và khôi phục
    error_count = 0
    max_errors = 3
    current_pos = 0
    
    # Tạo file tạm để có thể tiếp tục nếu bị gián đoạn
    temp_path = f"{local_path}.part"
    
    # Khôi phục tiến độ nếu file tạm tồn tại
    if os.path.exists(temp_path):
        current_pos = os.path.getsize(temp_path)
        mode = 'ab'  # chế độ append
        logger.info(f"Tiếp tục copy từ vị trí: {current_pos:,} bytes")
    else:
        mode = 'wb'  # chế độ write mới
    
    # Lấy thông tin server
    host = server_info.get('host')
    port = server_info.get('port', 22)
    username = server_info.get('username')
    password = server_info.get('password')
    key_file = server_info.get('key_file')
    
    try:
        # Khởi tạo kết nối SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Kết nối SSH với server
        if key_file and os.path.exists(key_file):
            # Sử dụng key file để xác thực
            key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh_client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=key,
                timeout=30
            )
        else:
            # Sử dụng password để xác thực
            ssh_client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=30
            )
        
        # Tạo kết nối SFTP
        sftp_client = ssh_client.open_sftp()
        
        try:
            # Lấy thông tin file
            stat_info = sftp_client.stat(remote_path)
            total_size = stat_info.st_size
            logger.info(f"Bắt đầu copy file: {remote_path} ({total_size:,} bytes)")
            
            # Nếu đã tải xong rồi, chỉ cần đổi tên file
            if current_pos >= total_size and os.path.exists(temp_path):
                os.replace(temp_path, local_path)
                logger.info(f"File đã tải xong trước đó")
                return True
            
            # Copy file với xử lý từng đoạn nhỏ
            chunk_size = 16384  # 16KB chunks
            
            with sftp_client.open(remote_path, 'rb') as remote_file:
                with open(temp_path, mode) as local_file:
                    # Di chuyển đến vị trí cần đọc tiếp
                    if current_pos > 0:
                        remote_file.seek(current_pos)
                    
                    # Đọc và ghi file theo từng đoạn
                    downloaded = current_pos
                    while True:
                        try:
                            chunk = remote_file.read(chunk_size)
                            if not chunk:
                                break
                                
                            local_file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Báo tiến độ
                            if progress_callback:
                                progress_callback(downloaded, total_size)
                                
                            # Làm mới kết nối SFTP sau mỗi 5MB
                            if downloaded % (5 * 1024 * 1024) < chunk_size and downloaded > chunk_size:
                                remote_file.flush()
                                
                            # Tạm dừng sau mỗi 10 chunks để tránh quá tải
                            if downloaded % (chunk_size * 10) < chunk_size and downloaded > chunk_size:
                                time.sleep(0.01)  # 10ms pause
                                
                        except Exception as e:
                            # Xử lý lỗi khi đang copy
                            error_count += 1
                            if error_count <= max_errors:
                                logger.warning(f"Lỗi khi copy lần {error_count}/{max_errors}: {e}")
                                time.sleep(error_count * 1)  # Nghỉ 1, 2, 3 giây
                                
                                # Thử làm mới kết nối SFTP
                                try:
                                    sftp_client = ssh_client.open_sftp()
                                    remote_file = sftp_client.open(remote_path, 'rb')
                                    remote_file.seek(downloaded)
                                except Exception:
                                    pass
                            else:
                                logger.error(f"Quá nhiều lỗi khi copy file")
                                raise
            
            # Đổi tên file tạm thành file đích khi hoàn tất
            os.replace(temp_path, local_path)
            logger.info(f"Đã copy xong file: {downloaded:,}/{total_size:,} bytes")
            return True
            
        finally:
            # Đảm bảo đóng kết nối SFTP
            try:
                sftp_client.close()
            except:
                pass
            
    except Exception as e:
        logger.error(f"Lỗi không mong đợi khi copy file: {e}")
        return False
        
    finally:
        # Đảm bảo đóng kết nối SSH
        try:
            ssh_client.close()
        except:
            pass
