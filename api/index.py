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

# CORS configuration - Enhanced for React compatibility
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "X-Api-Key"],
        "expose_headers": ["Content-Type", "X-Total-Count", "X-Processing-Time"],
        "supports_credentials": False,
        "max_age": 600
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
        """Generate truly unique recommendations based on specific user input combination."""
        print(f"Generating unique recommendations for {len(user_anime_list)} anime...")
        
        # Step 1: Analyze user's anime to build unique taste profile
        user_profile = {
            'genres': {},
            'studios': {},
            'avg_score': 0,
            'anime_titles': []
        }
        
        user_anime_data = []
        for anime_id in user_anime_list:
            anime_data = self.get_anime_details(anime_id)
            if anime_data:
                user_anime_data.append(anime_data)
                user_profile['anime_titles'].append(anime_data.get('title', ''))
                
                # Count genre frequencies
                for genre in anime_data.get("genres", []):
                    genre_name = genre.get("name")
                    if genre_name:
                        user_profile['genres'][genre_name] = user_profile['genres'].get(genre_name, 0) + 1
                
                # Count studio frequencies
                for studio in anime_data.get("studios", []):
                    studio_name = studio.get("name")
                    if studio_name:
                        user_profile['studios'][studio_name] = user_profile['studios'].get(studio_name, 0) + 1
        
        # Calculate user preferences
        scores = [a.get('score', 0) for a in user_anime_data if a.get('score', 0) > 0]
        user_profile['avg_score'] = sum(scores) / len(scores) if scores else 7.0
        
        top_genres = sorted(user_profile['genres'].items(), key=lambda x: x[1], reverse=True)
        preferred_studios = [s for s, c in user_profile['studios'].items() if c >= 2]
        
        print(f"Unique profile: Top genres: {[g for g, c in top_genres[:3]]}, Preferred studios: {preferred_studios}")
        
        # Step 2: Create targeted searches based on user's specific combination
        search_queries = []
        seen_anime_ids = set(user_anime_list)
        
        # Primary genre-based searches (more specific than generic)
        if len(top_genres) >= 1:
            primary_genre = top_genres[0][0]
            search_queries.append(f"best {primary_genre} anime")
            
            # Add combination searches for multiple genres
            if len(top_genres) >= 2:
                secondary_genre = top_genres[1][0]
                search_queries.append(f"{primary_genre} {secondary_genre}")
        
        # Studio-specific searches for strong preferences
        for studio in preferred_studios[:1]:  # Limit to one studio search
            search_queries.append(f"{studio} anime")
        
        # Score-tier specific search
        if user_profile['avg_score'] >= 8.0:
            search_queries.append("highly rated anime")
        else:
            search_queries.append("popular anime")
        
        # Limit total searches to prevent timeouts
        search_queries = search_queries[:4]
        print(f"Search queries: {search_queries}")
        
        # Step 3: Execute searches and collect unique candidates
        all_candidates = []
        
        for query in search_queries:
            try:
                print(f"Searching: {query}")
                search_results = self.mal_service.search_anime(query, limit=10)
                
                for anime in search_results:
                    anime_id = anime.get("mal_id")
                    score = anime.get("score", 0)
                    
                    # Filter: must have rating, not in user's list, not NSFW
                    if (anime_id and anime_id not in seen_anime_ids and 
                        score and score > 0 and not self.is_nsfw_content(anime)):
                        
                        # Calculate relevance to user's profile
                        relevance = self.calculate_relevance_score(anime, user_profile)
                        anime['relevance_score'] = relevance
                        anime['search_query'] = query
                        
                        all_candidates.append(anime)
                        seen_anime_ids.add(anime_id)
                
            except Exception as e:
                print(f"Search error for '{query}': {e}")
                continue
        
        # Step 4: Rank by relevance and select best matches
        all_candidates.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Step 5: Build final recommendations with diversity
        final_recommendations = []
        genre_counts = {}
        
        for anime in all_candidates:
            if len(final_recommendations) >= max_recommendations:
                break
            
            # Get primary genre for this anime
            anime_genres = [g.get('name', '') for g in anime.get('genres', [])]
            primary_genre = None
            
            # Find most relevant genre from user's preferences
            for genre in anime_genres:
                if genre in user_profile['genres']:
                    primary_genre = genre
                    break
            
            if not primary_genre and anime_genres:
                primary_genre = anime_genres[0]
            
            # Apply genre diversity (max 3 per genre)
            current_count = genre_counts.get(primary_genre, 0)
            if current_count < 3:
                
                # Check for studio boost
                anime_studios = [s.get('name', '') for s in anime.get('studios', [])]
                studio_boost = 0.1 if any(s in preferred_studios for s in anime_studios) else 0
                
                final_score = anime.get('relevance_score', 0) + studio_boost
                
                # Generate reason
                reason = self.generate_unique_reason(anime, user_profile, preferred_studios)
                
                recommendation = {
                    "mal_id": anime.get("mal_id"),
                    "title": anime.get("title", "Unknown"),
                    "score": anime.get("score", 0),
                    "genres": anime_genres,
                    "year": anime.get("year"),
                    "similarity_score": round(final_score, 3),
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
                    "studios": anime_studios,
                    "aired": anime.get("aired", {}).get("string"),
                    "primary_genre": primary_genre,
                    "genre_frequency": user_profile['genres'].get(primary_genre, 0),
                    "found_via": anime.get('search_query', 'unknown')
                }
                
                final_recommendations.append(recommendation)
                genre_counts[primary_genre] = current_count + 1
        
        print(f"Generated {len(final_recommendations)} unique recommendations")
        return final_recommendations
    
    def calculate_relevance_score(self, anime, user_profile):
        """Calculate how relevant this anime is to the user's specific profile."""
        score = 0.0
        
        # Genre matching (60% weight)
        anime_genres = set(g.get('name', '') for g in anime.get('genres', []))
        user_genres = set(user_profile['genres'].keys())
        genre_overlap = anime_genres.intersection(user_genres)
        
        if genre_overlap:
            # Weight by frequency in user's preferences
            genre_weight = sum(user_profile['genres'][g] for g in genre_overlap)
            total_user_genres = sum(user_profile['genres'].values())
            score += (genre_weight / total_user_genres) * 0.6
        
        # Score compatibility (25% weight)
        anime_score = anime.get('score', 0)
        if anime_score > 0:
            score_diff = abs(anime_score - user_profile['avg_score'])
            if score_diff <= 0.5:
                score += 0.25
            elif score_diff <= 1.0:
                score += 0.2
            elif score_diff <= 1.5:
                score += 0.15
            else:
                score += 0.05  # Small penalty for very different scores
        
        # Quality bonus (15% weight)
        if anime_score >= 8.0:
            score += 0.15
        elif anime_score >= 7.5:
            score += 0.1
        elif anime_score >= 7.0:
            score += 0.05
        
        return score
    
    def generate_unique_reason(self, anime, user_profile, preferred_studios):
        """Generate a reason based on why this anime matches the user's unique profile."""
        reasons = []
        
        # Check genre matches
        anime_genres = set(g.get('name', '') for g in anime.get('genres', []))
        user_genres = set(user_profile['genres'].keys())
        genre_matches = list(anime_genres.intersection(user_genres))
        
        if len(genre_matches) >= 2:
            reasons.append(f"Matches your {', '.join(genre_matches[:2])} preferences")
        elif len(genre_matches) == 1:
            reasons.append(f"Perfect {genre_matches[0]} match")
        
        # Check studio preference
        anime_studios = [s.get('name', '') for s in anime.get('studios', [])]
        for studio in anime_studios:
            if studio in preferred_studios:
                reasons.append(f"from your preferred {studio}")
                break
        
        # Check score match
        anime_score = anime.get('score', 0)
        if abs(anime_score - user_profile['avg_score']) <= 0.5:
            reasons.append(f"matches your taste ({anime_score:.1f}/10)")
        elif anime_score >= 8.0:
            reasons.append("highly rated")
        
        return " • ".join(reasons) if reasons else "recommended for your unique taste"
    
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
                "message": "user_anime_list must be a list of anime IDs or titles"
            }), 400
        
        if not user_anime_list:
            return jsonify({
                "status": "error", 
                "message": "user_anime_list cannot be empty"
            }), 400
        
        # Convert titles to IDs if needed
        processed_anime_list = []
        conversion_errors = []
        
        for anime in user_anime_list:
            if isinstance(anime, int):
                processed_anime_list.append(anime)
            elif isinstance(anime, str):
                try:
                    # Try to convert to int first (in case it's a string number)
                    anime_id = int(anime)
                    processed_anime_list.append(anime_id)
                except ValueError:
                    # It's an anime title, search for it
                    try:
                        search_results = mal_service.search_anime(anime.strip(), limit=1)
                        if search_results and len(search_results) > 0:
                            anime_id = search_results[0]['mal_id']
                            processed_anime_list.append(anime_id)
                            print(f"Converted title '{anime}' to ID {anime_id}")
                        else:
                            conversion_errors.append(f"Could not find anime with title: '{anime}'")
                    except Exception as e:
                        conversion_errors.append(f"Error searching for '{anime}': {str(e)}")
            else:
                conversion_errors.append(f"Invalid anime entry: {anime} (must be ID or title)")
        
        # If we have conversion errors, include them in response but continue with found anime
        if conversion_errors:
            print(f"Title conversion errors: {conversion_errors}")
        
        # If no valid anime found after conversion, return error
        if not processed_anime_list:
            return jsonify({
                "status": "error",
                "message": "No valid anime found after processing titles/IDs",
                "conversion_errors": conversion_errors
            }), 400
        
        # Get recommendations using the recommendation engine
        start_time = time.time()
        recommendations_list = recommendation_engine.get_recommendations(
            user_anime_list=processed_anime_list,
            max_recommendations=max_recommendations
        )
        processing_time = round(time.time() - start_time, 2)
        
        # Fallback if no recommendations found (prevent empty array for React)
        if not recommendations_list:
            print(f"No recommendations found for user list: {processed_anime_list}, trying fallback...")
            try:
                # Fallback: get some popular anime as basic recommendations
                fallback_anime = mal_service.get_top_anime(limit=max_recommendations)
                fallback_recommendations = []
                for anime in fallback_anime[:max_recommendations]:
                    if anime.get("mal_id") not in processed_anime_list:
                        # Filter NSFW from fallback too
                        if not recommendation_engine.is_nsfw_content(anime):
                            fallback_recommendations.append({
                                "mal_id": anime.get("mal_id"),
                                "title": anime.get("title", "Unknown"),
                                "score": anime.get("score", 0),
                                "genres": [g.get("name") for g in anime.get("genres", [])],
                                "year": anime.get("year"),
                                "similarity_score": 0.5,  # Default similarity
                                "reason": "Popular anime recommendation",
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
                recommendations_list = fallback_recommendations[:max_recommendations]
                print(f"Using fallback recommendations: {len(recommendations_list)} items")
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                
        # Format response
        response_data = {
            "status": "success",
            "recommendations": recommendations_list,
            "total_found": len(recommendations_list),
            "input_anime_count": len(processed_anime_list),
            "processing_time": processing_time,
            "algorithm": "Advanced Similarity Algorithm with NSFW filtering and fallback",
            "fallback_used": len(recommendations_list) > 0 and all(rec.get("reason") == "Popular anime recommendation" for rec in recommendations_list)
        }
        
        # Add conversion info if there were title conversions or errors
        if conversion_errors or any(isinstance(anime, str) for anime in user_anime_list):
            response_data["title_conversion"] = {
                "original_count": len(user_anime_list),
                "processed_count": len(processed_anime_list),
                "conversion_errors": conversion_errors
            }
        
        return jsonify(response_data)
        
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