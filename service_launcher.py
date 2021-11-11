"""
Service launcher to use Flask without wsgi.py
"""
from app import app  # pylint: disable=unused-import
from app.helpers.utils import init_logging

#initialize logging using JSON as a format.
init_logging()
