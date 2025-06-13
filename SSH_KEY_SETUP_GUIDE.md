# Hướng dẫn Setup SSH Key cho SSH Log Collector

## Tại sao dùng SSH Key?
- **An toàn hơn** password authentication
- **Ổn định hơn** - ít bị lỗi "garbage packet"
- **Tự động hóa** - không cần nhập password mỗi lần
- **Hiệu suất tốt hơn** cho file lớn 40-50MB

## Bước 1: Tạo SSH Key trên máy macOS

### Tạo SSH Key mới:
```bash
# Tạo SSH key (thay email của bạn)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Khi được hỏi file location, nhấn Enter để dùng default:
# /Users/your_username/.ssh/id_rsa

# Khi được hỏi passphrase:
# - Nhấn Enter để không dùng passphrase (đơn giản hơn)
# - Hoặc nhập passphrase để bảo mật cao hơn
```

### Kiểm tra SSH Key đã tạo:
```bash
# Xem danh sách SSH keys
ls -la ~/.ssh/

# Bạn sẽ thấy:
# id_rsa       (private key - KHÔNG chia sẻ)
# id_rsa.pub   (public key - cần copy lên server)
```

## Bước 2: Copy Public Key lên Server Linux

### Cách 1: Sử dụng ssh-copy-id (khuyến nghị)
```bash
# Thay thế user và server_ip của bạn
ssh-copy-id user@192.168.1.100

# Nhập password của server một lần cuối
# Key sẽ được tự động copy vào ~/.ssh/authorized_keys trên server
```

### Cách 2: Copy thủ công
```bash
# Xem nội dung public key
cat ~/.ssh/id_rsa.pub

# Copy toàn bộ text output (bắt đầu với ssh-rsa...)
# SSH vào server và thêm vào file authorized_keys:

ssh user@192.168.1.100
mkdir -p ~/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAA... your_email@example.com" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
exit
```

## Bước 3: Test SSH Key

```bash
# Test kết nối không cần password
ssh user@192.168.1.100

# Nếu thành công, bạn sẽ login không cần nhập password
# Nếu vẫn hỏi password, kiểm tra lại các bước trên
```

## Bước 4: Cập nhật config.yaml

```yaml
servers:
  - name: "My Linux Server"
    host: "192.168.1.100"        # IP server của bạn
    port: 22
    username: "your_username"    # Username SSH
    password: null               # Đặt null khi dùng SSH key
    key_file: "~/.ssh/id_rsa"    # Đường dẫn SSH private key
    passphrase: null             # null nếu không dùng passphrase
    timeout: 60
```

## Troubleshooting

### Lỗi "Permission denied (publickey)"
```bash
# Kiểm tra quyền file
ls -la ~/.ssh/
# id_rsa phải có quyền 600
# id_rsa.pub phải có quyền 644

chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

### Lỗi trên server
```bash
# SSH vào server và kiểm tra
ssh user@server_ip
ls -la ~/.ssh/
# authorized_keys phải có quyền 600
# .ssh folder phải có quyền 700

chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Lỗi SELinux (CentOS/RHEL)
```bash
# Trên server
restorecon -R ~/.ssh
```

## Lưu ý bảo mật

1. **KHÔNG bao giờ chia sẻ private key** (id_rsa)
2. **Backup SSH key** ở nơi an toàn
3. **Sử dụng passphrase** cho private key nếu môi trường yêu cầu
4. **Rotate key định kỳ** (6-12 tháng một lần)

## Kiểm tra cuối cùng

```bash
# Test SSH Log Collector với SSH key
python3 main.py

# Chọn server và thử download
# Không cần nhập password nữa
# File lớn 40-50MB sẽ download ổn định hơn
```