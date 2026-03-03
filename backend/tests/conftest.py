"""
Pytest conftest — set test DB before app import.
"""
import os
import tempfile

# Set test DB path before app is imported
if "ENGAGEFLOW_DB_PATH" not in os.environ:
    _fd, _path = tempfile.mkstemp(suffix=".db")
    os.close(_fd)
    os.environ["ENGAGEFLOW_DB_PATH"] = _path


# Seed helpers moved to tests/helpers.py
