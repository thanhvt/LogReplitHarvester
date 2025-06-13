# SSH Log Collector - Quick Start Guide

## 🚀 Cách nhanh nhất có file .exe

### Bước 1: Tạo GitHub Repository (2 phút)
1. Vào https://github.com → Đăng nhập/Đăng ký
2. Click **"New"** → Tên: `ssh-log-collector` → **"Create repository"**

### Bước 2: Upload code (3 phút)
1. Click **"uploading an existing file"** trong repository
2. Kéo thả TẤT CẢ file từ project này vào (quan trọng: bao gồm thư mục `.github`)
3. Commit message: "Add SSH Log Collector"
4. Click **"Commit changes"**

### Bước 3: Tải file .exe (5 phút chờ build)
1. Vào tab **"Actions"** → Đợi build xong (dấu ✓ xanh)
2. Click vào build job → Kéo xuống **"Artifacts"**
3. Click **"ssh-log-collector-windows"** → Tải file .zip

### Bước 4: Sử dụng
1. Giải nén file .zip
2. Sửa `config.yaml` với thông tin server của bạn:
```yaml
servers:
  - name: "My Server"
    host: "192.168.1.100"    # IP server của bạn
    username: "admin"        # Username SSH
    password: "your_pass"    # Password SSH
```
3. Chạy `ssh-log-collector.exe`

## 📋 Checklist
- [ ] Tạo GitHub repository
- [ ] Upload đầy đủ file (nhất là thư mục `.github`)
- [ ] Đợi Actions build xong
- [ ] Tải và giải nén
- [ ] Sửa config.yaml
- [ ] Chạy .exe

## ⚠️ Lưu ý
- Repository phải **Public** để dùng GitHub Actions miễn phí
- File `.github/workflows/build-exe.yml` quan trọng - đây là script build
- Mỗi lần thay đổi code, GitHub sẽ tự build .exe mới

## 🔧 Alternative: Chạy trực tiếp trên macOS
```bash
pip3 install paramiko rich click pyyaml keyboard
python3 main.py
```

Phần mềm hoạt động giống hệt nhau trên cả macOS và Windows.