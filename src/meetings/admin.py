from django.contrib import admin
from .models import MeetingRequest, Participant, BusySlot, SuggestedSlot
from .project_models import (
    Project, ProjectMembership, TodoTask, TaskTag, 
    TaskComment, TaskHistory, ProjectProgress
)


@admin.register(MeetingRequest)
class MeetingRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'duration_minutes', 'response_rate', 'created_at']
    list_filter = ['status', 'created_at', 'work_days_only']
    search_fields = ['title', 'description', 'created_by_email']
    readonly_fields = ['id', 'token', 'created_at', 'updated_at', 'response_rate']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'description', 'status', 'created_by_email']
        }),
        ('Meeting Configuration', {
            'fields': ['duration_minutes', 'timezone', 'date_range_start', 'date_range_end',
                      'work_hours_start', 'work_hours_end', 'step_size_minutes']
        }),
        ('Options', {
            'fields': ['work_days_only', 'response_deadline']
        }),
        ('Metadata', {
            'fields': ['id', 'token', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'meeting_request', 'has_responded', 'timezone', 'responded_at']
    list_filter = ['has_responded', 'timezone', 'created_at']
    search_fields = ['name', 'email', 'meeting_request__title']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(BusySlot)
class BusySlotAdmin(admin.ModelAdmin):
    list_display = ['participant', 'start_time', 'end_time', 'description']
    list_filter = ['created_at']
    search_fields = ['participant__name', 'participant__email', 'description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'start_time'


@admin.register(SuggestedSlot)
class SuggestedSlotAdmin(admin.ModelAdmin):
    list_display = ['meeting_request', 'start_time', 'end_time', 'available_count', 
                    'total_participants', 'availability_percentage', 'is_locked']
    list_filter = ['is_locked', 'calculated_at']
    search_fields = ['meeting_request__title']
    readonly_fields = ['id', 'calculated_at', 'availability_percentage', 'heatmap_level']
    date_hierarchy = 'start_time'


# =============================================================================
# PROJECT MANAGEMENT ADMIN
# =============================================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'priority', 'leader', 'start_date', 'deadline', 
                    'completion_percentage', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['name', 'description', 'goals', 'leader__username']
    readonly_fields = ['id', 'completion_percentage', 'created_at', 'updated_at']
    date_hierarchy = 'deadline'
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'description', 'goals']
        }),
        ('Status & Priority', {
            'fields': ['status', 'priority']
        }),
        ('Timeline', {
            'fields': ['start_date', 'deadline']
        }),
        ('Team', {
            'fields': ['leader']
        }),
        ('Progress', {
            'fields': ['completion_percentage'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'project__name']
    readonly_fields = ['id', 'joined_at']


@admin.register(TodoTask)
class TodoTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'due_date', 
                    'progress_percentage', 'created_by', 'created_at']
    list_filter = ['status', 'priority', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'project__name', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    filter_horizontal = ['assignees', 'tags']
    date_hierarchy = 'due_date'
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['project', 'title', 'description']
        }),
        ('Status & Priority', {
            'fields': ['status', 'priority', 'progress_percentage']
        }),
        ('Assignment', {
            'fields': ['created_by', 'assignees']
        }),
        ('Timeline', {
            'fields': ['due_date', 'estimated_hours', 'actual_hours']
        }),
        ('Categorization', {
            'fields': ['tags']
        }),
        ('Metadata', {
            'fields': ['id', 'created_at', 'updated_at', 'completed_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at']


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at', 'content_preview']
    list_filter = ['created_at']
    search_fields = ['task__title', 'user__username', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ['task', 'action', 'user', 'created_at', 'description_preview']
    list_filter = ['action', 'created_at']
    search_fields = ['task__title', 'user__username', 'description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description Preview'


@admin.register(ProjectProgress)
class ProjectProgressAdmin(admin.ModelAdmin):
    list_display = ['project', 'snapshot_date', 'total_tasks', 'completed_tasks', 
                    'overdue_tasks', 'completion_percentage', 'tasks_completed_last_week']
    list_filter = ['snapshot_date']
    search_fields = ['project__name']
    readonly_fields = ['id', 'snapshot_date']
    date_hierarchy = 'snapshot_date'
