# Hướng dẫn build file .exe cho SSH Log Collector

## Cách 1: Sử dụng GitHub Actions (Tự động build .exe online)

### Bước 1: Tạo repository trên GitHub
1. Tạo repository mới trên GitHub
2. Upload toàn bộ source code lên

### Bước 2: Tạo GitHub Actions workflow
Tạo file `.github/workflows/build-exe.yml`:

```yaml
name: Build Windows EXE

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install paramiko rich click pyyaml keyboard pyinstaller
    
    - name: Build executable
      run: |
        pyinstaller --onefile --console --name "ssh-log-collector" main.py
    
    - name: Copy config file
      run: |
        copy config.yaml dist\config.yaml
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: ssh-log-collector-exe
        path: |
          dist/ssh-log-collector.exe
          dist/config.yaml
```

### Bước 3: Tải file .exe
1. Vào tab "Actions" trong GitHub repository
2. Chọn workflow build mới nhất
3. Tải file .exe từ "Artifacts"

## Cách 2: Sử dụng Windows máy ảo

### Trên macOS với VMware/Parallels/VirtualBox:
1. Cài Windows 10/11 trên máy ảo
2. Cài Python 3.11+
3. Copy source code vào Windows VM
4. Chạy build.bat

## Cách 3: Sử dụng Wine (không khuyến khích)
```bash
# Cài Wine trên macOS
brew install --cask wine-stable

# Cài Python for Windows qua Wine
# Rất phức tạp và hay gặp lỗi
```

## Cách 4: Sử dụng Docker với Windows container
Yêu cầu Docker Desktop với Windows containers enabled.

## Khuyến nghị:
- **Dễ nhất**: Sử dụng GitHub Actions (Cách 1)
- **Nhanh nhất**: Tìm máy Windows để build
- **Thực tế nhất**: Chạy Python trực tiếp trên macOS