"""
Models for Project Management System
Handles projects, tasks, team members, and progress tracking
"""
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Project(models.Model):
    """
    Main model representing a project with goals, deadlines, and team members
    """
    STATUS_CHOICES = [
        ('planning', 'Đang lên kế hoạch'),
        ('active', 'Đang thực hiện'),
        ('on_hold', 'Tạm dừng'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255, verbose_name='Tên dự án')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    goals = models.TextField(blank=True, verbose_name='Mục tiêu', help_text='Các mục tiêu của dự án')
    
    # Status & Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Timeline
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    deadline = models.DateField(verbose_name='Hạn chót')
    
    # Team
    leader = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='led_projects',
        verbose_name='Trưởng nhóm'
    )
    members = models.ManyToManyField(
        User, 
        through='ProjectMembership',
        related_name='projects',
        verbose_name='Thành viên'
    )
    
    # Progress tracking
    completion_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Phần trăm hoàn thành'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['leader', 'status']),
            models.Index(fields=['status', 'deadline']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_overdue(self):
        """Check if project is past its deadline"""
        if self.status in ['completed', 'cancelled']:
            return False
        return timezone.now().date() > self.deadline
    
    @property
    def days_remaining(self):
        """Calculate days remaining until deadline"""
        delta = self.deadline - timezone.now().date()
        return delta.days
    
    @property
    def total_tasks(self):
        """Total number of tasks in project"""
        return self.tasks.count()
    
    @property
    def completed_tasks(self):
        """Number of completed tasks"""
        return self.tasks.filter(status='completed').count()
    
    @property
    def overdue_tasks(self):
        """Number of overdue tasks"""
        return self.tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now().date()
        ).count()
    
    @property
    def soon_overdue_tasks(self):
        """Number of tasks that will be overdue in next 3 days"""
        three_days_from_now = timezone.now().date() + timedelta(days=3)
        return self.tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__gte=timezone.now().date(),
            due_date__lte=three_days_from_now
        ).count()
    
    def update_completion_percentage(self):
        """Recalculate and update completion percentage based on tasks"""
        total = self.total_tasks
        if total == 0:
            self.completion_percentage = 0
        else:
            completed = self.completed_tasks
            self.completion_percentage = int((completed / total) * 100)
        self.save(update_fields=['completion_percentage', 'updated_at'])


class ProjectMembership(models.Model):
    """
    Represents the relationship between a user and a project with their role
    """
    ROLE_CHOICES = [
        ('leader', 'Trưởng nhóm'),
        ('developer', 'Lập trình viên'),
        ('designer', 'Thiết kế'),
        ('tester', 'Kiểm thử'),
        ('analyst', 'Phân tích'),
        ('member', 'Thành viên'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_memberships'
        unique_together = [['project', 'user']]
        indexes = [
            models.Index(fields=['project', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.get_role_display()})"


class TodoTask(models.Model):
    """
    Represents a task/todo item within a project
    """
    STATUS_CHOICES = [
        ('todo', 'Cần làm'),
        ('in_progress', 'Đang làm'),
        ('review', 'Đang review'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Dự án'
    )
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    # Status & Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Assignment
    assignees = models.ManyToManyField(
        User,
        related_name='assigned_tasks',
        blank=True,
        verbose_name='Người thực hiện'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='Người tạo'
    )
    
    # Timeline
    due_date = models.DateField(verbose_name='Hạn chót')
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Ước tính giờ'
    )
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Giờ thực tế'
    )
    
    # Progress
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Phần trăm hoàn thành'
    )
    
    # Tags
    tags = models.ManyToManyField(
        'TaskTag',
        related_name='tasks',
        blank=True,
        verbose_name='Tags'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'todo_tasks'
        ordering = ['-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['priority', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.project.name})"
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.status in ['completed', 'cancelled']:
            return False
        return timezone.now().date() > self.due_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining until due date"""
        delta = self.due_date - timezone.now().date()
        return delta.days
    
    @property
    def is_soon_overdue(self):
        """Check if task will be overdue within 3 days"""
        if self.status in ['completed', 'cancelled']:
            return False
        days = self.days_remaining
        return 0 <= days <= 3
    
    def save(self, *args, **kwargs):
        # Auto-set completed_at when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            self.progress_percentage = 100
        
        # Create history entry for status changes
        # Use _state.adding instead of pk check for UUID primary keys
        is_new = self._state.adding
        if not is_new:
            try:
                old_task = TodoTask.objects.get(pk=self.pk)
                if old_task.status != self.status:
                    # Will be created in signal or view
                    pass
            except TodoTask.DoesNotExist:
                # Task doesn't exist yet, treat as new
                pass
        
        super().save(*args, **kwargs)
        
        # Update project completion percentage
        if self.project_id:  # Check if project is set
            self.project.update_completion_percentage()


class TaskTag(models.Model):
    """
    Tags for categorizing tasks (e.g., 'bug', 'feature', 'documentation')
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, verbose_name='Tên tag')
    color = models.CharField(
        max_length=7, 
        default='#6c757d',
        verbose_name='Màu',
        help_text='Màu hex (e.g., #007bff)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_tags'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TaskComment(models.Model):
    """
    Comments/updates on tasks
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        TodoTask,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Task'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Người bình luận'
    )
    content = models.TextField(verbose_name='Nội dung')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.username if self.user else 'Unknown'} on {self.task.title}"


class TaskHistory(models.Model):
    """
    History of task changes for tracking progress over time
    This helps calculate probability of completion and track velocity
    """
    ACTION_CHOICES = [
        ('created', 'Tạo mới'),
        ('status_changed', 'Thay đổi trạng thái'),
        ('assigned', 'Gán người thực hiện'),
        ('priority_changed', 'Thay đổi ưu tiên'),
        ('updated', 'Cập nhật'),
        ('commented', 'Bình luận'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        TodoTask,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Task'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Người thực hiện'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_value = models.TextField(blank=True, verbose_name='Giá trị cũ')
    new_value = models.TextField(blank=True, verbose_name='Giá trị mới')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.task.title} at {self.created_at}"


class ProjectProgress(models.Model):
    """
    Snapshot of project progress at regular intervals
    Used for analytics and probability calculations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='progress_snapshots',
        verbose_name='Dự án'
    )
    
    # Metrics at this point in time
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    overdue_tasks = models.IntegerField(default=0)
    completion_percentage = models.IntegerField(default=0)
    
    # Velocity metrics (tasks completed per day/week)
    tasks_completed_last_week = models.IntegerField(default=0)
    
    # Metadata
    snapshot_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_progress'
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['project', '-snapshot_date']),
        ]
    
    def __str__(self):
        return f"{self.project.name} - {self.snapshot_date.date()}"
