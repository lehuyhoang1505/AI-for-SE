#!/bin/sh
# Lightweight wrapper to run the project's test suite with correct PYTHONPATH and Django settings.
# Usage:
#   ./run_tests.sh           # run all tests (defaults to `tests`)
#   ./run_tests.sh -q        # pass flags/args through to pytest
#   ./run_tests.sh tests/some_test.py::test_name

set -e

# Prefer the project's venv python if available
if [ -x "$(pwd)/.venv/bin/python" ]; then
  PYTHON_BIN="$(pwd)/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3 || command -v python)"
fi

# Ensure src/ is on PYTHONPATH so `meetings` and `time_mamager` import properly
export PYTHONPATH="$(pwd)/src"
export DJANGO_SETTINGS_MODULE=time_mamager.test_settings

# If no args provided, default to `tests`
if [ "$#" -eq 0 ]; then
  ARGS="tests"
else
  ARGS="$@"
fi

# Run pytest with given args
exec "$PYTHON_BIN" -m pytest $ARGS
