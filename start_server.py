"""
Production-ready startup script for the Anime Recommendation API
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Start the API server"""
    try:
        from api.app import AnimeRecommendationAPI
        
        # Create and configure the API
        api = AnimeRecommendationAPI()
        
        # Configuration for React app integration
        host = '127.0.0.1'  # Use localhost for React development
        port = 5000
        debug = False  # Set to False for stability
        
        print("\n" + "="*60)
        print("🎌 ANIME RECOMMENDATION API - REACT INTEGRATION")
        print("="*60)
        print(f"🚀 Server URL: http://{host}:{port}")
        print(f"🏥 Health Check: http://{host}:{port}/health")
        print(f"🎯 Recommendations: http://{host}:{port}/api/recommendations")
        print(f"🔥 Trending: http://{host}:{port}/api/trending")
        print(f"🔍 Search: http://{host}:{port}/api/anime/search?q=ANIME_NAME")
        print("="*60)
        print("\n📱 REACT INTEGRATION:")
        print("   Use this base URL in your React app:")
        print(f"   const API_BASE_URL = 'http://{host}:{port}';")
        print("\n🛑 Press CTRL+C to stop the server")
        print("="*60)
        
        # Start the server
        api.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return 1

if __name__ == '__main__':
    exit(main())