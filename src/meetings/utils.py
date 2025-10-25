"""
Utility functions for calculating available time slots
Heatmap generation and slot suggestions
"""
from datetime import datetime, timedelta, time
from typing import List, Dict, Tuple
from django.utils import timezone
from django.db.models import Q
import pytz


def generate_time_slots(meeting_request):
    """
    Generate all possible time slots based on meeting request configuration
    Returns list of (start_datetime, end_datetime) tuples in UTC
    """
    slots = []
    
    # Get timezone
    tz = pytz.timezone(meeting_request.timezone)
    
    # Iterate through date range
    current_date = meeting_request.date_range_start
    end_date = meeting_request.date_range_end
    
    while current_date <= end_date:
        # Skip weekends if work_days_only is True
        if meeting_request.work_days_only and current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            current_date += timedelta(days=1)
            continue
        
        # Create datetime for start and end of work hours
        work_start = datetime.combine(current_date, meeting_request.work_hours_start)
        work_end = datetime.combine(current_date, meeting_request.work_hours_end)
        
        # Localize to configured timezone
        work_start = tz.localize(work_start)
        work_end = tz.localize(work_end)
        
        # Generate slots with step size
        current_slot_start = work_start
        step = timedelta(minutes=meeting_request.step_size_minutes)
        duration = timedelta(minutes=meeting_request.duration_minutes)
        
        while current_slot_start + duration <= work_end:
            slot_end = current_slot_start + duration
            
            # Convert to UTC for storage
            slots.append((
                current_slot_start.astimezone(pytz.UTC),
                slot_end.astimezone(pytz.UTC)
            ))
            
            current_slot_start += step
        
        current_date += timedelta(days=1)
    
    return slots


def is_participant_available(participant, start_time, end_time):
    """
    Check if a participant is available during a specific time slot
    Returns True if available (no busy slots conflict), False otherwise
    """
    from .models import BusySlot
    
    # Check for any overlapping busy slots
    overlapping = BusySlot.objects.filter(
        participant=participant
    ).filter(
        Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
    )
    
    return not overlapping.exists()


def calculate_slot_availability(meeting_request, start_time, end_time):
    """
    Calculate how many participants are available for a specific time slot
    Returns (available_count, total_count, participant_ids_available)
    """
    from .models import Participant
    
    participants = meeting_request.participants.filter(has_responded=True)
    total_count = participants.count()
    
    if total_count == 0:
        return 0, 0, []
    
    available_participants = []
    
    for participant in participants:
        if is_participant_available(participant, start_time, end_time):
            available_participants.append(participant.id)
    
    return len(available_participants), total_count, available_participants


def generate_suggested_slots(meeting_request, force_recalculate=False):
    """
    Generate or update suggested slots for a meeting request
    This is the main algorithm that creates the heatmap data
    
    Returns: List of SuggestedSlot objects
    """
    from .models import SuggestedSlot
    
    # Clear existing suggestions if force recalculate
    if force_recalculate:
        SuggestedSlot.objects.filter(meeting_request=meeting_request).delete()
    
    # Generate all possible time slots
    possible_slots = generate_time_slots(meeting_request)
    
    suggested_slots = []
    
    for start_time, end_time in possible_slots:
        # Calculate availability for this slot
        available_count, total_count, participant_ids = calculate_slot_availability(
            meeting_request, start_time, end_time
        )
        
        # Only create suggestion if at least one person is available
        # Or create all for heatmap visualization
        slot, created = SuggestedSlot.objects.update_or_create(
            meeting_request=meeting_request,
            start_time=start_time,
            end_time=end_time,
            defaults={
                'available_count': available_count,
                'total_participants': total_count,
            }
        )
        
        suggested_slots.append(slot)
    
    return suggested_slots


def get_top_suggestions(meeting_request, limit=10, min_availability_pct=50):
    """
    Get top suggested slots sorted by availability
    
    Args:
        meeting_request: MeetingRequest instance
        limit: Maximum number of suggestions to return
        min_availability_pct: Minimum percentage of participants that must be available
    
    Returns: QuerySet of SuggestedSlot objects
    """
    from .models import SuggestedSlot
    
    suggestions = SuggestedSlot.objects.filter(
        meeting_request=meeting_request
    ).order_by('-available_count', 'start_time')
    
    # Filter by minimum availability percentage
    filtered_suggestions = [
        s for s in suggestions 
        if s.availability_percentage >= min_availability_pct
    ]
    
    return filtered_suggestions[:limit]


def get_heatmap_data(meeting_request, participant_timezone='Asia/Ho_Chi_Minh'):
    """
    Generate heatmap data for visualization
    Returns data structure suitable for frontend rendering
    
    Returns:
        {
            'dates': ['2024-01-01', '2024-01-02', ...],
            'time_slots': ['09:00', '09:30', '10:00', ...],
            'heatmap': {
                '2024-01-01': {
                    '09:00': {'level': 5, 'available': 10, 'total': 10},
                    '09:30': {'level': 4, 'available': 8, 'total': 10},
                    ...
                },
                ...
            },
            'timezone': 'Asia/Ho_Chi_Minh'
        }
    """
    from .models import SuggestedSlot
    
    tz = pytz.timezone(participant_timezone)
    
    # Get all suggested slots
    slots = SuggestedSlot.objects.filter(meeting_request=meeting_request)
    
    # If no suggested slots exist, generate time slots from meeting request configuration
    if not slots.exists():
        # Generate all possible time slots
        possible_slots = generate_time_slots(meeting_request)
        
        # Organize data by date and time
        heatmap = {}
        dates_set = set()
        times_set = set()
        
        for start_time_utc, end_time_utc in possible_slots:
            # Convert to participant's timezone
            local_start = start_time_utc.astimezone(tz)
            
            date_str = local_start.strftime('%Y-%m-%d')
            time_str = local_start.strftime('%H:%M')
            
            dates_set.add(date_str)
            times_set.add(time_str)
            
            if date_str not in heatmap:
                heatmap[date_str] = {}
            
            heatmap[date_str][time_str] = {
                'level': 0,
                'available': 0,
                'total': 0,
                'percentage': 0,
                'start_utc': start_time_utc.isoformat(),
                'end_utc': end_time_utc.isoformat(),
            }
        
        # Sort dates and times
        dates = sorted(list(dates_set))
        times = sorted(list(times_set))
        
        return {
            'dates': dates,
            'time_slots': times,
            'heatmap': heatmap,
            'timezone': participant_timezone,
        }
    
    # Organize data by date and time from suggested slots
    heatmap = {}
    dates_set = set()
    times_set = set()
    
    for slot in slots:
        # Convert to participant's timezone
        local_start = slot.start_time.astimezone(tz)
        
        date_str = local_start.strftime('%Y-%m-%d')
        time_str = local_start.strftime('%H:%M')
        
        dates_set.add(date_str)
        times_set.add(time_str)
        
        if date_str not in heatmap:
            heatmap[date_str] = {}
        
        heatmap[date_str][time_str] = {
            'level': slot.heatmap_level,
            'available': slot.available_count,
            'total': slot.total_participants,
            'percentage': slot.availability_percentage,
            'start_utc': slot.start_time.isoformat(),
            'end_utc': slot.end_time.isoformat(),
        }
    
    # Sort dates and times
    dates = sorted(list(dates_set))
    times = sorted(list(times_set))
    
    return {
        'dates': dates,
        'time_slots': times,
        'heatmap': heatmap,
        'timezone': participant_timezone,
    }



def format_datetime_for_timezone(dt, timezone_str):
    """
    Format a datetime object for display in a specific timezone
    """
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    tz = pytz.timezone(timezone_str)
    local_dt = dt.astimezone(tz)
    
    return local_dt.strftime('%Y-%m-%d %H:%M')


def parse_busy_slots_from_json(json_data, participant_timezone):
    """
    Parse busy slots from JSON format (from frontend)
    Expected format: [{'start': '2024-01-01T09:00', 'end': '2024-01-01T10:00'}, ...]
    
    Returns: List of (start_datetime_utc, end_datetime_utc) tuples
    """
    tz = pytz.timezone(participant_timezone)
    slots = []
    
    for slot_data in json_data:
        # Parse datetime strings
        start_str = slot_data.get('start')
        end_str = slot_data.get('end')
        
        if not start_str or not end_str:
            continue
        
        # Parse and localize
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        
        # If naive, assume participant's timezone
        if start_dt.tzinfo is None:
            start_dt = tz.localize(start_dt)
        if end_dt.tzinfo is None:
            end_dt = tz.localize(end_dt)
        
        # Convert to UTC
        slots.append((
            start_dt.astimezone(pytz.UTC),
            end_dt.astimezone(pytz.UTC)
        ))
    
    return slots
