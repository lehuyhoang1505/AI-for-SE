# TimeWeave - Meeting Scheduler

Ứng dụng giúp Leader tạo yêu cầu tìm thời điểm rảnh cho cuộc họp. Thành viên nhận link, nhập khoảng bận của mình. Hệ thống hợp nhất các khoảng bận, tính ra các khung rảnh phù hợp và hiển thị lịch heatmap.

## Tính năng chính

- ✅ **Nhanh chóng**: Tạo cuộc hẹn cho nhóm 5-50 người trong < 3 phút
- ✅ **Không cần đăng nhập**: Chỉ cần chia sẻ link với mã token
- ✅ **Hỗ trợ múi giờ**: Xử lý chênh lệch múi giờ tự động (UTC, Asia/Ho_Chi_Minh, v.v.)
- ✅ **Tính toán nhanh**: Gợi ý khung giờ tối ưu < 500ms
- ✅ **Heatmap trực quan**: Ô càng xanh đậm = càng nhiều người rảnh
- ✅ **Wizard 3 bước**: Dễ dàng tạo yêu cầu
- ✅ **Email Verification**: Xác thực email người dùng trước khi đăng nhập
- ✅ **Email Invitations**: Gửi email mời cuộc họp đến người tham gia
- ✅ **Auto Notifications**: Thông báo tự động khi chốt giờ họp

## Tech Stack

- **Backend**: Django 5.2.7
- **Database**: MySQL (with PyMySQL)
- **Frontend**: Bootstrap 5, jQuery
- **Timezone**: pytz
- **Email**: Resend API
- **Testing**: pytest, pytest-django, freezegun

## Quick Start (TL;DR)

```bash
# 1. Clone và setup
git clone https://github.com/lehuymanhtan/AI-for-SE
cd AI-for-SE
python -m venv .venv
source .venv/bin/activate  # hoặc .venv\Scripts\activate trên Windows

# 2. Cài đặt dependencies
pip install -r src/requirements.txt

# 3. Tạo database MySQL
mysql -u root -p -e "CREATE DATABASE sql_time_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. Cấu hình .env
cd src
cp .env.example .env
# Chỉnh sửa .env với thông tin database và secret key

# 5. Chạy migrations
python manage.py migrate

# 6. Khởi động server
python manage.py runserver
```

Truy cập: http://localhost:8000

## Cài đặt

### 1. Yêu cầu hệ thống

- Python 3.10+
- MySQL 5.7+ hoặc MySQL 8.0+
- pip

### 2. Clone repository

```bash
git clone https://github.com/lehuymanhtan/AI-for-SE
cd AI-for-SE
```

### 3. Tạo virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc
.venv\Scripts\activate  # Windows
```

### 4. Cài đặt dependencies

```bash
# Cài đặt dependencies cho ứng dụng
pip install -r src/requirements.txt

# Cài đặt dependencies cho test (tùy chọn, để chạy tests)
pip install -r tests/requirements-test.txt
```

### 5. Cấu hình Environment Variables

Sao chép file `.env.example` và điều chỉnh:

```bash
cd src
cp .env.example .env
```

Chỉnh sửa file `.env` với thông tin của bạn:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here  # Tạo mới bằng: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
DEBUG=True  # Đặt False trong production

# Database Settings
DB_NAME=sql_time_manager
DB_USER=your-mysql-username
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306

# Email Settings (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxxx  # Lấy từ https://resend.com/
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Site URL
SITE_URL=http://localhost:8000  # Thay bằng domain thực tế khi deploy

# Email Verification
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS=24
```

### 6. Cấu hình MySQL

Tạo database MySQL:

```sql
CREATE DATABASE sql_time_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'your-mysql-username'@'localhost' IDENTIFIED BY 'your-mysql-password';
GRANT ALL PRIVILEGES ON sql_time_manager.* TO 'your-mysql-username'@'localhost';
FLUSH PRIVILEGES;
```

### 7. Chạy migrations

```bash
cd src
python manage.py makemigrations
python manage.py migrate
```

### 8. Tạo superuser (tùy chọn)

```bash
python manage.py createsuperuser
```

### 9. Chạy development server

```bash
# Đảm bảo bạn đang ở trong thư mục src/
python manage.py runserver
```

Truy cập: http://localhost:8000

**Chạy trên port khác:**
```bash
python manage.py runserver 8080
```

**Cho phép truy cập từ mạng ngoài:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Lưu ý về Email:** 
- Trong development mode, email sẽ được in ra console terminal
- Để gửi email thật, cấu hình `RESEND_API_KEY` trong file `.env`


## Deployment (Production)

### Chuẩn bị cho Production

#### 1. Cấu hình Environment Variables

Cập nhật file `.env` với các giá trị production:

```bash
# Django Settings
SECRET_KEY=<your-strong-secret-key>  # Phải là key mạnh và bí mật
DEBUG=False  # QUAN TRỌNG: Tắt DEBUG mode

# Database Settings
DB_NAME=sql_time_manager
DB_USER=<production-db-user>
DB_PASSWORD=<strong-db-password>
DB_HOST=<db-host>  # Có thể là localhost hoặc remote DB
DB_PORT=3306

# Email Settings (Resend)
RESEND_API_KEY=<production-resend-api-key>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Site URL
SITE_URL=https://yourdomain.com  # URL production

# Email Verification
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS=24
```

#### 2. Cập nhật ALLOWED_HOSTS

Chỉnh sửa `src/time_mamager/settings.py`:

```python
ALLOWED_HOSTS = [
    'yourdomain.com',
    'www.yourdomain.com',
    '<server-ip>',
]

CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]
```

#### 3. Thu thập Static Files

```bash
cd src
python manage.py collectstatic --noinput
```

#### 4. Chạy Migrations

```bash
python manage.py migrate --noinput
```

### Deployment Options

#### Option 1: Deployment với Gunicorn + Nginx (Recommended)

**Bước 1: Cài đặt Gunicorn**

```bash
pip install gunicorn
```

**Bước 2: Tạo Gunicorn service file**

Tạo file `/etc/systemd/system/timeweave.service`:

```ini
[Unit]
Description=TimeWeave Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/AI-for-SE/src
Environment="PATH=/path/to/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=time_mamager.settings"
ExecStart=/path/to/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/path/to/AI-for-SE/timeweave.sock \
    time_mamager.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Bước 3: Start và enable service**

```bash
sudo systemctl start timeweave
sudo systemctl enable timeweave
sudo systemctl status timeweave
```

**Bước 4: Cấu hình Nginx**

Tạo file `/etc/nginx/sites-available/timeweave`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /path/to/AI-for-SE/src/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/AI-for-SE/timeweave.sock;
    }
}
```

**Bước 5: Enable site và restart Nginx**

```bash
sudo ln -s /etc/nginx/sites-available/timeweave /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Bước 6: Cài đặt SSL với Let's Encrypt (Tùy chọn nhưng khuyến nghị)**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### Option 2: Deployment với Docker

**Bước 1: Tạo Dockerfile**

Tạo file `Dockerfile` trong thư mục root:

```dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy project files
COPY src/ .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "time_mamager.wsgi:application"]
```

**Bước 2: Tạo docker-compose.yml**

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: sql_time_manager
      MYSQL_USER: timeweave_user
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 --workers 3 time_mamager.wsgi:application
    volumes:
      - ./src:/app
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - ./src/.env
    depends_on:
      - db

  nginx:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/static
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  mysql_data:
  static_volume:
```

**Bước 3: Build và chạy containers**

```bash
docker-compose up -d --build
```

**Bước 4: Run migrations trong container**

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

#### Option 3: Deployment trên Platform as a Service (PaaS)

**Railway.app / Render.com / Heroku:**

1. Thêm `Procfile` vào root directory:
```
web: cd src && gunicorn time_mamager.wsgi:application --log-file -
```

2. Thêm `runtime.txt`:
```
python-3.10.12
```

3. Cấu hình environment variables trên platform dashboard
4. Deploy từ GitHub repository

### Post-Deployment Checklist

- [ ] Kiểm tra `DEBUG=False` trong production
- [ ] Cấu hình ALLOWED_HOSTS và CSRF_TRUSTED_ORIGINS đúng
- [ ] Database backups được thiết lập
- [ ] SSL certificate đã được cài đặt
- [ ] Static files được serve đúng cách
- [ ] Email service (Resend) hoạt động
- [ ] Logs được cấu hình và monitor
- [ ] Firewall rules được thiết lập đúng
- [ ] Database credentials mạnh và bảo mật
- [ ] SECRET_KEY là unique và bí mật

### Monitoring và Maintenance

**Xem logs:**
```bash
# Gunicorn service logs
sudo journalctl -u timeweave -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f web
```

**Database backup:**
```bash
# Backup
mysqldump -u <user> -p sql_time_manager > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
mysql -u <user> -p sql_time_manager < backup_20231031_120000.sql
```

**Restart service:**
```bash
# Gunicorn
sudo systemctl restart timeweave

# Nginx
sudo systemctl restart nginx

# Docker
docker-compose restart web
```

## Chạy Tests

Project này có bộ test suite hoàn chỉnh nằm trong thư mục `tests/`.

### Phương pháp 1: Sử dụng wrapper script (Khuyến nghị)

Script `run_tests.sh` tự động cấu hình môi trường test:

```bash
# Làm cho script có thể thực thi (chỉ cần làm một lần)
chmod +x run_tests.sh

# Chạy tất cả tests
./run_tests.sh

# Chạy với chế độ quiet (im lặng)
./run_tests.sh -q

# Chạy một file test cụ thể
./run_tests.sh tests/test_generate_time_slots.py

# Chạy một test function cụ thể
./run_tests.sh tests/test_generate_time_slots.py::test_basic_slot_generation
```

### Phương pháp 2: Chạy pytest trực tiếp

```bash
# Thiết lập biến môi trường và chạy pytest
PYTHONPATH=$(pwd)/src \
DJANGO_SETTINGS_MODULE=time_mamager.test_settings \
python -m pytest tests -v

# Chạy với báo cáo coverage
PYTHONPATH=$(pwd)/src \
DJANGO_SETTINGS_MODULE=time_mamager.test_settings \
python -m pytest tests --cov=meetings.utils --cov-report=term-missing --cov-report=html

# Chạy một file test cụ thể
PYTHONPATH=$(pwd)/src \
DJANGO_SETTINGS_MODULE=time_mamager.test_settings \
python -m pytest tests/test_is_participant_available.py -v
```

### Cấu hình Test

- **Test settings**: `src/time_mamager/test_settings.py`
- **Pytest config**: `src/pytest.ini`
- **Test dependencies**: `tests/requirements-test.txt`


### Xử lý lỗi khi chạy Tests

**Lỗi: ModuleNotFoundError: No module named 'meetings'**
```bash
# Đảm bảo PYTHONPATH chứa src/
export PYTHONPATH=$(pwd)/src
```

**Lỗi: django.core.exceptions.ImproperlyConfigured**
```bash
# Đảm bảo set Django test settings
export DJANGO_SETTINGS_MODULE=time_mamager.test_settings
```

**Lỗi: ImportError: No module named 'pymysql'**
```bash
# Cài đặt dependencies
pip install -r src/requirements.txt
```

## Cấu trúc project

```
AI-for-SE/
├── README.md                  # Main README (test-focused)
├── README copy.md             # This file
├── run_tests.sh              # Test runner wrapper script
├── prompts/                  # AI prompts and logs
│   ├── log.md
│   ├── optimize_log.md
│   ├── optimize.md
│   ├── test_analysis.md
│   └── test_design.md
├── src/                      # Django application source
│   ├── manage.py
│   ├── requirements.txt      # Application dependencies
│   ├── pytest.ini           # Pytest configuration
│   ├── PROJECT_SUMMARY.md
│   ├── QUICKSTART.md
│   ├── README.md            # Application README
│   ├── time_mamager/        # Django project settings
│   │   ├── __init__.py
│   │   ├── settings.py      # Production settings
│   │   ├── test_settings.py # Test settings
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── meetings/            # Main Django app
│   │   ├── models.py       # MeetingRequest, Participant, BusySlot, SuggestedSlot
│   │   ├── views.py        # Leader & Member workflows
│   │   ├── forms.py        # Form definitions
│   │   ├── urls.py         # URL routing
│   │   ├── utils.py        # Core algorithms (slot finding, availability)
│   │   ├── admin.py        # Django admin
│   │   ├── migrations/     # Database migrations
│   │   ├── templates/      # HTML templates
│   │   │   └── meetings/
│   │   │       ├── base.html
│   │   │       ├── home.html
│   │   │       ├── create_step1.html
│   │   │       ├── create_step2.html
│   │   │       ├── create_step3.html
│   │   │       ├── respond_step1.html
│   │   │       ├── select_busy_times.html
│   │   │       └── ...
│   │   └── templatetags/   # Custom template filters
│   └── static/             # CSS, JS, images
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
└── tests/                   # Test suite
    ├── __init__.py
    ├── conftest.py         # Pytest fixtures
    ├── requirements-test.txt # Test dependencies
    ├── run_tests.sh        # Alternative test runner
    ├── test_calculate_slot_availability.py
    ├── test_generate_suggested_slots.py
    ├── test_generate_time_slots.py
    ├── test_get_top_suggestions.py
    └── test_is_participant_available.py
```

## Luồng sử dụng

### Leader tạo yêu cầu (3 bước)

1. **Bước 1 - Cấu hình**: 
   - Tiêu đề, mô tả cuộc họp
   - Thời lượng (15-480 phút)
   - Phạm vi ngày tìm kiếm
   - Khung giờ làm việc
   - Bước quét (15/30/60 phút)
   - Múi giờ mặc định

2. **Bước 2 - Thêm người tham gia** (tùy chọn):
   - Thêm từng người hoặc import hàng loạt
   - Có thể bỏ qua và gửi link công khai

3. **Bước 3 - Xác nhận**:
   - Xem preview heatmap rỗng
   - Nhận link chia sẻ
   - Gửi cho thành viên

### Member điền lịch bận

1. Mở link được chia sẻ
2. Nhập tên, email (tùy chọn), chọn múi giờ
3. Kéo chuột trên calendar để chọn các khoảng bận
4. Lưu và xem heatmap hiện tại

### Leader xem kết quả & chốt lịch

1. Theo dõi tiến độ phản hồi (% đã trả lời)
2. Xem heatmap với các mức độ màu xanh
3. Xem top gợi ý (sắp xếp theo số người rảnh)
4. Chọn và chốt khung giờ phù hợp
5. Xuất .ics hoặc tạo event (tính năng tương lai)

## Models chính

### MeetingRequest
- Thông tin yêu cầu họp
- Cấu hình (thời lượng, phạm vi ngày, múi giờ)
- Token để chia sẻ

### Participant
- Người tham gia
- Tên, email, múi giờ
- Trạng thái phản hồi

### BusySlot
- Khoảng thời gian bận của một participant
- Lưu dưới dạng UTC

### SuggestedSlot
- Khung giờ được gợi ý
- Số người rảnh / tổng số người
- Heatmap level (0-5)

## API Endpoints

- `GET /api/request/<id>/heatmap/` - Lấy dữ liệu heatmap
- `GET /api/request/<id>/suggestions/` - Lấy danh sách gợi ý
- `POST /r/<id>/save/` - Lưu busy slots của participant

## Admin Interface

Truy cập: http://localhost:8000/admin

Quản lý:
- Meeting Requests
- Participants
- Busy Slots
- Suggested Slots

## Xử lý sự cố

### Lỗi kết nối MySQL

```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server...")
```

**Giải pháp**: Kiểm tra MySQL service đang chạy và thông tin kết nối trong `src/time_mamager/settings.py`

### Lỗi import pytz

```
ModuleNotFoundError: No module named 'pytz'
```

**Giải pháp**: 
```bash
pip install pytz
```

### Lỗi import pymysql

```
ModuleNotFoundError: No module named 'pymysql'
```

**Giải pháp**:
```bash
pip install pymysql
```

### Static files không load

**Giải pháp**:
```bash
cd src
python manage.py collectstatic
```

### Tests không chạy được

**Giải pháp**: Đảm bảo đã set đúng PYTHONPATH và DJANGO_SETTINGS_MODULE:
```bash
export PYTHONPATH=$(pwd)/src
export DJANGO_SETTINGS_MODULE=time_mamager.test_settings
```

Hoặc sử dụng wrapper script:
```bash
./run_tests.sh
```

## Quy trình phát triển

### Chạy ứng dụng

```bash
cd src
python manage.py runserver
```

### Chạy tests trong quá trình phát triển

```bash
# Chạy tất cả tests
./run_tests.sh -v

# Chạy một module test cụ thể
./run_tests.sh tests/test_generate_time_slots.py -v

# Chạy với coverage
PYTHONPATH=$(pwd)/src DJANGO_SETTINGS_MODULE=time_mamager.test_settings \
python -m pytest tests --cov=meetings.utils --cov-report=html
```

### Database migrations

```bash
cd src
python manage.py makemigrations
python manage.py migrate
```

## Contributing

1. Fork project
2. Tạo feature branch (`git checkout -b feature/TinhNangMoi`)
3. Viết tests cho những thay đổi của bạn
4. Chạy test suite để đảm bảo tất cả đều pass (`./run_tests.sh`)
5. Commit các thay đổi (`git commit -m 'Thêm tính năng mới'`)
6. Push lên branch (`git push origin feature/TinhNangMoi`)
7. Tạo Pull Request

## Tài nguyên liên quan

- **Project Slide**: [Canva Presentation](https://www.canva.com/design/DAG2nlsFR1k/soonJh0gIRisxeUub7zJuw/edit)
- **Test-focused README**: [README.md](README.md)
- **Application README**: [src/README.md](src/README.md)
- **Project Summary**: [src/PROJECT_SUMMARY.md](src/PROJECT_SUMMARY.md)
- **Quick Start Guide**: [src/QUICKSTART.md](src/QUICKSTART.md)

## License

MIT License

## Author

TimeWeave Team
