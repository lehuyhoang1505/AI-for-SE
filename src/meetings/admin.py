from django.contrib import admin
from .models import MeetingRequest, Participant, BusySlot, SuggestedSlot


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
