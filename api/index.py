"""
Vercel serverless function entry point for anime recommendation API.
Self-contained implementation with direct MAL API integration.
"""
import sys
import os
from pathlib import Path
import requests
import time
import json
from typing import List, Dict, Any

from flask import Flask, jsonify, request
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)

# CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        "expose_headers": ["Content-Type", "X-Total-Count"],
        "supports_credentials": False,
        "max_age": 86400
    }
})

class SimpleMALService:
    """Simplified MAL service for Vercel deployment."""
    
    def __init__(self):
        self.base_url = "https://api.jikan.moe/v4"
        self.request_delay = 1.0  # Rate limiting
        self.last_request_time = 0
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make rate-limited request to Jikan API."""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=10)
            self.last_request_time = time.time()
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"MAL API error: {e}")
            return {"data": []}
    
    def get_anime_by_id(self, anime_id: int) -> Dict:
        """Get anime details by MAL ID."""
        return self._make_request(f"anime/{anime_id}")
    
    def search_anime(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for anime by title."""
        params = {"q": query, "limit": min(limit, 25)}
        result = self._make_request("anime", params)
        return result.get("data", [])
    
    def get_top_anime(self, limit: int = 10) -> List[Dict]:
        """Get top rated anime."""
        params = {"limit": min(limit, 25)}
        result = self._make_request("top/anime", params)
        return result.get("data", [])

class SimpleRecommendationEngine:
    """Simplified recommendation engine."""
    
    def __init__(self, mal_service: SimpleMALService):
        self.mal_service = mal_service
        self.anime_cache = {}
    
    def get_anime_details(self, anime_id: int) -> Dict:
        """Get cached anime details."""
        if anime_id not in self.anime_cache:
            result = self.mal_service.get_anime_by_id(anime_id)
            if result.get("data"):
                self.anime_cache[anime_id] = result["data"]
            else:
                return None
        return self.anime_cache.get(anime_id)
    
    def get_recommendations(self, user_anime_list: List[int], max_recommendations: int = 10) -> List[Dict]:
        """Generate recommendations based on user's anime list."""
        recommendations = []
        
        # Get user's anime details to understand preferences
        user_genres = set()
        user_scores = []
        
        for anime_id in user_anime_list[:5]:  # Limit to first 5 for efficiency
            anime_data = self.get_anime_details(anime_id)
            if anime_data:
                # Extract genres
                for genre in anime_data.get("genres", []):
                    user_genres.add(genre.get("name"))
                # Get score
                score = anime_data.get("score")
                if score:
                    user_scores.append(score)
        
        # Get top anime and filter/score them
        top_anime = self.mal_service.get_top_anime(limit=50)
        
        for anime in top_anime:
            anime_id = anime.get("mal_id")
            if anime_id in user_anime_list:
                continue
            
            # Calculate similarity score
            similarity_score = 0.5  # Base score
            
            # Genre similarity
            anime_genres = {genre.get("name") for genre in anime.get("genres", [])}
            genre_overlap = len(user_genres.intersection(anime_genres))
            if genre_overlap > 0:
                similarity_score += min(0.4, genre_overlap * 0.1)
            
            # Score similarity
            anime_score = anime.get("score", 0)
            if user_scores and anime_score:
                avg_user_score = sum(user_scores) / len(user_scores)
                score_diff = abs(anime_score - avg_user_score)
                if score_diff < 1.0:
                    similarity_score += 0.2
                elif score_diff < 2.0:
                    similarity_score += 0.1
            
            recommendations.append({
                "mal_id": anime_id,
                "title": anime.get("title", "Unknown"),
                "score": anime_score,
                "genres": [g.get("name") for g in anime.get("genres", [])],
                "year": anime.get("year"),
                "similarity_score": round(similarity_score, 2),
                "reason": f"Similar genres and high rating" if genre_overlap > 0 else "Highly rated anime",
                "image_url": anime.get("images", {}).get("jpg", {}).get("image_url"),
                "synopsis": anime.get("synopsis", "")[:200] + "..." if anime.get("synopsis") else "",
                "rank": anime.get("rank"),
                "popularity": anime.get("popularity"),
                "members": anime.get("members"),
                "favorites": anime.get("favorites"),
                "scored_by": anime.get("scored_by"),
                "status": anime.get("status"),
                "episodes": anime.get("episodes"),
                "duration": anime.get("duration"),
                "rating": anime.get("rating"),
                "source": anime.get("source"),
                "studios": [studio.get("name") for studio in anime.get("studios", [])],
                "aired": anime.get("aired", {}).get("string")
            })
        
        # Sort by similarity score and return top results
        recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
        return recommendations[:max_recommendations]

# Initialize services
try:
    mal_service = SimpleMALService()
    recommendation_engine = SimpleRecommendationEngine(mal_service)
    SERVICES_AVAILABLE = True
    IMPORT_ERROR = None
except Exception as e:
    print(f"Service initialization error: {e}")
    mal_service = None
    recommendation_engine = None
    SERVICES_AVAILABLE = False
    IMPORT_ERROR = str(e)

@app.route('/')
def root():
    return jsonify({
        "status": "ok",
        "message": "Anime Recommendation API with MAL integration",
        "version": "2.0.0",
        "services_available": SERVICES_AVAILABLE,
        "endpoints": ["/health", "/api/recommendations", "/api/search", "/api/trending"]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "message": "API is healthy and running with direct MAL integration",
        "service": "anime-recommendation-api",
        "mal_service": "available" if SERVICES_AVAILABLE else "unavailable",
        "import_error": IMPORT_ERROR if not SERVICES_AVAILABLE else None
    })

@app.route('/api/recommendations', methods=['POST', 'OPTIONS'])
def recommendations():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not SERVICES_AVAILABLE:
        return jsonify({
            "status": "error",
            "message": "MAL services unavailable",
            "error": IMPORT_ERROR
        }), 503
    
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body must be valid JSON"
            }), 400
        
        # Extract parameters
        user_anime_list = data.get('user_anime_list', [])
        max_recommendations = min(data.get('max_recommendations', 10), 25)  # Limit to 25
        
        # Validate input
        if not isinstance(user_anime_list, list):
            return jsonify({
                "status": "error",
                "message": "user_anime_list must be a list of anime IDs"
            }), 400
        
        if not user_anime_list:
            return jsonify({
                "status": "error", 
                "message": "user_anime_list cannot be empty"
            }), 400
        
        # Get recommendations using the recommendation engine
        start_time = time.time()
        recommendations_list = recommendation_engine.get_recommendations(
            user_anime_list=user_anime_list,
            max_recommendations=max_recommendations
        )
        processing_time = round(time.time() - start_time, 2)
        
        # Format response
        return jsonify({
            "status": "success",
            "recommendations": recommendations_list,
            "total_found": len(recommendations_list),
            "input_anime_count": len(user_anime_list),
            "processing_time": processing_time,
            "algorithm": "Simple Similarity Algorithm with real MAL data"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error processing recommendations: {str(e)}",
            "error_type": type(e).__name__
        }), 500

@app.route('/api/search')
def search():
    if not SERVICES_AVAILABLE:
        return jsonify({
            "status": "error",
            "message": "MAL services unavailable"
        }), 503
    
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 25)  # Limit to 25
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query parameter 'q' is required"
        }), 400
    
    try:
        # Search using MAL service
        search_results = mal_service.search_anime(query, limit=limit)
        
        # Format results
        formatted_results = []
        for anime in search_results:
            formatted_results.append({
                "mal_id": anime.get("mal_id"),
                "title": anime.get("title"),
                "score": anime.get("score"),
                "year": anime.get("year"),
                "genres": [g.get("name") for g in anime.get("genres", [])],
                "image_url": anime.get("images", {}).get("jpg", {}).get("image_url"),
                "synopsis": anime.get("synopsis", "")[:200] + "..." if anime.get("synopsis") else "",
                "rank": anime.get("rank"),
                "popularity": anime.get("popularity"),
                "members": anime.get("members"),
                "favorites": anime.get("favorites"),
                "scored_by": anime.get("scored_by"),
                "status": anime.get("status"),
                "episodes": anime.get("episodes"),
                "duration": anime.get("duration"),
                "rating": anime.get("rating"),
                "source": anime.get("source"),
                "studios": [studio.get("name") for studio in anime.get("studios", [])],
                "aired": anime.get("aired", {}).get("string")
            })
        
        return jsonify({
            "status": "success",
            "results": formatted_results,
            "query": query,
            "total_results": len(formatted_results),
            "limit": limit
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Search error: {str(e)}",
            "error_type": type(e).__name__
        }), 500

@app.route('/api/trending')
def trending():
    if not SERVICES_AVAILABLE:
        return jsonify({
            "status": "error",
            "message": "MAL services unavailable"
        }), 503
    
    limit = min(int(request.args.get('limit', 10)), 25)
    
    try:
        # Get trending anime from MAL
        trending_anime = mal_service.get_top_anime(limit=limit)
        
        # Format results
        formatted_results = []
        for anime in trending_anime:
            formatted_results.append({
                "mal_id": anime.get("mal_id"),
                "title": anime.get("title"),
                "score": anime.get("score"),
                "year": anime.get("year"),
                "genres": [g.get("name") for g in anime.get("genres", [])],
                "image_url": anime.get("images", {}).get("jpg", {}).get("image_url"),
                "synopsis": anime.get("synopsis", "")[:200] + "..." if anime.get("synopsis") else "",
                "rank": anime.get("rank"),
                "popularity": anime.get("popularity"),
                "members": anime.get("members"),
                "favorites": anime.get("favorites"),
                "scored_by": anime.get("scored_by"),
                "status": anime.get("status"),
                "episodes": anime.get("episodes"),
                "duration": anime.get("duration"),
                "rating": anime.get("rating"),
                "source": anime.get("source"),
                "studios": [studio.get("name") for studio in anime.get("studios", [])],
                "aired": anime.get("aired", {}).get("string")
            })
        
        return jsonify({
            "status": "success",
            "trending": formatted_results,
            "total_results": len(formatted_results),
            "limit": limit
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error fetching trending anime: {str(e)}",
            "error_type": type(e).__name__
        }), 500

# Export the app for Vercel
application = app

if __name__ == "__main__":
    app.run(debug=True)