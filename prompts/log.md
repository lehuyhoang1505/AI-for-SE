# 1. Phân tích

CORE FEATURE: Tính toán các khoảng thời gian rảnh

### Promt:
```
Analyze this Project's `Calculating overlapping free time slots` feature and identify all functions that need unit testing:

For each function, identify:
1. Main functionality
2. Input parameters and types
3. Expected return values
4. Potential edge cases
5. Dependencies that need mocking
Output into an md file, called `test_analystic.md`
```
OUTPUT: [test_analysis.md](test_analysis.md)

# 2. Thiết kế test case:

### Promt:
```
Generate comprehensive unit test cases for this Project's `Calculating overlapping free time slots` feature based on this `test_analysis.md` document. Output in a table with these columns `Category,Test Case, Input, Expected` and save into `test/test_design.md`
```
OUTPUT: [test_design.md](test_design.md)

# 3. Sinh Test Code
Promt: 
```
Based on this document `test/test_design.md`, Create pytest unit tests for this Project's `Calculating overlapping free time slots` feature. save all test in `test` folder
```

# 4. Chạy & Debug Tests
- Chạy lệnh: `run_test.sh`
=> lỗi: `ModuleNotFoundError: No module named 'pytests'`

Promt: 
```
Help me fix this error while run unit test:
`ModuleNotFoundError: No module named 'pytests'`
```

# 5. Tối ưu & Mocking
Promt:
```
Looking into `tests/*.py`, check if the test is optimized and show what to optimize if needed. Then output to `prompts/optimize.md
```
OUTPUT: [optimize.md](optimize.md)

