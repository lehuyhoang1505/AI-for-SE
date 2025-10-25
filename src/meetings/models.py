"""
Models for Meeting Time Scheduler
Handles meeting requests, participants, busy slots, and suggested time slots
"""
import secrets
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import pytz


class MeetingRequest(models.Model):
    """
    Main model representing a meeting scheduling request created by a Leader
    """
    STEP_SIZE_CHOICES = [
        (15, '15 phút'),
        (30, '30 phút'),
        (60, '60 phút'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('active', 'Đang hoạt động'),
        ('locked', 'Đã khóa'),
        ('cancelled', 'Đã hủy'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, editable=False)
    
    # Basic Information
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Meeting Configuration
    duration_minutes = models.IntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(480)],
        verbose_name='Thời lượng (phút)',
        help_text='Thời lượng cuộc họp từ 15 phút đến 8 giờ'
    )
    timezone = models.CharField(
        max_length=50, 
        default='Asia/Ho_Chi_Minh',
        verbose_name='Múi giờ mặc định'
    )
    
    # Date Range
    date_range_start = models.DateField(verbose_name='Ngày bắt đầu phạm vi')
    date_range_end = models.DateField(verbose_name='Ngày kết thúc phạm vi')
    
    # Working Hours (stored in 24-hour format)
    work_hours_start = models.TimeField(
        default='09:00:00',
        verbose_name='Giờ làm việc bắt đầu'
    )
    work_hours_end = models.TimeField(
        default='18:00:00',
        verbose_name='Giờ làm việc kết thúc'
    )
    
    # Configuration
    step_size_minutes = models.IntegerField(
        choices=STEP_SIZE_CHOICES,
        default=30,
        verbose_name='Bước quét'
    )
    work_days_only = models.BooleanField(
        default=True,
        verbose_name='Chỉ ngày làm việc',
        help_text='Chỉ tìm kiếm trong các ngày Thứ 2 - Thứ 6'
    )
    hide_participant_names = models.BooleanField(
        default=False,
        verbose_name='Ẩn tên người tham gia'
    )
    
    # Deadline
    response_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hạn chót trả lời'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_email = models.EmailField(blank=True, verbose_name='Email người tạo')
    creator_id = models.CharField(max_length=100, blank=True, verbose_name='ID người tạo', 
                                    help_text='Session/cookie-based identifier for the creator')
    
    class Meta:
        db_table = 'meeting_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} ({self.id})"
    
    @property
    def is_active(self):
        """Check if the request is still active"""
        if self.status != 'active':
            return False
        if self.response_deadline and timezone.now() > self.response_deadline:
            return False
        return True
    
    @property
    def response_rate(self):
        """Calculate percentage of participants who have responded"""
        total = self.participants.count()
        if total == 0:
            return 0
        responded = self.participants.filter(has_responded=True).count()
        return round((responded / total) * 100)
    
    def get_share_url(self):
        """Generate shareable URL for participants"""
        return f"/r/{self.id}?t={self.token}"


class Participant(models.Model):
    """
    Represents a participant invited to provide their availability
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting_request = models.ForeignKey(
        MeetingRequest,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    
    # Participant Info
    name = models.CharField(max_length=255, blank=True, verbose_name='Tên')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    timezone = models.CharField(
        max_length=50,
        default='Asia/Ho_Chi_Minh',
        verbose_name='Múi giờ'
    )
    
    # Response Status
    has_responded = models.BooleanField(default=False)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'participants'
        unique_together = [['meeting_request', 'email']]
        indexes = [
            models.Index(fields=['meeting_request', 'has_responded']),
        ]
    
    def __str__(self):
        display_name = self.name or self.email or f"Participant {self.id}"
        return f"{display_name} - {self.meeting_request.title}"


class BusySlot(models.Model):
    """
    Represents a time slot when a participant is busy/unavailable
    All times stored in UTC for consistency
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='busy_slots'
    )
    
    # Time range in UTC
    start_time = models.DateTimeField(verbose_name='Thời gian bắt đầu (UTC)')
    end_time = models.DateTimeField(verbose_name='Thời gian kết thúc (UTC)')
    
    # Optional description
    description = models.CharField(max_length=255, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'busy_slots'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['participant', 'start_time', 'end_time']),
        ]
    
    def __str__(self):
        return f"{self.participant.name or 'Unknown'}: {self.start_time} - {self.end_time}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_time >= self.end_time:
            raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu')


class SuggestedSlot(models.Model):
    """
    Represents a suggested time slot for the meeting
    Calculated based on participant availability
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting_request = models.ForeignKey(
        MeetingRequest,
        on_delete=models.CASCADE,
        related_name='suggested_slots'
    )
    
    # Time range in UTC
    start_time = models.DateTimeField(verbose_name='Thời gian bắt đầu (UTC)')
    end_time = models.DateTimeField(verbose_name='Thời gian kết thúc (UTC)')
    
    # Availability metrics
    available_count = models.IntegerField(
        default=0,
        verbose_name='Số người rảnh',
        help_text='Number of participants available during this slot'
    )
    total_participants = models.IntegerField(
        default=0,
        verbose_name='Tổng số người'
    )
    
    # Calculation metadata
    calculated_at = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(
        default=False,
        verbose_name='Đã chốt',
        help_text='Leader has selected this slot as final'
    )
    
    class Meta:
        db_table = 'suggested_slots'
        ordering = ['-available_count', 'start_time']
        indexes = [
            models.Index(fields=['meeting_request', '-available_count']),
            models.Index(fields=['meeting_request', 'is_locked']),
        ]
    
    @property
    def availability_percentage(self):
        """Calculate what percentage of participants are available"""
        if self.total_participants == 0:
            return 0
        return round((self.available_count / self.total_participants) * 100, 1)
    
    @property
    def heatmap_level(self):
        """
        Return heatmap intensity level (0-5) based on availability
        5 = 80%+, 4 = 60-79%, 3 = 40-59%, 2 = 20-39%, 1 = 1-19%, 0 = 0%
        """
        pct = self.availability_percentage
        if pct >= 80:
            return 5
        elif pct >= 60:
            return 4
        elif pct >= 40:
            return 3
        elif pct >= 20:
            return 2
        elif pct > 0:
            return 1
        return 0
    
    def __str__(self):
        return f"{self.meeting_request.title}: {self.start_time} ({self.available_count}/{self.total_participants})"
