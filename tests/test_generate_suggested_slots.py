"""
Unit tests for generate_suggested_slots() function
Tests all scenarios from the test design document
"""
import pytest
import pytz
from datetime import datetime, date, time, timedelta
from meetings.utils import generate_suggested_slots
from meetings.models import SuggestedSlot


@pytest.mark.django_db
class TestGenerateSuggestedSlots:
    """Test suite for generate_suggested_slots function"""
    
    def test_initial_generation(self, create_meeting_request):
        """Initial Generation: First time generation (no existing slots)"""
        # Create meeting: 60min duration, 30min step, 1 day, 09:00-17:00
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=30,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Expected slots: 09:00, 09:30, 10:00, ..., 16:00
        # From 09:00-17:00 (8 hours), with 60min duration and 30min step
        # Last slot starts at 16:00 and ends at 17:00
        # Calculation: (17:00 - 09:00) = 8 hours = 480 minutes
        # Slots possible: (480 - 60) / 30 + 1 = 420/30 + 1 = 14 + 1 = 15 slots
        expected_slot_count = 15
        
        assert len(slots) == expected_slot_count, f"Should generate {expected_slot_count} slots"
        
        # Verify first slot
        first_slot = slots[0]
        expected_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        assert first_slot.start_time == expected_start, "First slot should start at 09:00"
        
        # Verify all slots are SuggestedSlot objects
        for slot in slots:
            assert isinstance(slot, SuggestedSlot), "All items should be SuggestedSlot objects"
    
    def test_update_existing(self, create_meeting_request, create_participant, create_suggested_slot):
        """Update Existing: Regeneration without force_recalculate"""
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=30,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0)  # 2-hour window
        )
        
        # Create existing slot with old data
        old_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        old_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        create_suggested_slot(
            meeting_request, 
            old_start, 
            old_end,
            available_count=0,
            total_participants=0
        )
        
        # Add a participant
        create_participant(meeting_request, has_responded=True)
        
        # Regenerate without force
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Check that slots are updated
        updated_slot = SuggestedSlot.objects.get(
            meeting_request=meeting_request,
            start_time=old_start
        )
        assert updated_slot.total_participants == 1, "Should update total_participants"
    
    def test_force_recalculate(self, create_meeting_request, create_suggested_slot):
        """Force Recalculate: Complete regeneration with force_recalculate"""
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=30,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0)
        )
        
        # Create 10 old slots with random times
        for i in range(10):
            old_start = pytz.UTC.localize(datetime(2024, 1, 1, 8, i * 5))
            old_end = old_start + timedelta(minutes=60)
            create_suggested_slot(meeting_request, old_start, old_end)
        
        old_count = SuggestedSlot.objects.filter(meeting_request=meeting_request).count()
        assert old_count == 10, "Should have 10 old slots"
        
        # Force recalculate
        slots = generate_suggested_slots(meeting_request, force_recalculate=True)
        
        new_count = SuggestedSlot.objects.filter(meeting_request=meeting_request).count()
        
        # Should have new slots based on configuration
        assert new_count > 0, "Should have new slots"
        assert len(slots) == new_count, "Returned slots should match database"
    
    def test_no_participants(self, create_meeting_request):
        """No Participants: Generate slots with no participants"""
        meeting_request = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 2)
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        assert len(slots) > 0, "Should generate slots even without participants"
        
        for slot in slots:
            assert slot.available_count == 0, "available_count should be 0"
            assert slot.total_participants == 0, "total_participants should be 0"
    
    def test_no_responses(self, create_meeting_request, create_participant):
        """No Responses: Generate slots when no one responded"""
        meeting_request = create_meeting_request()
        
        # Create 5 participants, none responded
        for i in range(5):
            create_participant(meeting_request, has_responded=False)
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        assert len(slots) > 0, "Should generate slots"
        
        for slot in slots:
            assert slot.available_count == 0, "available_count should be 0 (no responses)"
            assert slot.total_participants == 0, "total_participants should be 0 (only count responded)"
    
    def test_partial_responses(self, create_meeting_request, create_participant):
        """Partial Responses: Some participants responded"""
        meeting_request = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0)
        )
        
        # 6 responded
        for i in range(6):
            create_participant(meeting_request, has_responded=True, email=f'responded{i}@test.com')
        
        # 4 not responded
        for i in range(4):
            create_participant(meeting_request, has_responded=False, email=f'notresponded{i}@test.com')
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        assert len(slots) > 0, "Should generate slots"
        
        # Check that total_participants is based on responded only
        for slot in slots:
            assert slot.total_participants == 6, "Should only count 6 responded participants"
    
    def test_weekend_exclusion(self, create_meeting_request):
        """Weekend Exclusion: Work days only = True"""
        # Jan 1, 2024 is Monday; Jan 7, 2024 is Sunday
        meeting_request = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 7),
            work_days_only=True,
            step_size_minutes=60,
            duration_minutes=60,
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0)  # 1 slot per day
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Should only have slots for Mon-Fri (5 days)
        # Each day has 1 slot (09:00-10:00)
        expected_slot_count = 5
        
        assert len(slots) == expected_slot_count, f"Should generate {expected_slot_count} slots (weekdays only)"
    
    def test_include_weekends(self, create_meeting_request):
        """Include Weekends: Work days only = False"""
        meeting_request = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 7),
            work_days_only=False,
            step_size_minutes=60,
            duration_minutes=60,
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0)  # 1 slot per day
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Should have slots for all 7 days
        expected_slot_count = 7
        
        assert len(slots) == expected_slot_count, f"Should generate {expected_slot_count} slots (all days)"
    
    def test_step_size_variation(self, create_meeting_request):
        """Step Size Variation: Different step sizes"""
        # Duration 60min, step 15min, 2-hour window (09:00-11:00)
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=15,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0)
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Possible start times: 09:00, 09:15, 09:30, 09:45, 10:00
        # (10:15 would end at 11:15, which is outside work hours)
        expected_slot_count = 5
        
        assert len(slots) == expected_slot_count, f"Should generate {expected_slot_count} slots with 15-min step"
    
    def test_short_duration(self, create_meeting_request):
        """Short Duration: Minimum duration (15 min)"""
        meeting_request = create_meeting_request(
            duration_minutes=15,
            step_size_minutes=15,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0)
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Possible start times: 09:00, 09:15, 09:30, 09:45
        expected_slot_count = 4
        
        assert len(slots) == expected_slot_count, f"Should generate {expected_slot_count} slots"
    
    def test_long_duration(self, create_meeting_request):
        """Long Duration: Maximum duration (8 hours)"""
        meeting_request = create_meeting_request(
            duration_minutes=480,  # 8 hours
            step_size_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0)  # 8-hour window
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Only one 8-hour slot fits: 09:00-17:00
        expected_slot_count = 1
        
        assert len(slots) == expected_slot_count, f"Should generate {expected_slot_count} slot (8-hour meeting)"
    
    def test_extended_date_range(self, create_meeting_request):
        """Extended Date Range: Multi-week range"""
        # 14 days, work days only
        meeting_request = create_meeting_request(
            date_range_start=date(2024, 1, 1),  # Monday
            date_range_end=date(2024, 1, 14),   # Sunday (2 weeks)
            work_days_only=True,
            step_size_minutes=60,
            duration_minutes=60,
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0)  # 1 slot per day
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # 2 weeks = 10 weekdays
        expected_slot_count = 10
        
        assert len(slots) == expected_slot_count, f"Should generate {expected_slot_count} slots (10 weekdays)"
    
    def test_availability_variations(self, create_meeting_request, create_participant, create_busy_slot):
        """Availability Variations: Slots with different availability levels"""
        meeting_request = create_meeting_request(
            duration_minutes=60,
            step_size_minutes=60,
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(12, 0)  # 3 slots
        )
        
        # Create 10 participants
        participants = []
        for i in range(10):
            p = create_participant(meeting_request, has_responded=True, email=f'p{i}@test.com')
            participants.append(p)
        
        # First slot (09:00-10:00): 3 busy
        slot1_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        slot1_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        for i in range(3):
            create_busy_slot(participants[i], slot1_start, slot1_end)
        
        # Second slot (10:00-11:00): 7 busy
        slot2_start = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        slot2_end = pytz.UTC.localize(datetime(2024, 1, 1, 11, 0))
        for i in range(7):
            create_busy_slot(participants[i], slot2_start, slot2_end)
        
        # Third slot (11:00-12:00): all available
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        assert len(slots) == 3, "Should generate 3 slots"
        
        # Verify different availability counts
        slot_dict = {slot.start_time: slot for slot in slots}
        
        assert slot_dict[slot1_start].available_count == 7, "First slot should have 7 available"
        assert slot_dict[slot2_start].available_count == 3, "Second slot should have 3 available"
    
    def test_timezone_handling(self, create_meeting_request):
        """Timezone Handling: Non-UTC timezone configuration"""
        # Create meeting in America/New_York timezone
        meeting_request = create_meeting_request(
            timezone='America/New_York',
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            work_hours_start=time(9, 0),
            work_hours_end=time(17, 0),
            duration_minutes=60,
            step_size_minutes=60
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        assert len(slots) > 0, "Should generate slots"
        
        # Verify slots are stored in UTC
        for slot in slots:
            assert slot.start_time.tzinfo == pytz.UTC, "Start time should be in UTC"
            assert slot.end_time.tzinfo == pytz.UTC, "End time should be in UTC"
    
    def test_same_day_range(self, create_meeting_request):
        """Same Day Range: Single day date range"""
        meeting_request = create_meeting_request(
            date_range_start=date(2024, 1, 1),
            date_range_end=date(2024, 1, 1),
            duration_minutes=60,
            step_size_minutes=60,
            work_hours_start=time(9, 0),
            work_hours_end=time(12, 0)
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Should have slots for only that single day
        # 09:00-12:00 with 60min slots = 3 slots
        expected_slot_count = 3
        
        assert len(slots) == expected_slot_count, "Should generate slots for single day only"
        
        # All slots should be on the same day
        for slot in slots:
            local_time = slot.start_time.astimezone(pytz.UTC)
            assert local_time.date() == date(2024, 1, 1), "All slots should be on Jan 1"
    
    def test_empty_date_range(self, create_meeting_request):
        """Empty Date Range: Start date after end date (invalid)"""
        meeting_request = create_meeting_request(
            date_range_start=date(2024, 1, 10),
            date_range_end=date(2024, 1, 5)  # Before start date
        )
        
        slots = generate_suggested_slots(meeting_request, force_recalculate=False)
        
        # Should return empty list for invalid date range
        assert len(slots) == 0, "Should return empty list for invalid date range"
