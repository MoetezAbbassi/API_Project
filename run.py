"""
Main entry point to run the Flask application using Waitress WSGI server
Waitress is a pure-Python WSGI server that works better on Windows than Flask's dev server
"""
import os
import sys
from dotenv import load_dotenv
from waitress import serve

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import create_app

# Create app at module level so Gunicorn can find it
app = create_app()

if __name__ == '__main__':
    
    port = int(os.getenv('FLASK_PORT', 5000))
    flask_env = os.getenv('FLASK_ENV', 'development')
    
    print("\n" + "="*60)
    print("[SERVER] Fitness API Server Starting")
    print("="*60)
    print(f"Environment: {flask_env}")
    print(f"Frontend URL: http://localhost:{port}")
    print(f"App URL: http://localhost:{port}/app")
    print(f"API URL: http://localhost:{port}/api")
    print(f"Health Check: http://localhost:{port}/api/health")
    print("="*60 + "\n")
    
    # Run production WSGI server
    # Waitress is much more stable than Flask's development server
    serve(app, host='0.0.0.0', port=port, threads=4)
