# Quick Start Guide - TIMEWEAVE

## Cài đặt nhanh (Windows)

### 1. Chuẩn bị

Đảm bảo đã cài đặt:
- Python 3.10+ ([Download](https://www.python.org/downloads/))
- MySQL 8.0+ ([Download](https://dev.mysql.com/downloads/installer/))

### 2. Setup Database

Mở MySQL Command Line hoặc MySQL Workbench, chạy:

```sql
CREATE DATABASE time_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Cài đặt ứng dụng

```bash
# Tạo virtual environment
python -m venv venv
venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình database
# Mở file time_mamager\settings.py
# Thay đổi USER và PASSWORD trong DATABASES theo MySQL của bạn

# Tạo tables
python manage.py makemigrations
python manage.py migrate

# (Tùy chọn) Tạo admin user
python manage.py createsuperuser

# Chạy server
python manage.py runserver
```

### 4. Truy cập

- **Website**: http://127.0.0.1:8000
- **Admin**: http://127.0.0.1:8000/admin

## Sử dụng nhanh

### Tạo yêu cầu họp (Leader)

1. Vào trang chủ → Click "Tạo yêu cầu mới"
2. Điền thông tin:
   - Tiêu đề: "Họp Sprint Planning"
   - Thời lượng: 60 phút
   - Ngày: 7 ngày tiếp theo
   - Giờ làm việc: 9:00 - 18:00
3. Thêm người tham gia hoặc bỏ qua
4. Nhận link chia sẻ
5. Gửi link cho thành viên

### Điền lịch bận (Member)

1. Mở link nhận được
2. Nhập tên, email (tùy chọn)
3. Chọn múi giờ của bạn
4. Kéo chuột để chọn các khoảng BẬN
5. Click "Lưu"

### Xem kết quả & chốt lịch (Leader)

1. Vào "Dashboard" → Click vào yêu cầu
2. Xem tiến độ phản hồi
3. Xem heatmap (ô xanh đậm = nhiều người rảnh)
4. Xem top 10 khung giờ được gợi ý
5. Click "Chốt" khung giờ phù hợp

## Lỗi thường gặp

### Không kết nối được MySQL

```
Error: (2003, "Can't connect to MySQL server")
```

**Giải pháp**:
1. Kiểm tra MySQL service đang chạy
2. Kiểm tra USER, PASSWORD trong settings.py
3. Kiểm tra database đã tạo chưa

### Import Error: No module named 'mysqlclient'

```bash
# Windows: Tải wheel file
pip install mysqlclient-1.4.6-cp310-cp310-win_amd64.whl

# hoặc
pip install pymysql
```

Thêm vào `time_mamager/__init__.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### Static files không hiển thị

```bash
python manage.py collectstatic
```

Trong settings.py:
```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

## Kiểm tra cài đặt

```bash
# Kiểm tra Python
python --version  # Phải >= 3.10

# Kiểm tra pip packages
pip list

# Kiểm tra database connection
python manage.py dbshell
```

## Demo Data (Optional)

Để tạo dữ liệu mẫu:

```bash
python manage.py shell
```

```python
from meetings.models import MeetingRequest
from datetime import datetime, timedelta

# Tạo meeting request mẫu
mr = MeetingRequest.objects.create(
    title="Họp Sprint Planning",
    description="Lên kế hoạch sprint tháng 11",
    duration_minutes=60,
    timezone="Asia/Ho_Chi_Minh",
    date_range_start=datetime.now().date(),
    date_range_end=datetime.now().date() + timedelta(days=7),
)

print(f"Created: {mr.get_share_url()}")
```

## Tài liệu chi tiết

Xem file README.md để biết thêm thông tin chi tiết về:
- Cấu trúc project
- Models và database schema
- API endpoints
- Tính năng nâng cao

## Support

Nếu gặp vấn đề, tạo issue trên GitHub hoặc liên hệ team.
