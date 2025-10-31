"""
WSGI entrypoint for the Anime Recommendation System.

This module exposes a top-level ``app`` variable compatible with WSGI servers
like waitress or gunicorn. You can run it on EC2 with:

    waitress-serve --listen=0.0.0.0:5000 src.app:app

It also retains a CLI-friendly ``main()`` for local development.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir
sys.path.insert(0, str(src_dir))

from api.app import AnimeRecommendationAPI

# Create the API instance once at import time and expose the Flask app
_api = AnimeRecommendationAPI()
app = _api.app

def main():
    """Main application entry point"""
    # Use the already created WSGI app instance
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("=" * 50)
    print("🎌 Anime Recommendation System API")
    print("=" * 50)
    print(f"Server: http://{host}:{port}")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"Recommendations: http://{host}:{port}/api/recommendations")
    print(f"Trending: http://{host}:{port}/api/trending")
    print("=" * 50)
    
    _api.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()