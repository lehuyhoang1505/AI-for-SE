# Test Design Document - Calculating Overlapping Free Time Slots

## Overview
Comprehensive unit test cases for the meeting time scheduler's core feature: calculating overlapping free time slots. This document covers all functions in `meetings/utils.py` that handle availability calculations and slot suggestions.

---

## Test Cases

### Function 1: `is_participant_available(participant, start_time, end_time)`

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| **Basic Availability** | Participant with no busy slots | `participant` (no busy slots), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `True` - Participant is available |
| **Basic Conflict** | Busy slot exactly matching time range | `participant` (busy: 09:00-10:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `False` - Exact match conflict |
| **Partial Overlap** | Busy slot partially overlapping at start | `participant` (busy: 08:30-09:30), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `False` - Overlaps first 30 minutes |
| **Partial Overlap** | Busy slot partially overlapping at end | `participant` (busy: 09:30-10:30), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `False` - Overlaps last 30 minutes |
| **Containment** | Busy slot completely within checking range | `participant` (busy: 09:15-09:45), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `False` - Busy slot contained in check range |
| **Containment** | Checking range completely within busy slot | `participant` (busy: 08:00-11:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `False` - Check range contained in busy slot |
| **Multiple Conflicts** | Multiple overlapping busy slots | `participant` (busy: 09:00-09:30, 09:15-09:45), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `False` - Multiple conflicts detected |
| **Boundary - Adjacent Before** | Busy slot ending exactly when checking starts | `participant` (busy: 08:00-09:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `True` - No overlap (touching boundary OK) |
| **Boundary - Adjacent After** | Busy slot starting exactly when checking ends | `participant` (busy: 10:00-11:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `True` - No overlap (touching boundary OK) |
| **No Conflict** | Busy slot before checking range | `participant` (busy: 07:00-08:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `True` - No overlap |
| **No Conflict** | Busy slot after checking range | `participant` (busy: 11:00-12:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `True` - No overlap |
| **Edge Case** | Multiple non-overlapping busy slots | `participant` (busy: 07:00-08:00, 11:00-12:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `True` - Available between busy slots |
| **Edge Case** | Same-minute busy slot (1 min duration) | `participant` (busy: 09:00-09:01), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `False` - Even 1 minute counts as conflict |
| **Edge Case** | Cross-day busy slot | `participant` (busy: 2024-01-01 23:00 - 2024-01-02 01:00), `start_time=2024-01-01 23:30 UTC`, `end_time=2024-01-02 00:30 UTC` | `False` - Cross-day overlap detected |

---

### Function 2: `calculate_slot_availability(meeting_request, start_time, end_time)`

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| **No Participants** | Meeting request with no participants | `meeting_request` (0 participants), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(0, 0, [])` - Empty result |
| **No Responses** | Participants exist but none responded | `meeting_request` (3 participants, 0 responded), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(0, 0, [])` - Only count responded participants |
| **All Available** | All participants available | `meeting_request` (5 participants, all responded, all available), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(5, 5, [uuid1, uuid2, uuid3, uuid4, uuid5])` |
| **Partial Availability** | Some available, some busy | `meeting_request` (10 participants, 10 responded, 7 available), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(7, 10, [uuid1, uuid2, ..., uuid7])` |
| **None Available** | All participants busy | `meeting_request` (5 participants, 5 responded, 0 available), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(0, 5, [])` - Total count includes busy participants |
| **Mixed Response** | Some responded, some not | `meeting_request` (10 participants: 6 responded & available, 2 responded & busy, 2 not responded), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(6, 8, [uuid1, ..., uuid6])` - Only count 8 who responded |
| **Complex Busy Patterns** | Participants with multiple busy slots | `meeting_request` (3 participants: P1 busy 09:00-09:30, P2 busy 09:30-10:00, P3 no busy slots), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(1, 3, [P3_uuid])` - Only P3 available for entire slot |
| **Boundary Testing** | Participants with adjacent busy slots | `meeting_request` (3 participants: P1 busy 08:00-09:00, P2 busy 10:00-11:00, P3 busy 09:00-10:00), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(2, 3, [P1_uuid, P2_uuid])` - P1 and P2 available (adjacent OK) |
| **Single Participant** | Only one participant responded | `meeting_request` (1 participant, 1 responded, available), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(1, 1, [uuid1])` - Edge case minimum |
| **Large Group** | Many participants (stress test) | `meeting_request` (100 participants, 100 responded, 75 available), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(75, 100, [uuid1, ..., uuid75])` - Handle large groups |
| **Timezone Edge Case** | Participants in different timezones (UTC storage) | `meeting_request` (3 participants in Asia/Tokyo, all available), `start_time=2024-01-01 09:00 UTC`, `end_time=2024-01-01 10:00 UTC` | `(3, 3, [uuid1, uuid2, uuid3])` - UTC storage ensures consistency |

---

### Function 3: `generate_suggested_slots(meeting_request, force_recalculate=False)`

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| **Initial Generation** | First time generation (no existing slots) | `meeting_request` (duration=60min, step=30min, date_range=1 day, work_hours=09:00-17:00), `force_recalculate=False` | List of 16 `SuggestedSlot` objects (slots at 09:00, 09:30, 10:00, ..., 16:00) |
| **Update Existing** | Regeneration without force_recalculate | `meeting_request` (existing slots with old availability data), `force_recalculate=False` | Updated slots with new availability counts, same slot count |
| **Force Recalculate** | Complete regeneration with force_recalculate | `meeting_request` (existing 10 slots), `force_recalculate=True` | Old slots deleted, new complete set created |
| **No Participants** | Generate slots with no participants | `meeting_request` (0 participants, date_range=2 days), `force_recalculate=False` | Slots created with `available_count=0`, `total_participants=0` |
| **No Responses** | Generate slots when no one responded | `meeting_request` (5 participants, 0 responded), `force_recalculate=False` | Slots created with `available_count=0`, `total_participants=0` |
| **Partial Responses** | Some participants responded | `meeting_request` (10 participants: 6 responded, 4 not), `force_recalculate=False` | Slots show availability based on 6 responded participants only |
| **Weekend Exclusion** | Work days only = True | `meeting_request` (date_range=2024-01-01 to 2024-01-07 (Mon-Sun), work_days_only=True), `force_recalculate=False` | Slots generated only for Mon-Fri (5 days) |
| **Include Weekends** | Work days only = False | `meeting_request` (date_range=2024-01-01 to 2024-01-07, work_days_only=False), `force_recalculate=False` | Slots generated for all 7 days |
| **Step Size Variation** | Different step sizes | `meeting_request` (duration=60min, step=15min, 1 day, 09:00-11:00), `force_recalculate=False` | 8 slots: 09:00, 09:15, 09:30, 09:45, 10:00 (5 possible start times within 2-hour window) |
| **Short Duration** | Minimum duration (15 min) | `meeting_request` (duration=15min, step=15min, 1 day, 09:00-10:00), `force_recalculate=False` | 4 slots: 09:00, 09:15, 09:30, 09:45 |
| **Long Duration** | Maximum duration (8 hours) | `meeting_request` (duration=480min, step=60min, 1 day, 09:00-17:00), `force_recalculate=False` | 1 slot: 09:00-17:00 (only one 8-hour slot fits) |
| **Extended Date Range** | Multi-week range | `meeting_request` (date_range=14 days, work_days_only=True), `force_recalculate=False` | Slots for 10 weekdays (2 weeks) |
| **Availability Variations** | Slots with different availability levels | `meeting_request` (10 participants with varying busy times), `force_recalculate=False` | Slots with different `available_count` values (0-10) |
| **Timezone Handling** | Non-UTC timezone configuration | `meeting_request` (timezone='America/New_York', work_hours=09:00-17:00), `force_recalculate=False` | Slots stored in UTC, correctly converted from EST/EDT |
| **Empty Date Range** | Start date after end date (invalid) | `meeting_request` (date_range_start=2024-01-10, date_range_end=2024-01-05), `force_recalculate=False` | Empty list or validation error |
| **Same Day Range** | Single day date range | `meeting_request` (date_range_start=2024-01-01, date_range_end=2024-01-01), `force_recalculate=False` | Slots for only that single day |
| **Cross-Day Work Hours** | Work hours spanning midnight (edge case) | `meeting_request` (work_hours_start=22:00, work_hours_end=02:00), `force_recalculate=False` | Slots correctly handle day boundary |

---

### Function 4: `get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)`

| Category | Test Case | Input | Expected |
|----------|-----------|-------|----------|
| **Default Parameters** | Get top suggestions with defaults | `meeting_request` (20 slots: 12 above 50%, 8 below 50%), `limit=10`, `min_availability_pct=50` | Top 10 slots with ≥50% availability, sorted by availability desc |
| **All Above Threshold** | All suggestions meet minimum | `meeting_request` (5 slots, all 100% available), `limit=10`, `min_availability_pct=50` | All 5 slots returned (less than limit) |
| **All Below Threshold** | No suggestions meet minimum | `meeting_request` (10 slots, all 0-30% available), `limit=10`, `min_availability_pct=50` | Empty list `[]` |
| **Exact Threshold** | Slots at exact threshold percentage | `meeting_request` (slots at 49%, 50%, 51%), `limit=10`, `min_availability_pct=50` | Only 50% and 51% slots returned (≥ comparison) |
| **Zero Threshold** | Minimum 0% (return all) | `meeting_request` (20 slots with varying availability), `limit=10`, `min_availability_pct=0` | Top 10 slots by availability (all included) |
| **100% Threshold** | Only perfect matches | `meeting_request` (20 slots: 3 at 100%, rest below), `limit=10`, `min_availability_pct=100` | Only 3 slots with 100% availability |
| **Limit = 1** | Single result limit | `meeting_request` (10 slots above 50%), `limit=1`, `min_availability_pct=50` | Single best slot (highest availability) |
| **Limit = 0** | Zero limit edge case | `meeting_request` (10 slots above 50%), `limit=0`, `min_availability_pct=50` | Empty list `[]` |
| **Negative Limit** | Negative limit boundary | `meeting_request` (10 slots), `limit=-5`, `min_availability_pct=50` | Empty list `[]` or all qualifying slots (implementation dependent) |
| **Large Limit** | Limit exceeds available slots | `meeting_request` (5 slots above 50%), `limit=100`, `min_availability_pct=50` | All 5 qualifying slots (limited by available data) |
| **Sorting - Availability** | Multiple slots with same availability | `meeting_request` (3 slots: all 80% available at 09:00, 10:00, 11:00), `limit=10`, `min_availability_pct=50` | All 3 returned, sorted by start_time ascending (secondary sort) |
| **Sorting - Time** | Verify time-based secondary sort | `meeting_request` (slots: 60%@14:00, 80%@10:00, 80%@09:00, 60%@13:00), `limit=10`, `min_availability_pct=50` | Order: 80%@09:00, 80%@10:00, 60%@13:00, 60%@14:00 |
| **No Suggested Slots** | Meeting request with no suggestions | `meeting_request` (no SuggestedSlot objects exist), `limit=10`, `min_availability_pct=50` | Empty list `[]` |
| **Percentage Calculation** | Verify percentage filtering logic | `meeting_request` (10 total participants: slots with 3, 5, 7, 9 available = 30%, 50%, 70%, 90%), `limit=10`, `min_availability_pct=60` | Only 70% and 90% slots returned |
| **Mixed Availability** | Complex availability distribution | `meeting_request` (25 slots: 0%, 20%, 40%, 50%, 60%, 80%, 100% distributed), `limit=5`, `min_availability_pct=50` | Top 5 from ≥50% group (100%, 80%, 60%, 50%) |
| **Rounding Edge Case** | Percentage exactly on boundary due to rounding | `meeting_request` (7 total participants: 3 available = 42.857...%), `limit=10`, `min_availability_pct=43` | Depends on `availability_percentage` rounding (likely excluded if rounds to 42.9) |
| **Decimal Threshold** | Non-integer minimum percentage | `meeting_request` (slots: 49.5%, 50.5%, 51.5%), `limit=10`, `min_availability_pct=50.5` | Only 50.5% and 51.5% slots (precise decimal comparison) |
| **Empty Meeting Request** | Newly created request with no data | `meeting_request` (just created, no participants or slots), `limit=10`, `min_availability_pct=50` | Empty list `[]` |

---

## Test Implementation Notes

### Mocking Strategy
1. **Database Models**: Mock `MeetingRequest`, `Participant`, `BusySlot`, `SuggestedSlot` using Django test utilities or unittest.mock
2. **QuerySets**: Mock `.filter()`, `.exists()`, `.count()`, `.delete()`, `.update_or_create()` operations
3. **Datetime**: Use fixed datetime values with explicit UTC timezone for consistency
4. **Function Dependencies**: Mock `is_participant_available()` when testing `calculate_slot_availability()` and higher-level functions

### Setup Requirements
- Use `pytest` or Django's `TestCase`/`TransactionTestCase`
- Use `freezegun` or similar for consistent datetime testing
- Use `factory_boy` or manual fixture creation for model instances
- All test datetimes should be timezone-aware (UTC)

### Assertions to Verify
- **Return types**: Tuple structure, list contents, boolean values
- **Counts**: Availability counts match expected values
- **Participant IDs**: Correct UUIDs in returned lists
- **Sorting**: Order of results matches specification
- **Database state**: Slots created/updated/deleted as expected
- **Boundary conditions**: Exact time comparisons work correctly

### Coverage Goals
- **Line coverage**: 100% of function logic
- **Branch coverage**: All conditional paths tested
- **Edge cases**: Boundary values, empty states, maximum values
- **Integration**: Function interactions with dependencies

---

## Test Execution Priority

### Phase 1 - Core Logic (High Priority)
- `is_participant_available()` - Foundation for all availability checks
- `calculate_slot_availability()` - Aggregates availability data

### Phase 2 - Slot Generation (Medium Priority)  
- `generate_suggested_slots()` - Core heatmap algorithm
- `generate_time_slots()` - Helper function for slot creation

---

## Traceability Matrix

| Function | Total Test Cases | Categories Covered |
|----------|-----------------|-------------------|
| `is_participant_available()` | 14 | Basic Availability, Conflicts, Partial Overlaps, Containment, Boundaries, Multiple Conflicts, Edge Cases |
| `calculate_slot_availability()` | 11 | No Data, Partial Data, Full Availability, Mixed States, Complex Patterns, Boundaries, Scale Testing |
| `generate_suggested_slots()` | 18 | Initial Generation, Updates, Force Recalculation, Participant States, Date Ranges, Work Days, Step Sizes, Durations, Timezones, Edge Cases |
| `get_top_suggestions()` | 18 | Default Behavior, Thresholds, Limits, Sorting, Empty States, Boundary Values, Percentage Calculations, Complex Distributions |
| **TOTAL** | **61** | **Comprehensive coverage of all scenarios** |

---

*Document Version: 1.0*  
*Created: October 25, 2025*  
*Last Updated: October 25, 2025*
