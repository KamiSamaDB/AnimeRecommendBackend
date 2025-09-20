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
        """Generate recommendations based on user's anime list using comprehensive scoring."""
        recommendations = []
        seen_anime_ids = set()
        
        # Get user's anime details to understand preferences
        user_genres = {}  # Genre -> count
        user_scores = []
        user_popularity_scores = []
        user_studios = {}  # Studio -> count
        
        print(f"Analyzing user preferences from {len(user_anime_list)} anime...")
        
        for anime_id in user_anime_list[:10]:  # Analyze up to 10 user anime
            anime_data = self.get_anime_details(anime_id)
            if anime_data:
                # Extract genres with weights
                for genre in anime_data.get("genres", []):
                    genre_name = genre.get("name")
                    user_genres[genre_name] = user_genres.get(genre_name, 0) + 1
                
                # Get score preference
                score = anime_data.get("score")
                if score and score > 0:
                    user_scores.append(score)
                
                # Get popularity preference (inverse of popularity rank - lower rank = more popular)
                popularity = anime_data.get("popularity")
                if popularity:
                    user_popularity_scores.append(1.0 / popularity if popularity > 0 else 0)
                
                # Track preferred studios
                for studio in anime_data.get("studios", []):
                    studio_name = studio.get("name")
                    user_studios[studio_name] = user_studios.get(studio_name, 0) + 1
        
        # Calculate user preferences
        avg_user_score = sum(user_scores) / len(user_scores) if user_scores else 7.0
        avg_user_popularity = sum(user_popularity_scores) / len(user_popularity_scores) if user_popularity_scores else 0.001
        top_user_genres = sorted(user_genres.items(), key=lambda x: x[1], reverse=True)[:5]
        top_user_studios = sorted(user_studios.items(), key=lambda x: x[1], reverse=True)[:3]
        
        print(f"User preferences - Avg Score: {avg_user_score:.2f}, Top Genres: {[g[0] for g in top_user_genres[:3]]}")
        
        # Gather candidate anime with user-focused approach
        candidate_pools = []
        
        # 1. Genre-focused search (primary source - 60% of candidates)
        genre_candidates = []
        for genre_name, count in top_user_genres[:3]:  # Top 3 user genres
            try:
                # Multiple search approaches for each genre
                search_terms = [
                    f"{genre_name} anime",
                    f"best {genre_name} anime",
                    f"{genre_name.lower()}"
                ]
                for term in search_terms:
                    genre_results = self.mal_service.search_anime(term, limit=8)
                    genre_candidates.extend(genre_results)
            except Exception as e:
                print(f"Error searching for genre {genre_name}: {e}")
                continue
        candidate_pools.extend(genre_candidates)
        
        # 2. Studio-based recommendations if user has clear preferences
        studio_candidates = []
        for studio_name, count in top_user_studios[:2]:
            if count >= 2:  # Only if user has multiple anime from this studio
                try:
                    studio_results = self.mal_service.search_anime(f"{studio_name}", limit=6)
                    studio_candidates.extend(studio_results)
                except Exception as e:
                    print(f"Error searching for studio {studio_name}: {e}")
        candidate_pools.extend(studio_candidates)
        
        # 3. Score-range targeted search (20% of candidates)
        try:
            if avg_user_score >= 8.5:
                score_results = self.mal_service.get_top_anime(limit=12)
            elif avg_user_score >= 7.5:
                score_results = self.mal_service.search_anime("popular anime", limit=12)
            else:
                score_results = self.mal_service.search_anime("good anime", limit=12)
            candidate_pools.extend(score_results)
        except Exception as e:
            print(f"Error in score-targeted search: {e}")
        
        # 4. Diversity searches (20% of candidates) - only if we have enough genre matches
        if len(genre_candidates) < 30:  # Only add variety if genre search was limited
            try:
                variety_searches = [
                    ("underrated anime", 6),
                    ("hidden gems", 6), 
                    ("recent anime", 6)
                ]
                for search_term, limit in variety_searches:
                    variety_results = self.mal_service.search_anime(search_term, limit=limit)
                    candidate_pools.extend(variety_results)
            except Exception as e:
                print(f"Error in variety search: {e}")
        
        # Remove duplicates while preserving order
        seen_ids = set()
        unique_candidates = []
        for anime in candidate_pools:
            anime_id = anime.get("mal_id")
            if anime_id and anime_id not in seen_ids:
                unique_candidates.append(anime)
                seen_ids.add(anime_id)
        
        # Process all candidates
        print(f"Processing {len(unique_candidates)} unique candidate anime...")
        
        for anime in unique_candidates:
            anime_id = anime.get("mal_id")
            if not anime_id or anime_id in user_anime_list or anime_id in seen_anime_ids:
                continue
            
            seen_anime_ids.add(anime_id)
            
            # Calculate comprehensive similarity score
            try:
                similarity_score = self.calculate_similarity_score(
                    anime, user_genres, user_scores, user_popularity_scores, user_studios,
                    avg_user_score, avg_user_popularity
                )
            except Exception as e:
                print(f"Error calculating similarity for {anime.get('title', 'Unknown')}: {e}")
                similarity_score = 0.1  # Default low score
            
            # More flexible filtering - adjust thresholds for better results
            anime_genres = {genre.get("name", "") for genre in anime.get("genres", []) if genre.get("name")}
            has_genre_match = bool(anime_genres.intersection(set(user_genres.keys())))
            
            # Adjusted thresholds to prevent empty results
            if has_genre_match:
                min_similarity = 0.25  # Lowered from 0.3
            else:
                min_similarity = 0.45  # Lowered from 0.6
            
            if similarity_score >= min_similarity:
                # Check for NSFW content and filter it out
                rating = anime.get("rating", "")
                is_nsfw = self.is_nsfw_content(anime)
                
                if is_nsfw:
                    print(f"Filtered NSFW content: {anime.get('title', 'Unknown')} (Rating: {rating})")
                    continue  # Skip this anime
                
                # Generate recommendation reason
                try:
                    reason = self.generate_recommendation_reason(
                        anime, user_genres, top_user_genres, top_user_studios, similarity_score
                    )
                except Exception as e:
                    print(f"Error generating reason for {anime.get('title', 'Unknown')}: {e}")
                    reason = "Recommended based on your preferences"
                
                recommendations.append({
                    "mal_id": anime_id,
                    "title": anime.get("title", "Unknown"),
                    "score": anime.get("score", 0),
                    "genres": [g.get("name") for g in anime.get("genres", [])],
                    "year": anime.get("year"),
                    "similarity_score": round(similarity_score, 3),
                    "reason": reason,
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
        
        # Sort by similarity score and return diverse results
        recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Ensure diversity by limiting same genre/studio recommendations
        final_recommendations = self.ensure_diversity(recommendations, max_recommendations)
        
        print(f"Generated {len(final_recommendations)} recommendations")
        return final_recommendations
    
    def calculate_similarity_score(self, anime, user_genres, user_scores, user_popularity_scores, 
                                 user_studios, avg_user_score, avg_user_popularity):
        """Calculate comprehensive similarity score for an anime."""
        try:
            score = 0.0
            
            # 1. Genre similarity (60% weight - increased for more focus)
            anime_genres = {genre.get("name", "") for genre in anime.get("genres", []) if genre.get("name")}
            genre_score = 0.0
            total_user_genre_count = sum(user_genres.values()) if user_genres else 1
            
            # Calculate genre overlap score
            genre_overlap_count = len(anime_genres.intersection(set(user_genres.keys())))
            
            if genre_overlap_count > 0:
                # Base score from genre weights
                for genre_name in anime_genres:
                    if genre_name in user_genres:
                        genre_weight = user_genres[genre_name] / total_user_genre_count
                        genre_score += genre_weight
                
                # Bonus for multiple genre matches (stronger preference alignment)
                if genre_overlap_count >= 2:
                    genre_score += 0.3
                elif genre_overlap_count >= 3:
                    genre_score += 0.5
            else:
                # Heavy penalty for no genre matches
                genre_score = 0.0
            
            score += min(genre_score, 1.0) * 0.6
            
            # 2. Rating similarity (15% weight - reduced) 
            anime_score = anime.get("score", 0)
            if anime_score and anime_score > 0 and avg_user_score > 0:
                score_diff = abs(anime_score - avg_user_score)
                if score_diff <= 0.5:
                    score += 0.15
                elif score_diff <= 1.0:
                    score += 0.12
                elif score_diff <= 1.5:
                    score += 0.09
                elif score_diff <= 2.0:
                    score += 0.06
                # Slight bonus for decent anime even if score doesn't match perfectly
                elif anime_score >= 7.0 and genre_overlap_count > 0:
                    score += 0.03
            
            # 3. Popularity balance (15% weight)
            anime_popularity = anime.get("popularity", 999999)
            if anime_popularity and anime_popularity > 0:
                anime_pop_score = 1.0 / anime_popularity
                if avg_user_popularity > 0:
                    pop_ratio = min(anime_pop_score / avg_user_popularity, avg_user_popularity / anime_pop_score)
                    score += pop_ratio * 0.10
                else:
                    # Balanced approach to popularity
                    if anime_popularity <= 1000:
                        score += 0.08
                    elif anime_popularity <= 5000:
                        score += 0.06
                    elif anime_popularity <= 10000:
                        score += 0.04
            
            # 4. Studio preference (10% weight)
            anime_studios = {studio.get("name", "") for studio in anime.get("studios", []) if studio.get("name")}
            for studio_name in anime_studios:
                if studio_name in user_studios:
                    studio_weight = user_studios[studio_name] / len(user_studios) if user_studios else 0
                    score += studio_weight * 0.10
                    break  # Only count one studio match
            
            # 5. Quality and diversity bonus (5% weight - adjusted)
            members = anime.get("members", 0)
            if members and members > 50000:  # Lowered threshold from 100k to 50k
                score += 0.02
            if anime_score and anime_score >= 7.5:  # Lowered threshold from 8.0 to 7.5
                score += 0.02
            # Small bonus for less popular but decent anime
            if anime_popularity and 1000 < anime_popularity <= 10000 and anime_score and anime_score >= 7.0:
                score += 0.01  # Hidden gem bonus
            
            return min(score, 1.0)  # Cap at 1.0
        except Exception as e:
            print(f"Error in similarity calculation: {e}")
            return 0.1  # Default low score
    
    def generate_recommendation_reason(self, anime, user_genres, top_user_genres, top_user_studios, similarity_score):
        """Generate a meaningful reason for the recommendation."""
        try:
            reasons = []
            
            anime_genres = {genre.get("name", "") for genre in anime.get("genres", []) if genre.get("name")}
            anime_studios = {studio.get("name", "") for studio in anime.get("studios", []) if studio.get("name")}
            
            # Check genre matches
            genre_matches = []
            for genre_name, count in (top_user_genres or [])[:3]:
                if genre_name in anime_genres:
                    genre_matches.append(genre_name)
            
            if genre_matches:
                if len(genre_matches) == 1:
                    reasons.append(f"Similar {genre_matches[0]} genre")
                else:
                    reasons.append(f"Shares {', '.join(genre_matches[:2])} genres")
            
            # Check studio matches
            for studio_name, count in (top_user_studios or [])[:2]:
                if studio_name in anime_studios:
                    reasons.append(f"From {studio_name} studio")
                    break
            
            # Check rating
            anime_score = anime.get("score", 0)
            if anime_score and anime_score >= 8.5:
                reasons.append("Highly rated")
            elif anime_score and anime_score >= 8.0:
                reasons.append("Well rated")
            
            # Check popularity
            popularity = anime.get("popularity", 999999)
            if popularity and popularity <= 100:
                reasons.append("Very popular")
            elif popularity and popularity <= 500:
                reasons.append("Popular choice")
            
            return " • ".join(reasons) if reasons else "Recommended based on your preferences"
        except Exception as e:
            print(f"Error generating reason: {e}")
            return "Recommended based on your preferences"
    
    def ensure_diversity(self, recommendations, max_recommendations):
        """Ensure diversity in final recommendations."""
        if len(recommendations) <= max_recommendations:
            return recommendations
        
        final_recs = []
        used_genres = set()
        used_studios = set()
        
        # First pass: Take top recommendations ensuring genre/studio diversity
        for rec in recommendations:
            if len(final_recs) >= max_recommendations:
                break
            
            rec_genres = set(rec["genres"])
            rec_studios = set(rec["studios"])
            
            # Check if this adds new genres or studios
            adds_genre_diversity = bool(rec_genres - used_genres)
            adds_studio_diversity = bool(rec_studios - used_studios)
            
            if len(final_recs) < max_recommendations // 2 or adds_genre_diversity or adds_studio_diversity:
                final_recs.append(rec)
                used_genres.update(rec_genres)
                used_studios.update(rec_studios)
        
        # Second pass: Fill remaining slots with highest scored
        remaining_slots = max_recommendations - len(final_recs)
        if remaining_slots > 0:
            remaining_recs = [r for r in recommendations if r not in final_recs]
            final_recs.extend(remaining_recs[:remaining_slots])
        
        return final_recs
    
    def is_nsfw_content(self, anime):
        """Check if anime contains NSFW content based on rating and genres."""
        try:
            # Check rating for NSFW indicators
            rating = anime.get("rating", "").lower()
            nsfw_ratings = [
                "r+",           # Mild Nudity
                "rx",           # Hentai 
                "hentai",       # Explicit
                "18+",          # Adult
                "mature"        # Mature content
            ]
            
            # Check if any NSFW rating is present
            if any(nsfw_rating in rating for nsfw_rating in nsfw_ratings):
                return True
            
            # Check genres for NSFW content
            genres = [genre.get("name", "").lower() for genre in anime.get("genres", [])]
            nsfw_genres = [
                "hentai",
                "ecchi",        # Might be borderline but often NSFW
                "yaoi",         # Adult BL content
                "yuri"          # Adult GL content (some might be SFW but safer to filter)
            ]
            
            # Check if any NSFW genre is present
            if any(nsfw_genre in " ".join(genres) for nsfw_genre in nsfw_genres):
                return True
            
            # Check title for obvious NSFW indicators (as a last resort)
            title = anime.get("title", "").lower()
            nsfw_title_indicators = [
                "hentai",
                "ecchi",
                "18+",
                "adult"
            ]
            
            if any(indicator in title for indicator in nsfw_title_indicators):
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking NSFW status for {anime.get('title', 'Unknown')}: {e}")
            # If we can't determine, err on the side of caution for unknown content
            return False

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
        
        # Format results with NSFW filtering
        formatted_results = []
        for anime in search_results:
            # Filter out NSFW content
            if recommendation_engine and recommendation_engine.is_nsfw_content(anime):
                continue
                
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
        
        # Format results with NSFW filtering
        formatted_results = []
        for anime in trending_anime:
            # Filter out NSFW content
            if recommendation_engine and recommendation_engine.is_nsfw_content(anime):
                continue
                
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