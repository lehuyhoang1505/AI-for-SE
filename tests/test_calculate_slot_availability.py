"""
Unit tests for calculate_slot_availability() function
Tests all scenarios from the test design document
"""
import pytest
import pytz
from datetime import datetime
from meetings.utils import calculate_slot_availability


@pytest.mark.django_db
class TestCalculateSlotAvailability:
    """Test suite for calculate_slot_availability function"""
    
    def test_no_participants(self, sample_meeting_request):
        """No Participants: Meeting request with no participants"""
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 0, "Should have 0 available participants"
        assert total == 0, "Should have 0 total participants"
        assert participant_ids == [], "Should have empty participant list"
    
    def test_no_responses(self, sample_meeting_request, create_participant):
        """No Responses: Participants exist but none responded"""
        # Create 3 participants, none responded
        for i in range(3):
            create_participant(sample_meeting_request, has_responded=False)
        
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 0, "Should have 0 available (only count responded)"
        assert total == 0, "Should have 0 total (only count responded)"
        assert participant_ids == [], "Should have empty participant list"
    
    def test_all_available(self, sample_meeting_request, create_participant):
        """All Available: All participants available"""
        # Create 5 participants, all responded and available
        participants = []
        for i in range(5):
            p = create_participant(
                sample_meeting_request, 
                has_responded=True,
                email=f'participant{i}@test.com'
            )
            participants.append(p)
        
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 5, "All 5 participants should be available"
        assert total == 5, "Total should be 5"
        assert len(participant_ids) == 5, "Should have 5 participant IDs"
        
        # Check all participant IDs are included
        expected_ids = {str(p.id) for p in participants}
        actual_ids = {str(pid) for pid in participant_ids}
        assert expected_ids == actual_ids, "All participant IDs should be in the list"
    
    def test_partial_availability(self, sample_meeting_request):
        """Partial Availability: Some available, some busy (optimized with bulk_create)"""
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        from meetings.models import Participant, BusySlot
        
        # Create 10 participants using bulk_create: 7 available, 3 busy
        available_participants = [
            Participant(
                meeting_request=sample_meeting_request,
                has_responded=True,
                email=f'available{i}@test.com',
                name=f'Available {i}',
                timezone='UTC'
            ) for i in range(7)
        ]
        Participant.objects.bulk_create(available_participants)
        
        # Create 3 busy participants
        busy_participants = [
            Participant(
                meeting_request=sample_meeting_request,
                has_responded=True,
                email=f'busy{i}@test.com',
                name=f'Busy {i}',
                timezone='UTC'
            ) for i in range(3)
        ]
        busy_participants = Participant.objects.bulk_create(busy_participants)
        
        # Add busy slots
        busy_slots = [
            BusySlot(
                participant=p,
                start_time=start_time,
                end_time=end_time,
                description='Busy'
            ) for p in busy_participants
        ]
        BusySlot.objects.bulk_create(busy_slots)
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 7, "7 participants should be available"
        assert total == 10, "Total should be 10"
        assert len(participant_ids) == 7, "Should have 7 participant IDs"
    
    def test_none_available(self, sample_meeting_request, create_participant, create_busy_slot):
        """None Available: All participants busy"""
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        # Create 5 participants, all responded but all busy
        for i in range(5):
            p = create_participant(
                sample_meeting_request, 
                has_responded=True,
                email=f'busy{i}@test.com'
            )
            create_busy_slot(p, start_time, end_time)
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 0, "0 participants should be available"
        assert total == 5, "Total should be 5 (includes busy participants)"
        assert participant_ids == [], "Should have empty participant list"
    
    def test_mixed_response(self, sample_meeting_request, create_participant, create_busy_slot):
        """Mixed Response: Some responded, some not"""
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        # 6 responded and available
        for i in range(6):
            create_participant(
                sample_meeting_request, 
                has_responded=True,
                email=f'available{i}@test.com'
            )
        
        # 2 responded but busy
        for i in range(2):
            p = create_participant(
                sample_meeting_request, 
                has_responded=True,
                email=f'busy{i}@test.com'
            )
            create_busy_slot(p, start_time, end_time)
        
        # 2 not responded
        for i in range(2):
            create_participant(
                sample_meeting_request, 
                has_responded=False,
                email=f'notresponded{i}@test.com'
            )
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 6, "6 participants should be available"
        assert total == 8, "Total should be 8 (only count who responded)"
        assert len(participant_ids) == 6, "Should have 6 participant IDs"
    
    def test_complex_busy_patterns(self, sample_meeting_request, create_participant, create_busy_slot):
        """Complex Busy Patterns: Participants with multiple busy slots"""
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        # P1: busy 09:00-09:30
        p1 = create_participant(sample_meeting_request, has_responded=True, email='p1@test.com')
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 30))
        create_busy_slot(p1, busy_start, busy_end)
        
        # P2: busy 09:30-10:00
        p2 = create_participant(sample_meeting_request, has_responded=True, email='p2@test.com')
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 9, 30))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        create_busy_slot(p2, busy_start, busy_end)
        
        # P3: no busy slots
        p3 = create_participant(sample_meeting_request, has_responded=True, email='p3@test.com')
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 1, "Only P3 should be available for entire slot"
        assert total == 3, "Total should be 3"
        assert len(participant_ids) == 1, "Should have 1 participant ID"
        assert str(p3.id) in [str(pid) for pid in participant_ids], "P3 should be in available list"
    
    def test_boundary_testing(self, sample_meeting_request, create_participant, create_busy_slot):
        """Boundary Testing: Participants with adjacent busy slots"""
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        # P1: busy 08:00-09:00 (adjacent before)
        p1 = create_participant(sample_meeting_request, has_responded=True, email='p1@test.com')
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 8, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        create_busy_slot(p1, busy_start, busy_end)
        
        # P2: busy 10:00-11:00 (adjacent after)
        p2 = create_participant(sample_meeting_request, has_responded=True, email='p2@test.com')
        busy_start = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        busy_end = pytz.UTC.localize(datetime(2024, 1, 1, 11, 0))
        create_busy_slot(p2, busy_start, busy_end)
        
        # P3: busy 09:00-10:00 (exact overlap)
        p3 = create_participant(sample_meeting_request, has_responded=True, email='p3@test.com')
        create_busy_slot(p3, start_time, end_time)
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 2, "P1 and P2 should be available (adjacent OK)"
        assert total == 3, "Total should be 3"
        assert len(participant_ids) == 2, "Should have 2 participant IDs"
    
    def test_single_participant(self, sample_meeting_request, create_participant):
        """Single Participant: Only one participant responded"""
        p = create_participant(sample_meeting_request, has_responded=True)
        
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 1, "Single participant should be available"
        assert total == 1, "Total should be 1"
        assert len(participant_ids) == 1, "Should have 1 participant ID"
        assert str(p.id) in [str(pid) for pid in participant_ids], "Participant ID should match"
    
    def test_large_group(self, sample_meeting_request):
        """Large Group: Many participants (optimized with bulk_create)"""
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        # Create 20 participants using bulk_create: 15 available, 5 busy
        from meetings.models import Participant, BusySlot
        
        # Create available participants
        available_participants = [
            Participant(
                meeting_request=sample_meeting_request,
                has_responded=True,
                email=f'available{i}@test.com',
                name=f'Available {i}',
                timezone='UTC'
            ) for i in range(15)
        ]
        Participant.objects.bulk_create(available_participants)
        
        # Create busy participants
        busy_participants = [
            Participant(
                meeting_request=sample_meeting_request,
                has_responded=True,
                email=f'busy{i}@test.com',
                name=f'Busy {i}',
                timezone='UTC'
            ) for i in range(5)
        ]
        busy_participants = Participant.objects.bulk_create(busy_participants)
        
        # Create busy slots for busy participants
        busy_slots = [
            BusySlot(
                participant=p,
                start_time=start_time,
                end_time=end_time,
                description='Busy'
            ) for p in busy_participants
        ]
        BusySlot.objects.bulk_create(busy_slots)
        
        available, total, participant_ids = calculate_slot_availability(
            sample_meeting_request, start_time, end_time
        )
        
        assert available == 15, "15 participants should be available"
        assert total == 20, "Total should be 20"
        assert len(participant_ids) == 15, "Should have 15 participant IDs"
    
    def test_timezone_edge_case(self, create_meeting_request, create_participant):
        """Timezone Edge Case: Participants in different timezones (UTC storage)"""
        # Create meeting request with Asia/Tokyo timezone
        meeting_request = create_meeting_request(timezone='Asia/Tokyo')
        
        # Create 3 participants
        for i in range(3):
            create_participant(
                meeting_request, 
                has_responded=True,
                timezone='Asia/Tokyo',
                email=f'participant{i}@test.com'
            )
        
        # Check availability in UTC
        start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
        
        available, total, participant_ids = calculate_slot_availability(
            meeting_request, start_time, end_time
        )
        
        assert available == 3, "All 3 participants should be available"
        assert total == 3, "Total should be 3"
        assert len(participant_ids) == 3, "Should have 3 participant IDs (UTC storage ensures consistency)"
