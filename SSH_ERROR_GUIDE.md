# SSH Garbage Packet Error - Nguyên nhân và cách khắc phục

## Nguyên nhân chính của lỗi "garbage packet error":

### 1. Vấn đề mạng
- **Kết nối mạng không ổn định**: Mất gói tin, độ trễ cao
- **Tường lửa can thiệp**: Firewall hoặc proxy thay đổi gói tin SSH
- **MTU size không phù hợp**: Gói tin quá lớn bị phân mảnh

### 2. Cấu hình SSH server
- **SSH server quá tải**: Quá nhiều kết nối đồng thời
- **Timeout ngắn**: Server đóng kết nối sớm
- **Cipher không tương thích**: Thuật toán mã hóa xung đột

### 3. Vấn đề phần cứng
- **Router/Switch lỗi**: Thiết bị mạng hoạt động không ổn định
- **Network interface card**: Card mạng máy client hoặc server bị lỗi

## Cách khắc phục đã tích hợp:

### 1. Retry mechanism (Đã thêm)
- Tự động thử lại 3 lần khi gặp lỗi
- Reconnect SSH connection nếu cần
- Delay 2 giây giữa các lần thử

### 2. Optimized SSH settings (Đã thêm)
- Tăng timeout: banner_timeout=60, auth_timeout=60
- Disable weak algorithms
- Tối ưu hóa cipher và key exchange

### 3. Better error handling (Đã thêm)
- Phân loại lỗi chi tiết
- Log rõ ràng để debug
- Graceful degradation

## Khuyến nghị thêm:

### 1. Cấu hình server SSH (/etc/ssh/sshd_config):
```bash
# Tăng giới hạn kết nối
MaxSessions 50
MaxStartups 30

# Tăng timeout
ClientAliveInterval 60
ClientAliveCountMax 3

# Optimize ciphers
Ciphers aes128-ctr,aes192-ctr,aes256-ctr
MACs hmac-sha2-256,hmac-sha2-512
```

### 2. Cấu hình client SSH (~/.ssh/config):
```bash
Host your-server
    HostName 192.168.1.100
    User your-username
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    Compression yes
```

### 3. Kiểm tra mạng:
```bash
# Test ping
ping -c 10 your-server-ip

# Test MTU
ping -M do -s 1472 your-server-ip

# Test SSH connection
ssh -vvv user@server
```

### 4. Nếu vẫn gặp lỗi thường xuyên:
- Giảm số file download đồng thời
- Tăng timeout trong config.yaml
- Sử dụng SSH key thay vì password
- Kiểm tra network hardware

## Cấu hình khuyến nghị trong config.yaml:
```yaml
settings:
  max_concurrent_transfers: 2  # Giảm từ 5 xuống 2
  retry_attempts: 5            # Tăng từ 3 lên 5
  connection_timeout: 60       # Tăng từ 30 lên 60
```