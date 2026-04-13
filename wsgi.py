"""
WSGI config for EduMind AI project on Fly.io.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys

# Set the path to your app directory
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

from app import create_app

# Create the Flask application
application = create_app('production')

# Alias for gunicorn
app = application

# For debugging (change to False in production)
application.debug = False
