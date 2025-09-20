"""
Vercel serverless function entry point for anime recommendation API.
This file adapts the Flask app for Vercel's serverless environment.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the Flask app
from src.api.app import AnimeRecommendationAPI

# Create the Flask app instance
api_instance = AnimeRecommendationAPI()
app = api_instance.app

# This is the handler function that Vercel calls
def handler(request):
    """
    Vercel serverless function handler.
    This function will be called for each HTTP request.
    """
    return app(request.environ, lambda status, headers: None)

# For Vercel, we need to export the app
# Vercel looks for either 'app' or a function as the default export
if __name__ == "__main__":
    # This allows local testing
    app.run(debug=True)
else:
    # This is the export for Vercel
    application = app