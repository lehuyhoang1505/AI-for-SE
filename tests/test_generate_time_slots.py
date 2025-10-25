"""
Additional utility tests and helper function tests
"""
import pytest
import pytz
from datetime import datetime, date, time
from meetings.utils import generate_time_slots


@pytest.mark.django_db
class TestGenerateTimeSlots:
    """Test suite for generate_time_slots helper function"""
    
    def test_single_day_generation(self, create_meeting_request):
        """Test generating slots for a single day"""
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=30,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            timezone='UTC'
        )
        
        slots = generate_time_slots(meeting_request)
        
        # Should generate slots: 09:00, 09:30, 10:00
        assert len(slots) == 3, "Should generate 3 time slots"
        
        # Verify all slots are tuples of (start, end)
        for slot in slots:
            assert isinstance(slot, tuple), "Each slot should be a tuple"
            assert len(slot) == 2, "Each slot should have start and end time"
            assert isinstance(slot[0], datetime), "Start time should be datetime"
            assert isinstance(slot[1], datetime), "End time should be datetime"
            assert slot[0].tzinfo == pytz.UTC, "Start time should be in UTC"
            assert slot[1].tzinfo == pytz.UTC, "End time should be in UTC"
    
    def test_multiple_days_generation(self, create_meeting_request):
        """Test generating slots across multiple days"""
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 3),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),  # 1 slot per day
            work_days_only=False,
            timezone='UTC'
        )
        
        slots = generate_time_slots(meeting_request)
        
        # Should generate 1 slot per day for 3 days
        assert len(slots) == 3, "Should generate 3 time slots (1 per day)"
    
    def test_skip_weekends(self, create_meeting_request):
        """Test skipping weekends when work_days_only is True"""
        # Jan 1, 2024 is Monday
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=60,
            date_range_start=date(2024, 1, 1),  # Monday
            date_range_end=date(2024, 1, 7),    # Sunday
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            work_days_only=True,
            timezone='UTC'
        )
        
        slots = generate_time_slots(meeting_request)
        
        # Should generate 5 slots (Mon-Fri only)
        assert len(slots) == 5, "Should skip weekends and generate 5 slots"
    
    def test_timezone_conversion(self, create_meeting_request):
        """Test that slots are correctly converted to UTC from other timezones"""
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            timezone='America/New_York'
        )
        
        slots = generate_time_slots(meeting_request)
        
        assert len(slots) == 1, "Should generate 1 slot"
        
        start_utc, end_utc = slots[0]
        
        # 9 AM EST/EDT should be 14:00 UTC (EST is UTC-5, but check for DST)
        # Jan 1 is in EST (not DST)
        assert start_utc.tzinfo == pytz.UTC, "Should be in UTC"
        assert start_utc.hour == 14, "9 AM EST should be 14:00 UTC"
    
    def test_no_slots_when_duration_too_long(self, create_meeting_request):
        """Test that no slots are generated when duration is longer than work hours"""
        meeting_request = create_meeting_request(
            duration_minutes=120,  # 2 hours
            step_size_minutes=30,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),  # Only 1 hour window
            timezone='UTC'
        )
        
        slots = generate_time_slots(meeting_request)
        
        assert len(slots) == 0, "Should not generate slots when duration exceeds work hours"
    
    def test_slot_duration_matches_request(self, create_meeting_request):
        """Test that generated slots have correct duration"""
        meeting_request = create_meeting_request(
            duration_minutes=45,
            step_size_minutes=30,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            timezone='UTC'
        )
        
        slots = generate_time_slots(meeting_request)
        
        # Check each slot has 45-minute duration
        for start, end in slots:
            duration = (end - start).total_seconds() / 60
            assert duration == 45, f"Each slot should be 45 minutes, got {duration}"
    
    def test_slots_respect_step_size(self, create_meeting_request):
        """Test that slots are generated with correct step size"""
        meeting_request = create_meeting_request(
            duration_minutes=30,
            step_size_minutes=15,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            timezone='UTC'
        )
        
        slots = generate_time_slots(meeting_request)
        
        # Verify step size between consecutive slots
        for i in range(len(slots) - 1):
            current_start = slots[i][0]
            next_start = slots[i + 1][0]
            step = (next_start - current_start).total_seconds() / 60
            assert step == 15, f"Step size should be 15 minutes, got {step}"
