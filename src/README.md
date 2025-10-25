# TimeWeave - Meeting Scheduler

Ứng dụng giúp Leader tạo yêu cầu tìm thời điểm rảnh cho cuộc họp. Thành viên nhận link, nhập khoảng bận của mình. Hệ thống hợp nhất các khoảng bận, tính ra các khung rảnh phù hợp và hiển thị lịch heatmap.

## Tính năng chính

- ✅ **Nhanh chóng**: Tạo cuộc hẹn cho nhóm 5-50 người trong < 3 phút
- ✅ **Không cần đăng nhập**: Chỉ cần chia sẻ link với mã token
- ✅ **Hỗ trợ múi giờ**: Xử lý chênh lệch múi giờ tự động (UTC, Asia/Ho_Chi_Minh, v.v.)
- ✅ **Tính toán nhanh**: Gợi ý khung giờ tối ưu < 500ms
- ✅ **Heatmap trực quan**: Ô càng xanh đậm = càng nhiều người rảnh
- ✅ **Wizard 3 bước**: Dễ dàng tạo yêu cầu

## Tech Stack

- **Backend**: Django 5.2.7
- **Database**: MySQL
- **Frontend**: Bootstrap 5, jQuery
- **Timezone**: pytz

## Cài đặt

### 1. Yêu cầu hệ thống

- Python 3.10+
- MySQL 5.7+ hoặc MySQL 8.0+
- pip

### 2. Clone repository

```bash
git clone <repository-url>
cd time-manager
```

### 3. Tạo virtual environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# hoặc
source venv/bin/activate  # Linux/Mac
```

### 4. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 5. Cấu hình MySQL

Tạo database MySQL:

```sql
CREATE DATABASE time_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Cập nhật thông tin kết nối trong `time_mamager/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'time_manager_db',
        'USER': 'root',  # Thay đổi theo user MySQL của bạn
        'PASSWORD': 'root',  # Thay đổi theo password MySQL của bạn
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 6. Chạy migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Tạo superuser (tùy chọn)

```bash
python manage.py createsuperuser
```

### 8. Chạy development server

```bash
python manage.py runserver
```

Truy cập: http://localhost:8000

## Cấu trúc project

```
time-manager/
├── manage.py
├── requirements.txt
├── time_mamager/          # Project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── meetings/              # Main app
│   ├── models.py         # MeetingRequest, Participant, BusySlot, SuggestedSlot
│   ├── views.py          # Leader & Member workflows
│   ├── forms.py          # Form definitions
│   ├── urls.py           # URL routing
│   ├── utils.py          # Algorithm for finding available slots
│   ├── admin.py          # Django admin
│   └── templates/        # HTML templates
│       └── meetings/
│           ├── base.html
│           ├── home.html
│           ├── create_step1.html
│           ├── create_step2.html
│           ├── create_step3.html
│           ├── respond_step1.html
│           ├── select_busy_times.html
│           └── ...
└── static/               # CSS, JS, images
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
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

## Tính năng nâng cao (TODO)

- [ ] Export to ICS file
- [ ] Google Calendar integration (OAuth)
- [ ] Outlook Calendar integration
- [ ] Email notifications
- [ ] Real-time updates với WebSocket
- [ ] Multi-language support
- [ ] Mobile app

## Troubleshooting

### Lỗi kết nối MySQL

```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server...")
```

**Giải pháp**: Kiểm tra MySQL service đang chạy và thông tin kết nối trong settings.py

### Lỗi import pytz

```
ModuleNotFoundError: No module named 'pytz'
```

**Giải pháp**: 
```bash
pip install pytz
```

### Static files không load

**Giải pháp**:
```bash
python manage.py collectstatic
```

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License

## Author

TimeWeave Team
