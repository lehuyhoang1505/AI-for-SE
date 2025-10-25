#!/bin/bash

# Test runner script for Time Manager project
# Usage: ./test/run_tests.sh [options]

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Time Manager - Test Suite Runner${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing test dependencies...${NC}"
    pip install -r test/requirements-test.txt
fi

# Parse command line arguments
COVERAGE=false
VERBOSE=false
FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --file|-f)
            FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./test/run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage    Run with coverage report"
            echo "  -v, --verbose     Run in verbose mode"
            echo "  -f, --file FILE   Run specific test file"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./test/run_tests.sh                                    # Run all tests"
            echo "  ./test/run_tests.sh -v                                 # Run with verbose output"
            echo "  ./test/run_tests.sh -c                                 # Run with coverage"
            echo "  ./test/run_tests.sh -f test_is_participant_available.py # Run specific file"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
CMD="pytest"

if [ -n "$FILE" ]; then
    CMD="$CMD test/$FILE"
else
    CMD="$CMD test/"
fi

if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    CMD="$CMD --cov=meetings.utils --cov-report=term-missing --cov-report=html"
fi

# Run the tests
echo -e "${GREEN}Running tests...${NC}\n"
eval $CMD

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo -e "\n${BLUE}Coverage report generated in htmlcov/index.html${NC}"
    fi
else
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Some tests failed. Please review above.${NC}"
    echo -e "${YELLOW}========================================${NC}"
    exit 1
fi
