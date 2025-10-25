# Time Manager - Test Suite

This repo contains comprehensive unit tests for the Time Manager project's **Calculating Overlapping Free Time Slots** feature.

## Test Structure

The tests are organized by function under test:

- **`test_is_participant_available.py`** - Tests for checking individual participant availability (14 test cases)
- **`test_calculate_slot_availability.py`** - Tests for calculating aggregate availability across participants (11 test cases)
- **`test_generate_suggested_slots.py`** - Tests for generating time slot suggestions (18 test cases)
- **`test_get_top_suggestions.py`** - Tests for retrieving top suggestions with filtering (18 test cases)
- **`test_generate_time_slots.py`** - Tests for the time slot generation helper function (8 test cases)
- **`conftest.py`** - Shared pytest fixtures and test utilities

**Total: 69 comprehensive test cases**

## Running the Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r test/requirements-test.txt
```

Or install pytest-django directly:

```bash
pip install pytest pytest-django freezegun pytest-cov
```

### Run All Tests

```bash
pytest test/
```

### Run Specific Test File

README for the Time Manager project (tests-focused)

This README explains how to run the project's tests locally and includes a small wrapper script (`run_tests.sh`) that sets the required environment (PYTHONPATH + Django test settings).

Where tests live
---------------

All tests are located in the top-level `tests/` directory. Application code lives under `src/` (the Django project `time_mamager` and the `meetings` app).

Quick start — run tests locally
-----------------------------

1. (Optional) Create and activate a virtualenv:

```sh
python -m venv .venv
.venv/bin/python -m pip install -U pip
```

2. Install project and test dependencies:

```sh
.venv/bin/python -m pip install -r src/requirements.txt
.venv/bin/python -m pip install -r tests/requirements-test.txt
```

3. Run tests from the repository root (this ensures `src/` is importable and Django test settings are used):

```sh
PYTHONPATH=$(pwd)/src \
	DJANGO_SETTINGS_MODULE=time_mamager.test_settings \
	.venv/bin/python -m pytest tests -q
```

Using the included `run_tests.sh` wrapper
---------------------------------------

A convenience script `run_tests.sh` is provided at the repository root. It:

- prefills `PYTHONPATH` to include `src/`
- sets `DJANGO_SETTINGS_MODULE=time_mamager.test_settings`
- prefers `.venv/bin/python` when present

Make it executable and run it from the repo root:

```sh
chmod +x run_tests.sh
./run_tests.sh            # runs all tests (defaults to `tests`)
./run_tests.sh -q         # pass flags to pytest (quiet)
./run_tests.sh tests/some_test.py::test_name
```

The script will use your venv's Python if `.venv/bin/python` exists; otherwise it will fall back to the system `python`/`python3`.

Troubleshooting
---------------

- ModuleNotFoundError: `meetings`
	- Ensure `PYTHONPATH` includes the `src/` directory (the wrapper script does this).

- django.core.exceptions.ImproperlyConfigured: settings are not configured
	- Set `DJANGO_SETTINGS_MODULE` to `time_mamager.test_settings` before running tests (the wrapper does this).

- ImportError: No module named `pymysql`
	- Install requirements (see step 2). The project calls `pymysql.install_as_MySQLdb()` in `src/time_mamager/__init__.py`.

CI notes
--------

In CI, ensure you set `PYTHONPATH` to include `src/` and `DJANGO_SETTINGS_MODULE=time_mamager.test_settings` before running pytest.

Related files
-------------

- Django test settings: `src/time_mamager/test_settings.py`
- Application code: `src/meetings/`
- Tests: `tests/`

Local test result (this run)
----------------------------

Running the included script in this environment produced: `65 passed in 0.82s`.
