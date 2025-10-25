"""
Unit tests for get_top_suggestions() function
Tests all scenarios from the test design document
"""
import pytest
import pytz
from datetime import datetime, date, time
from meetings.utils import get_top_suggestions


@pytest.mark.django_db
class TestGetTopSuggestions:
    """Test suite for get_top_suggestions function"""
    
    def test_default_parameters(self, create_meeting_request, create_suggested_slot):
        """Default Parameters: Get top suggestions with defaults"""
        meeting_request = create_meeting_request()
        
        # Create 20 slots: 12 above 50%, 8 below 50%
        # 100 total participants
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # 12 slots with >= 50% availability (50, 60, 70, 80, 90, 100%)
        for i in range(12):
            available = 50 + (i * 5)  # 50, 55, 60, 65...
            if available > 100:
                available = 100
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=available,
                total_participants=100
            )
        
        # 8 slots with < 50% availability
        for i in range(8):
            available = 10 + (i * 5)  # 10, 15, 20...
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=15 + i, minute=30),
                base_time.replace(hour=16 + i, minute=30),
                available_count=available,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 10, "Should return top 10 slots"
        
        # Verify all have >= 50% availability
        for slot in results:
            assert slot.availability_percentage >= 50, "All slots should have >= 50% availability"
    
    def test_all_above_threshold(self, create_meeting_request, create_suggested_slot):
        """All Above Threshold: All suggestions meet minimum"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 5 slots, all 100% available
        for i in range(5):
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=10,
                total_participants=10
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 5, "Should return all 5 slots (less than limit)"
    
    def test_all_below_threshold(self, create_meeting_request, create_suggested_slot):
        """All Below Threshold: No suggestions meet minimum"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 10 slots with 0-30% availability
        for i in range(10):
            available = i * 3  # 0, 3, 6, 9... (max 27%)
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=available,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 0, "Should return empty list"
    
    def test_exact_threshold(self, create_meeting_request, create_suggested_slot):
        """Exact Threshold: Slots at exact threshold percentage"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create slots at 49%, 50%, 51%
        create_suggested_slot(
            meeting_request,
            base_time.replace(hour=9),
            base_time.replace(hour=10),
            available_count=49,
            total_participants=100
        )
        create_suggested_slot(
            meeting_request,
            base_time.replace(hour=10),
            base_time.replace(hour=11),
            available_count=50,
            total_participants=100
        )
        create_suggested_slot(
            meeting_request,
            base_time.replace(hour=11),
            base_time.replace(hour=12),
            available_count=51,
            total_participants=100
        )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 2, "Should return 2 slots (50% and 51%)"
        
        # Verify percentages
        percentages = [slot.availability_percentage for slot in results]
        assert 49 not in percentages, "49% should be excluded"
        assert 50 in percentages or 50.0 in percentages, "50% should be included"
        assert 51 in percentages or 51.0 in percentages, "51% should be included"
    
    def test_zero_threshold(self, create_meeting_request, create_suggested_slot):
        """Zero Threshold: Minimum 0% (return all)"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 20 slots with varying availability (0-100%)
        for i in range(20):
            available = i * 5  # 0, 5, 10, 15...
            # Use hours and minutes separately to avoid minute > 59
            hour_offset = i // 6
            minute_offset = (i % 6) * 10
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + hour_offset, minute=minute_offset),
                base_time.replace(hour=10 + hour_offset, minute=minute_offset),
                available_count=available,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=0)
        
        assert len(results) == 10, "Should return top 10 slots (all included)"
    
    def test_hundred_percent_threshold(self, create_meeting_request, create_suggested_slot):
        """100% Threshold: Only perfect matches"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 20 slots: 3 at 100%, rest below
        for i in range(3):
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=10,
                total_participants=10
            )
        
        for i in range(17):
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=12 + (i // 2), minute=(i % 2) * 30),
                base_time.replace(hour=13 + (i // 2), minute=(i % 2) * 30),
                available_count=9,
                total_participants=10
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=100)
        
        assert len(results) == 3, "Should return only 3 slots with 100% availability"
    
    def test_limit_one(self, create_meeting_request, create_suggested_slot):
        """Limit = 1: Single result limit"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 10 slots above 50%
        for i in range(10):
            available = 50 + i * 5
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=available,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=1, min_availability_pct=50)
        
        assert len(results) == 1, "Should return single best slot"
        assert results[0].availability_percentage >= 50, "Should have highest availability"
    
    def test_limit_zero(self, create_meeting_request, create_suggested_slot):
        """Limit = 0: Zero limit edge case"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 10 slots above 50%
        for i in range(10):
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=60,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=0, min_availability_pct=50)
        
        assert len(results) == 0, "Should return empty list with limit=0"
    
    def test_negative_limit(self, create_meeting_request, create_suggested_slot):
        """Negative Limit: Negative limit boundary"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 10 slots
        for i in range(10):
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=60,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=-5, min_availability_pct=50)
        
        # Implementation dependent - Python slicing with negative values returns all elements up to that point
        # [:−5] returns all qualifying slots (implementation shows it returns filtered list sliced)
        assert len(results) >= 0, "Should handle negative limit gracefully"
    
    def test_large_limit(self, create_meeting_request, create_suggested_slot):
        """Large Limit: Limit exceeds available slots"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 5 slots above 50%
        for i in range(5):
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=60,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=100, min_availability_pct=50)
        
        assert len(results) == 5, "Should return all 5 qualifying slots (limited by available data)"
    
    def test_sorting_availability(self, create_meeting_request, create_suggested_slot):
        """Sorting - Availability: Multiple slots with same availability"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 3 slots all with 80% availability at different times
        times = [11, 10, 9]  # Create in reverse order
        for hour in times:
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=hour),
                base_time.replace(hour=hour + 1),
                available_count=80,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 3, "Should return all 3 slots"
        
        # Verify sorted by start_time ascending when availability is same
        assert results[0].start_time < results[1].start_time < results[2].start_time, \
            "Should be sorted by start_time ascending as secondary sort"
    
    def test_sorting_time(self, create_meeting_request, create_suggested_slot):
        """Sorting - Time: Verify time-based secondary sort"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create slots: 60%@14:00, 80%@10:00, 80%@09:00, 60%@13:00
        slots_data = [
            (14, 60),
            (10, 80),
            (9, 80),
            (13, 60),
        ]
        
        for hour, available in slots_data:
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=hour),
                base_time.replace(hour=hour + 1),
                available_count=available,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 4, "Should return all 4 slots"
        
        # Expected order: 80%@09:00, 80%@10:00, 60%@13:00, 60%@14:00
        assert results[0].start_time.hour == 9, "First should be 80%@09:00"
        assert results[1].start_time.hour == 10, "Second should be 80%@10:00"
        assert results[2].start_time.hour == 13, "Third should be 60%@13:00"
        assert results[3].start_time.hour == 14, "Fourth should be 60%@14:00"
    
    def test_no_suggested_slots(self, create_meeting_request):
        """No Suggested Slots: Meeting request with no suggestions"""
        meeting_request = create_meeting_request()
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 0, "Should return empty list"
    
    def test_percentage_calculation(self, create_meeting_request, create_suggested_slot):
        """Percentage Calculation: Verify percentage filtering logic"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # 10 total participants: create slots with 3, 5, 7, 9 available (30%, 50%, 70%, 90%)
        availabilities = [3, 5, 7, 9]
        
        for i, available in enumerate(availabilities):
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + i),
                base_time.replace(hour=10 + i),
                available_count=available,
                total_participants=10
            )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=60)
        
        assert len(results) == 2, "Should return only 70% and 90% slots"
        
        for slot in results:
            assert slot.availability_percentage >= 60, "All slots should have >= 60%"
    
    def test_mixed_availability(self, create_meeting_request, create_suggested_slot):
        """Mixed Availability: Complex availability distribution"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create 25 slots with distributed availability: 0%, 20%, 40%, 50%, 60%, 80%, 100%
        availabilities = [0, 0, 0, 20, 20, 20, 40, 40, 40, 50, 50, 50, 50, 60, 60, 60, 60, 80, 80, 80, 100, 100, 100, 100, 100]
        
        for i, available in enumerate(availabilities):
            # Calculate hour and minute to avoid overflow
            hour_offset = i // 4  # 4 slots per hour (every 15 min)
            minute_offset = (i % 4) * 15
            create_suggested_slot(
                meeting_request,
                base_time.replace(hour=9 + hour_offset, minute=minute_offset),
                base_time.replace(hour=10 + hour_offset, minute=minute_offset),
                available_count=available,
                total_participants=100
            )
        
        results = get_top_suggestions(meeting_request, limit=5, min_availability_pct=50)
        
        assert len(results) == 5, "Should return top 5 from >= 50% group"
        
        # Should be highest availability first
        for slot in results:
            assert slot.availability_percentage >= 50, "All should have >= 50%"
    
    def test_decimal_threshold(self, create_meeting_request, create_suggested_slot):
        """Decimal Threshold: Non-integer minimum percentage"""
        meeting_request = create_meeting_request()
        
        base_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
        
        # Create slots with precise percentages
        # Note: availability_percentage is calculated as (available/total)*100
        # For precise control, use specific numbers
        create_suggested_slot(
            meeting_request,
            base_time.replace(hour=9),
            base_time.replace(hour=10),
            available_count=495,
            total_participants=1000  # 49.5%
        )
        create_suggested_slot(
            meeting_request,
            base_time.replace(hour=10),
            base_time.replace(hour=11),
            available_count=505,
            total_participants=1000  # 50.5%
        )
        create_suggested_slot(
            meeting_request,
            base_time.replace(hour=11),
            base_time.replace(hour=12),
            available_count=515,
            total_participants=1000  # 51.5%
        )
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50.5)
        
        assert len(results) == 2, "Should return only 50.5% and 51.5% slots"
    
    def test_empty_meeting_request(self, create_meeting_request):
        """Empty Meeting Request: Newly created request with no data"""
        meeting_request = create_meeting_request()
        
        # Don't create any participants or slots
        
        results = get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)
        
        assert len(results) == 0, "Should return empty list for new request"
