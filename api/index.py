import sys
import os

# Add the parent directory to sys.path so the Vercel serverless function can
# import modules from the main backend app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app
