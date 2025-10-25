"""
Unit tests for is_participant_available() function
Tests all scenarios from the test design document (optimized with parametrization)
"""
import pytest
import pytz
from datetime import datetime
from meetings.utils import is_participant_available


@pytest.mark.django_db
class TestIsParticipantAvailable:
    """Test suite for is_participant_available function"""
    
    def test_participant_with_no_busy_slots(self, sample_meeting_request, create_participant):
        """Basic Availability: Participant with no busy slots"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, start_time, end_time)
        
        assert result is True, "Participant should be available when no busy slots exist"
    
    @pytest.mark.parametrize("busy_start_hour,busy_start_min,busy_end_hour,busy_end_min,expected,scenario", [
        (9, 0, 10, 0, False, "Exact match"),
        (8, 30, 9, 30, False, "Partial overlap at start"),
        (9, 30, 10, 30, False, "Partial overlap at end"),
        (9, 15, 9, 45, False, "Busy within check range"),
        (8, 0, 11, 0, False, "Check range within busy"),
        (8, 0, 9, 0, True, "Adjacent before (busy ends when check starts)"),
        (10, 0, 11, 0, True, "Adjacent after (busy starts when check ends)"),
    ])
    def test_overlap_scenarios(self, sample_meeting_request, create_participant, create_busy_slot,
                               busy_start_hour, busy_start_min, busy_end_hour, busy_end_min, expected, scenario):
        """Parametrized test for various overlap scenarios"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, busy_start_hour, busy_start_min))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, busy_end_hour, busy_end_min))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is expected, f"Failed for scenario: {scenario}"
    
    def test_multiple_overlapping_busy_slots(self, sample_meeting_request, create_participant, create_busy_slot):
        """Multiple Conflicts: Multiple overlapping busy slots"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Multiple busy slots: 09:00-09:30 and 09:15-09:45
        busy1_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        busy1_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 30))
        create_busy_slot(participant, busy1_start, busy1_end)
        
        busy2_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 15))
        busy2_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 45))
        create_busy_slot(participant, busy2_start, busy2_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is False, "Participant should be unavailable with multiple overlapping busy slots"
    
    @pytest.mark.parametrize("busy_start_hour,busy_end_hour,expected,scenario", [
        (7, 8, True, "Busy before check range"),
        (11, 12, True, "Busy after check range"),
    ])
    def test_no_conflict_scenarios(self, sample_meeting_request, create_participant, create_busy_slot,
                                   busy_start_hour, busy_end_hour, expected, scenario):
        """Parametrized test for non-conflicting busy slots"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, busy_start_hour, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, busy_end_hour, 0))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is expected, f"Failed for scenario: {scenario}"
    
    def test_multiple_non_overlapping_busy_slots(self, sample_meeting_request, create_participant, create_busy_slot):
        """Edge Case: Multiple non-overlapping busy slots"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy slots: 07:00-08:00 and 11:00-12:00, checking 09:00-10:00
        busy1_start = pytz.UTC.localize(datetime(2024, 1, 1, 7, 0))
        busy1_end = pytz.UTC.localize(datetime(2024, 1, 1, 8, 0))
        create_busy_slot(participant, busy1_start, busy1_end)
        
        busy2_start = pytz.UTC.localize(datetime(2024, 1, 1, 11, 0))
        busy2_end = pytz.UTC.localize(datetime(2024, 1, 1, 12, 0))
        create_busy_slot(participant, busy2_start, busy2_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is True, "Participant should be available between non-overlapping busy slots"
    
    def test_same_minute_busy_slot(self, sample_meeting_request, create_participant, create_busy_slot):
        """Edge Case: Same-minute busy slot (1 min duration)"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 09:00-09:01, checking 09:00-10:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 1))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is False, "Even 1 minute conflict should make participant unavailable"
    
    def test_cross_day_busy_slot(self, sample_meeting_request, create_participant, create_busy_slot):
        """Edge Case: Cross-day busy slot"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 2024-01-01 23:00 to 2024-01-02 01:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 23, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 2, 1, 0))
        create_busy_slot(participant, busy_start, busy_end)
        
        # Checking 2024-01-01 23:30 to 2024-01-02 00:30
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 23, 30))
        check_end = pytz.UTC.localize(datetime(2024, 1, 2, 0, 30))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is False, "Cross-day overlap should be detected correctly"
