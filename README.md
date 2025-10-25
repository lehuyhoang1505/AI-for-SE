# README for the Time Manager project (tests-focused)

Project Readme: [README.md](src/README.md)

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
- Project README: [README.md](src/README.md)
- Tests: `tests/`
- Slide: [Slide Canva](https://www.canva.com/design/DAG2nlsFR1k/soonJh0gIRisxeUub7zJuw/edit)

