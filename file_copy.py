"""
Module hỗ trợ copy file từ server về máy local thông qua SCP
Đơn giản, nhanh chóng, và tránh lỗi 'Garbage packet received'
"""

import os
import subprocess
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

def copy_file_from_server(
    server_info: dict,
    remote_path: str,
    local_path: str,
    progress_callback: Optional[Callable] = None
) -> bool:
    """
    Copy file từ server về local thông qua SCP command
    
    Tham số đầu vào:
      - server_info: Thông tin server (host, port, username, password/key_file)
      - remote_path: Đường dẫn file trên server
      - local_path: Đường dẫn file để lưu ở local
      - progress_callback: Hàm callback để báo tiến độ (không hỗ trợ trong SCP)
      
    Tham số đầu ra:
      - bool: True nếu copy thành công, False nếu có lỗi
    """
    # Đảm bảo thư mục đích tồn tại
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    try:
        # Tạo lệnh SCP
        host = server_info.get('host')
        port = server_info.get('port', 22)
        username = server_info.get('username')
        key_file = server_info.get('key_file')
        
        scp_command = ['scp', '-P', str(port)]
        
        # Thêm key file nếu có
        if key_file and os.path.exists(key_file):
            scp_command.extend(['-i', key_file])
            
        # Tạo path theo định dạng SCP: username@host:path
        remote_source = f"{username}@{host}:{remote_path}"
        scp_command.extend([remote_source, local_path])
        
        # Thực hiện lệnh SCP
        logger.info(f"Bắt đầu copy file: {remote_path} về {local_path}")
        process = subprocess.run(
            scp_command, 
            capture_output=True, 
            text=True
        )
        
        # Kiểm tra kết quả
        if process.returncode == 0:
            logger.info(f"Đã copy thành công file: {remote_path}")
            return True
        else:
            logger.error(f"Lỗi SCP: {process.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Lỗi không mong đợi khi copy file: {e}")
        return False
        
def copy_with_expect(
    server_info: dict,
    remote_path: str,
    local_path: str
) -> bool:
    """
    Copy file bằng expect script để tự động nhập mật khẩu
    Sử dụng khi cần xác thực bằng password thay vì key
    
    Tham số đầu vào:
      - server_info: Thông tin server (host, port, username, password)
      - remote_path: Đường dẫn file trên server
      - local_path: Đường dẫn file để lưu ở local
      
    Tham số đầu ra:
      - bool: True nếu copy thành công, False nếu có lỗi
    """
    try:
        # Đảm bảo thư mục đích tồn tại
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Lấy thông tin server
        host = server_info.get('host')
        port = server_info.get('port', 22)
        username = server_info.get('username')
        password = server_info.get('password', '')
        
        # Tạo expect script
        expect_script = f"""
        #!/usr/bin/expect -f
        set timeout 600
        spawn scp -P {port} {username}@{host}:{remote_path} {local_path}
        expect {{
            "yes/no" {{ send "yes\\r"; exp_continue }}
            "password:" {{ send "{password}\\r" }}
        }}
        expect eof
        """
        
        # Lưu script vào file tạm
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.exp', delete=False) as f:
            f.write(expect_script)
            temp_script = f.name
        
        # Cấp quyền thực thi
        os.chmod(temp_script, 0o700)
        
        # Thực thi script
        logger.info(f"Bắt đầu copy file với password: {remote_path}")
        process = subprocess.run(
            [temp_script],
            capture_output=True,
            text=True
        )
        
        # Xóa file tạm
        try:
            os.unlink(temp_script)
        except:
            pass
        
        # Kiểm tra kết quả
        if process.returncode == 0 and os.path.exists(local_path):
            logger.info(f"Đã copy thành công file: {remote_path}")
            return True
        else:
            logger.error(f"Lỗi copy với expect: {process.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Lỗi không mong đợi khi copy file: {e}")
        return False
