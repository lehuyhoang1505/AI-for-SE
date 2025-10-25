"""
Unit tests for is_participant_available() function
Tests all scenarios from the test design document
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
    
    def test_busy_slot_exactly_matching_time_range(self, sample_meeting_request, create_participant, create_busy_slot):
        """Basic Conflict: Busy slot exactly matching time range"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        create_busy_slot(participant, start_time, end_time)
        
        result = is_participant_available(participant, start_time, end_time)
        
        assert result is False, "Participant should be unavailable when busy slot exactly matches"
    
    def test_partial_overlap_at_start(self, sample_meeting_request, create_participant, create_busy_slot):
        """Partial Overlap: Busy slot partially overlapping at start"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 08:30-09:30, checking 09:00-10:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 8, 30))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 30))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is False, "Participant should be unavailable with partial overlap at start"
    
    def test_partial_overlap_at_end(self, sample_meeting_request, create_participant, create_busy_slot):
        """Partial Overlap: Busy slot partially overlapping at end"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 09:30-10:30, checking 09:00-10:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 30))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 30))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is False, "Participant should be unavailable with partial overlap at end"
    
    def test_busy_slot_completely_within_checking_range(self, sample_meeting_request, create_participant, create_busy_slot):
        """Containment: Busy slot completely within checking range"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 09:15-09:45, checking 09:00-10:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 15))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 45))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is False, "Participant should be unavailable when busy slot is within range"
    
    def test_checking_range_completely_within_busy_slot(self, sample_meeting_request, create_participant, create_busy_slot):
        """Containment: Checking range completely within busy slot"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 08:00-11:00, checking 09:00-10:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 8, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 11, 0))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is False, "Participant should be unavailable when check range is within busy slot"
    
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
    
    def test_boundary_adjacent_before(self, sample_meeting_request, create_participant, create_busy_slot):
        """Boundary: Busy slot ending exactly when checking starts"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 08:00-09:00, checking 09:00-10:00 (touching boundary)
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 8, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is True, "Participant should be available when busy slot ends exactly when checking starts"
    
    def test_boundary_adjacent_after(self, sample_meeting_request, create_participant, create_busy_slot):
        """Boundary: Busy slot starting exactly when checking ends"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 10:00-11:00, checking 09:00-10:00 (touching boundary)
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 11, 0))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is True, "Participant should be available when busy slot starts exactly when checking ends"
    
    def test_no_conflict_busy_slot_before(self, sample_meeting_request, create_participant, create_busy_slot):
        """No Conflict: Busy slot before checking range"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 07:00-08:00, checking 09:00-10:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 7, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 8, 0))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is True, "Participant should be available when busy slot is before checking range"
    
    def test_no_conflict_busy_slot_after(self, sample_meeting_request, create_participant, create_busy_slot):
        """No Conflict: Busy slot after checking range"""
        participant = create_participant(sample_meeting_request, has_responded=True)
        
        # Busy 11:00-12:00, checking 09:00-10:00
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 11, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 12, 0))
        create_busy_slot(participant, busy_start, busy_end)
        
        check_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        check_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        result = is_participant_available(participant, check_start, check_end)
        
        assert result is True, "Participant should be available when busy slot is after checking range"
    
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
