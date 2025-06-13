# Hướng dẫn chi tiết build file .exe bằng GitHub Actions

## Bước 1: Tạo tài khoản GitHub (nếu chưa có)
1. Truy cập https://github.com
2. Đăng ký tài khoản miễn phí
3. Xác thực email

## Bước 2: Tạo repository mới
1. Đăng nhập GitHub
2. Click nút **"New"** (màu xanh) hoặc **"+"** góc phải → **"New repository"**
3. Đặt tên repository: `ssh-log-collector`
4. Chọn **"Public"** (để sử dụng GitHub Actions miễn phí)
5. Tick **"Add a README file"**
6. Click **"Create repository"**

## Bước 3: Upload source code lên GitHub

### Cách 3a: Sử dụng GitHub Web Interface (Dễ nhất)
1. Trong repository vừa tạo, click **"uploading an existing file"**
2. Kéo thả hoặc chọn tất cả file source code:
   - `main.py`
   - `config.py` 
   - `ui.py`
   - `ssh_manager.py`
   - `file_transfer.py`
   - `utils.py`
   - `config.yaml`
   - `build.bat`
   - `README.md`
   - Thư mục `.github` (quan trọng!)

3. Viết commit message: "Initial upload"
4. Click **"Commit changes"**

### Cách 3b: Sử dụng Git command line
```bash
# Clone repository về máy
git clone https://github.com/your-username/ssh-log-collector.git
cd ssh-log-collector

# Copy tất cả source code vào thư mục này
# Bao gồm thư mục .github với file workflow

# Add và commit
git add .
git commit -m "Initial upload with build workflow"
git push origin main
```

## Bước 4: Kiểm tra GitHub Actions đã chạy
1. Vào repository trên GitHub
2. Click tab **"Actions"** (cạnh Code, Issues, Pull requests)
3. Bạn sẽ thấy workflow **"Build Windows EXE"** đang chạy
4. Click vào workflow để xem tiến trình

## Bước 5: Tải file .exe khi build xong
1. Đợi workflow hoàn thành (màu xanh ✓)
2. Trong trang workflow, kéo xuống phần **"Artifacts"**
3. Click **"ssh-log-collector-windows"** để tải về
4. File tải về sẽ là file .zip chứa:
   - `ssh-log-collector.exe`
   - `config.yaml`
   - `README.txt`

## Bước 6: Sử dụng file .exe
1. Giải nén file .zip vừa tải
2. Chỉnh sửa `config.yaml` với thông tin server thực của bạn
3. Double-click `ssh-log-collector.exe` để chạy

## Troubleshooting

### Nếu workflow không chạy:
- Đảm bảo file `.github/workflows/build-exe.yml` đã được upload
- Repository phải là Public để dùng GitHub Actions miễn phí
- Kiểm tra tab Actions có bị disable không

### Nếu build bị lỗi:
- Click vào workflow failed để xem log lỗi
- Thường là lỗi dependency hoặc syntax Python
- Sửa lỗi và push code mới, workflow sẽ tự chạy lại

### Nếu không có Artifacts:
- Workflow phải hoàn thành thành công (màu xanh)
- Artifacts chỉ tồn tại 90 ngày
- Cần đăng nhập GitHub để tải

## Lưu ý quan trọng:
- GitHub Actions miễn phí cho public repository
- Private repository có giới hạn thời gian build
- File .exe chỉ chạy được trên Windows
- Mỗi lần push code mới, sẽ tự động build lại

## Các bước tự động hóa:
- Mỗi khi bạn thay đổi code và push lên GitHub
- Workflow sẽ tự động build file .exe mới
- Luôn có phiên bản .exe mới nhất