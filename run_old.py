"""
Main entry point to run the Flask application
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import create_app
from flask_cors import CORS

if __name__ == '__main__':
    app = create_app()
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Serve frontend files
    @app.route('/')
    def index():
        with open(os.path.join('frontend', 'index.html'), 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    
    @app.route('/app')
    def app_page():
        with open(os.path.join('frontend', 'app.html'), 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        if '..' in filename or filename.startswith('/'):
            return "Invalid file path", 403
        
        filepath = os.path.join('frontend', filename)
        if not os.path.exists(filepath):
            return f"File not found: {filename}", 404
        
        if filename.endswith('.css'):
            with open(filepath, 'r') as f:
                return f.read(), 200, {'Content-Type': 'text/css'}
        elif filename.endswith('.js'):
            with open(filepath, 'r') as f:
                return f.read(), 200, {'Content-Type': 'application/javascript'}
        elif filename.endswith('.html'):
            with open(filepath, 'r') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
        return "Unsupported file type", 400
    
    port = int(os.getenv('FLASK_PORT', 5000))
    flask_env = os.getenv('FLASK_ENV', 'development')
    debug = flask_env == 'development'
    
    print("\n" + "="*60)
    print("🏋️  Fitness API Server Starting")
    print("="*60)
    print(f"Environment: {flask_env}")
    print(f"Frontend URL: http://localhost:{port}")
    print(f"App URL: http://localhost:{port}/app")
    print(f"API URL: http://localhost:{port}/api")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=debug)
