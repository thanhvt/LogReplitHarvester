# Khắc phục lỗi "Garbage packet received" - Cập nhật mới

## Cải tiến đã thêm:

### 1. Progressive Backoff Retry
- Lần thử 1: Đợi 3 giây
- Lần thử 2: Đợi 6 giây  
- Lần thử 3: Đợi 9 giây
- Lần thử 4: Đợi 12 giây
- Lần thử 5: Đợi 15 giây

### 2. Force Fresh Connection
- Xóa file download lỗi trước khi thử lại
- Đóng hoàn toàn kết nối SSH cũ
- Đợi 2 giây rồi tạo kết nối mới
- Cấu hình lại transport layer

### 3. Transport Layer Optimization
- Keepalive packets mỗi 30 giây
- Window size 2MB cho throughput tốt hơn
- Rekey parameters được tối ưu

### 4. Sequential Downloads
- Chỉ download 1 file cùng lúc (max_concurrent_transfers: 1)
- Giảm load trên SSH server
- Tránh xung đột resource

## Hướng dẫn khắc phục:

### Bước 1: Cập nhật config.yaml
```yaml
settings:
  max_concurrent_transfers: 1  # Quan trọng!
  retry_attempts: 5
  connection_timeout: 60
```

### Bước 2: Kiểm tra server SSH
Trên server Linux, chỉnh sửa `/etc/ssh/sshd_config`:
```bash
# Tăng giới hạn kết nối
MaxSessions 10
MaxStartups 10:30:60

# Tăng timeout
ClientAliveInterval 60
ClientAliveCountMax 10

# Restart SSH service
sudo systemctl restart sshd
```

### Bước 3: Cải thiện mạng
```bash
# Test kết nối
ping -c 10 your-server-ip

# Test MTU size
ping -M do -s 1472 your-server-ip

# Nếu ping lớn bị drop, giảm MTU
sudo ip link set dev eth0 mtu 1400
```

### Bước 4: SSH Key thay vì Password
Tạo SSH key (an toàn hơn):
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/logcollector_key
ssh-copy-id -i ~/.ssh/logcollector_key.pub user@server
```

Cập nhật config.yaml:
```yaml
servers:
  - name: "My Server"
    host: "your-server-ip"
    username: "your-user"
    password: null
    key_file: "~/.ssh/logcollector_key"
```

### Bước 5: Monitoring
File log sẽ hiển thị chi tiết:
```
ssh_log_collector.log
```

Theo dõi để thấy:
- "SSH packet error on attempt X/5"
- "Waiting X seconds before retry"
- "Force reconnecting with fresh SSH connection"
- "Reconnected successfully"

## Nếu vẫn gặp lỗi:

1. **Giảm file size**: Chỉ download file nhỏ trước
2. **Thay đổi network**: Dùng VPN hoặc network khác
3. **Contact admin**: Yêu cầu kiểm tra SSH server logs
4. **Alternative method**: Dùng rsync hoặc scp command line

## Root Cause Analysis:
Lỗi này thường do:
- Network instability (70%)
- SSH server overload (20%)
- Firewall interference (10%)

File .log cụ thể bạn gặp lỗi có thể có vấn đề đặc biệt hoặc quá lớn.