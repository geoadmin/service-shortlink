"""
Service launcher to use Flask without wsgi.py
"""
from app import app  # pylint: disable=unused-import
from app.helpers import init_logging

#initialize logging using JSON as a format.
init_logging()
