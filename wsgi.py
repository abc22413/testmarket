"""
WSGI entry point for production deployment with Gunicorn.
Usage: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import app, db

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

if __name__ == '__main__':
    app.run()
