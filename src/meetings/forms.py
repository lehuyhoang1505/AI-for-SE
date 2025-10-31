"""
Forms for Meeting Time Scheduler
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MeetingRequest, Participant, BusySlot
from datetime import datetime, timedelta, date
import pytz


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email này đã được đăng ký')
        return email


class MeetingRequestForm(forms.ModelForm):
    """Form for creating a new meeting request (Step 1 of wizard)"""
    
    class Meta:
        model = MeetingRequest
        fields = [
            'title', 'description', 'duration_minutes', 'timezone',
            'date_range_start', 'date_range_end',
            'work_hours_start', 'work_hours_end',
            'step_size_minutes', 'work_days_only',
            'response_deadline',
            'created_by_email'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: Họp sprint planning tháng 11'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả chi tiết về cuộc họp (tùy chọn)'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'max': 480,
                'step': 15
            }),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'date_range_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_range_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'work_hours_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'work_hours_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'step_size_minutes': forms.Select(attrs={'class': 'form-select'}),
            'work_days_only': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'response_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'created_by_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate timezone choices
        common_timezones = [
            'UTC',
            'Asia/Ho_Chi_Minh',
            'Asia/Singapore',
            'Asia/Bangkok',
            'Asia/Tokyo',
            'Asia/Seoul',
            'Europe/London',
            'Europe/Paris',
            'America/New_York',
            'America/Los_Angeles',
        ]
        self.fields['timezone'].widget = forms.Select(
            choices=[(tz, tz) for tz in common_timezones],
            attrs={'class': 'form-select'}
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('date_range_start')
        end_date = cleaned_data.get('date_range_end')
        work_start = cleaned_data.get('work_hours_start')
        work_end = cleaned_data.get('work_hours_end')
        response_deadline = cleaned_data.get('response_deadline')
        
        # Get today's date for comparison
        today = timezone.now().date()
        
        # Check if start date is in the past
        if start_date and start_date < today:
            raise ValidationError('Ngày bắt đầu không được ở quá khứ')
        
        # Check if end date is in the past
        if end_date and end_date < today:
            raise ValidationError('Ngày kết thúc không được ở quá khứ')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu')
            
            # Limit to reasonable range
            if (end_date - start_date).days > 90:
                raise ValidationError('Phạm vi ngày không được vượt quá 90 ngày')
        
        # Check if response deadline is in the past
        if response_deadline:
            if response_deadline < timezone.now():
                raise ValidationError('Hạn chót trả lời không được ở quá khứ')
        
        if work_start and work_end:
            if work_end <= work_start:
                raise ValidationError('Giờ kết thúc phải sau giờ bắt đầu')
        
        return cleaned_data


class ParticipantForm(forms.ModelForm):
    """Form for adding participants (Step 2 of wizard)"""
    
    class Meta:
        model = Participant
        fields = ['name', 'email', 'timezone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên người tham gia'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate timezone choices
        common_timezones = [
            'Asia/Ho_Chi_Minh',
            'UTC',
            'Asia/Singapore',
            'Asia/Bangkok',
            'Asia/Tokyo',
            'Asia/Seoul',
            'Europe/London',
            'Europe/Paris',
            'America/New_York',
            'America/Los_Angeles',
        ]
        self.fields['timezone'].widget = forms.Select(
            choices=[(tz, tz) for tz in common_timezones],
            attrs={'class': 'form-select'}
        )


class BulkParticipantForm(forms.Form):
    """Form for adding multiple participants at once"""
    participants_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Nhập danh sách người tham gia, mỗi dòng một người:\nNguyễn Văn A, a@example.com\nTrần Thị B, b@example.com'
        }),
        required=False,
        help_text='Mỗi dòng: Tên, Email (hoặc chỉ Email)'
    )


class BusySlotForm(forms.ModelForm):
    """Form for participants to input their busy times"""
    
    class Meta:
        model = BusySlot
        fields = ['start_time', 'end_time', 'description']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ghi chú (tùy chọn)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        
        if start and end:
            if end <= start:
                raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu')
        
        return cleaned_data


class ParticipantResponseForm(forms.Form):
    """Form for participant to provide their information and timezone"""
    name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên của bạn (tùy chọn)'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email của bạn (tùy chọn)'
        })
    )
    timezone = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_timezones = [
            'Asia/Ho_Chi_Minh',
            'UTC',
            'Asia/Singapore',
            'Asia/Bangkok',
            'Asia/Tokyo',
            'Asia/Seoul',
            'Europe/London',
            'Europe/Paris',
            'America/New_York',
            'America/Los_Angeles',
        ]
        self.fields['timezone'].choices = [(tz, tz) for tz in common_timezones]
