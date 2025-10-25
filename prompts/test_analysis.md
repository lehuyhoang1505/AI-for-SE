## Function Analysis and Test Cases

### 1. `is_participant_available(participant, start_time, end_time)`

**Location:** `meetings/utils.py`

**Main Functionality:**
- Checks if a participant has no conflicting busy slots during the specified time range
- Uses database query with Q objects to find overlapping busy slots
- Returns True if available (no conflicts), False otherwise

**Input Parameters:**
- `participant` (Participant): Participant model instance
- `start_time` (datetime): Start time of the slot to check (UTC, timezone-aware)
- `end_time` (datetime): End time of the slot to check (UTC, timezone-aware)

**Expected Return Values:**
- `True` if participant is available (no overlapping busy slots)
- `False` if participant has one or more overlapping busy slots

**Edge Cases to Test:**
1. Busy slot exactly matching the time range
2. Busy slot partially overlapping
3. Busy slot completely contained within the checking time range
4. Checking time range completely contained within a busy slot
5. Multiple overlapping busy slots
6. Adjacent busy slots (touching but not overlapping)
7. Busy slot ending exactly when checking slot starts (boundary case - should be available)
8. Busy slot starting exactly when checking slot ends (boundary case - should be available)

**Dependencies to Mock:**
- `BusySlot.objects.filter()` - Database query for participant's busy slots
- Database ORM query with Q objects for overlap detection

**Test Considerations:**
- Test the overlap logic: `Q(start_time__lt=end_time) & Q(end_time__gt=start_time)`
- Verify boundary conditions (adjacent slots shouldn't conflict)
- Mock database queries to avoid actual database dependencies

---

### 2. `calculate_slot_availability(meeting_request, start_time, end_time)`

**Location:** `meetings/utils.py`

**Main Functionality:**
- Calculates how many participants are available for a specific time slot
- Returns count of available participants, total participants who responded, and list of available participant IDs
- Only counts participants who have responded

**Input Parameters:**
- `meeting_request` (MeetingRequest): Meeting request instance
- `start_time` (datetime): Start time of the slot (UTC, timezone-aware)
- `end_time` (datetime): End time of the slot (UTC, timezone-aware)

**Expected Return Values:**
- Tuple: `(available_count, total_count, [participant_ids_available])`
- `available_count` (int): Number of participants available
- `total_count` (int): Total number of participants who have responded
- List of UUIDs of available participants
- Example: `(8, 10, [uuid1, uuid2, uuid3, ...])`

**Edge Cases to Test:**
1. No participants have responded (should return `(0, 0, [])`)
2. Some participants available, some not (partial availability)
3. Mix of participants with and without busy slots
4. Participants with multiple overlapping busy slots
5. Meeting request with no participants at all

**Dependencies to Mock:**
- `Participant.objects.filter()` - Database query for responded participants
- `is_participant_available()` - Function dependency (should be tested separately)

**Test Considerations:**
- Only participants with `has_responded=True` should be counted
- Verify participant IDs in returned list match those who are available
- Test with mocked `is_participant_available()` to isolate this function's logic

---

### 3. `generate_suggested_slots(meeting_request, force_recalculate=False)`

**Location:** `meetings/utils.py`

**Main Functionality:**
- Main algorithm that generates all suggested slots with availability calculations
- Creates or updates SuggestedSlot objects in the database
- Optionally clears existing suggestions before recalculating (when `force_recalculate=True`)
- This is the core heatmap generation function

**Input Parameters:**
- `meeting_request` (MeetingRequest): Meeting request instance
- `force_recalculate` (bool): Whether to delete existing suggestions first (default: False)

**Expected Return Values:**
- List of `SuggestedSlot` objects (newly created or updated)
- Each slot contains availability counts and metadata

**Edge Cases to Test:**
1. Regeneration without `force_recalculate` (should update existing slots)
2. Regeneration with `force_recalculate=True` (should delete and recreate all)
3. Meeting request with no participants
4. Meeting request with no responded participants (all slots should have 0 available)
5. Partial responses (some participants responded, some haven't)

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter().delete()` - Database deletion
- `SuggestedSlot.objects.update_or_create()` - Database upsert operation
- `generate_time_slots()` - Function dependency
- `calculate_slot_availability()` - Function dependency

**Test Considerations:**
- Verify correct behavior with and without `force_recalculate`
- Check that all possible slots are generated
- Ensure availability counts are correct for each slot
- Test database operations (create vs update logic)
- Verify returned list contains all expected slots

---

### 4. `get_top_suggestions(meeting_request, limit=10, min_availability_pct=50)`

**Location:** `meetings/utils.py`

**Main Functionality:**
- Retrieves top suggested slots sorted by availability
- Filters by minimum availability percentage
- Limits the number of results returned
- Used to show best meeting time options to the leader

**Input Parameters:**
- `meeting_request` (MeetingRequest): Meeting request instance
- `limit` (int): Maximum number of suggestions to return (default: 10)
- `min_availability_pct` (float): Minimum availability percentage threshold (default: 50)

**Expected Return Values:**
- List of `SuggestedSlot` objects (filtered and limited)
- Sorted by: 1) available_count (descending), 2) start_time (ascending)
- Empty list if no suggestions meet criteria

**Edge Cases to Test:**
1. All suggestions below `min_availability_pct` threshold (should return empty list)
2. Some suggestions above, some below threshold (should filter correctly)
3. `min_availability_pct = 0` (should return all suggestions, limited by count)
4. `min_availability_pct = 100` (should return only perfect matches)
5. `limit = 1` (edge case for single result)
6. `limit = 0` or negative (boundary testing)

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter()` - Database query
- `SuggestedSlot.availability_percentage` - Property calculation (depends on model)

**Test Considerations:**
- Verify sorting order is correct (highest availability first)
- Test filtering logic for minimum percentage
- Ensure limit is applied correctly
- Check behavior with edge values for limit and min_availability_pct
