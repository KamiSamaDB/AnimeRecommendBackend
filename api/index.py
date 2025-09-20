"""
Vercel serverless function entry point for anime recommendation API.
This file adapts the Flask app for Vercel's serverless environment.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # Import the Flask app
    from src.api.app import AnimeRecommendationAPI
    
    # Create the Flask app instance
    api_instance = AnimeRecommendationAPI()
    app = api_instance.app
    
except ImportError as e:
    # Fallback: Create a simple Flask app if imports fail
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "ok",
            "message": "API is running (fallback mode)",
            "error": f"Import error: {str(e)}"
        })
    
    @app.route('/api/recommendations', methods=['POST'])
    def recommendations():
        return jsonify({
            "status": "error",
            "message": "Service temporarily unavailable",
            "error": "Import configuration issue"
        }), 503

# Export for Vercel
application = app

# For local testing
if __name__ == "__main__":
    app.run(debug=True)