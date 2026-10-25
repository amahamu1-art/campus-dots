import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from web import app

# Vercel expects a callable named `app`
