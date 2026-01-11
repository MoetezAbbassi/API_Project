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
    
    # Enable CORS FIRST
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Serve frontend files - AFTER blueprint registration
    @app.route('/')
    def index():
        """Serve login/register page"""
        try:
            with open(os.path.join('frontend', 'index.html'), 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
        except FileNotFoundError:
            return "Frontend files not found. Make sure 'frontend' folder exists.", 404
    
    @app.route('/app')
    def app_page():
        """Serve main app page"""
        try:
            with open(os.path.join('frontend', 'app.html'), 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
        except FileNotFoundError:
            return "app.html not found", 404
    
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """Serve CSS files"""
        if '..' in filename or filename.startswith('/'):
            return "Invalid file path", 403
        
        filepath = os.path.join('frontend', 'css', filename)
        if not os.path.exists(filepath):
            return f"File not found: {filename}", 404
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'text/css; charset=utf-8'}
        except:
            return "Error reading CSS file", 500
    
    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """Serve JavaScript files"""
        if '..' in filename or filename.startswith('/'):
            return "Invalid file path", 403
        
        filepath = os.path.join('frontend', 'js', filename)
        if not os.path.exists(filepath):
            return f"File not found: {filename}", 404
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read(), 200, {'Content-Type': 'application/javascript; charset=utf-8'}
        except:
            return "Error reading JS file", 500
    
    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        """Serve uploaded files"""
        if '..' in filename or filename.startswith('/'):
            return "Invalid file path", 403
        
        filepath = os.path.join('uploads', filename)
        if not os.path.exists(filepath):
            return f"File not found: {filename}", 404
        
        try:
            with open(filepath, 'rb') as f:
                ext = filename.split('.')[-1].lower()
                content_types = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                return f.read(), 200, {'Content-Type': content_type}
        except:
            return "Error reading file", 500
    
    # Get configuration
    port = int(os.getenv('FLASK_PORT', 5000))
    flask_env = os.getenv('FLASK_ENV', 'development')
    debug = flask_env == 'development'
    
    # Print startup message
    print("\n" + "="*60)
    print("🏋️  Fitness API Server Starting")
    print("="*60)
    print(f"Environment: {flask_env}")
    print(f"Debug Mode: {debug}")
    print(f"Frontend URL: http://localhost:{port}")
    print(f"App URL: http://localhost:{port}/app")
    print(f"API URL: http://localhost:{port}/api")
    print(f"Health Check: http://localhost:{port}/api/health")
    print("="*60 + "\n")
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )
