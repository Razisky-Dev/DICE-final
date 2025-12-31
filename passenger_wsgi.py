import sys
import os

# Add the project directory to the sys.path
project_home = u'/home/u123456789/domains/yourdomain.com/public_html/flask_app' # ADJUST THIS PATH
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from app import app as application
