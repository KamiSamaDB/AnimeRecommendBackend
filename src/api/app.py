"""
Flask API for anime recommendation system.
Provides endpoints for getting anime recommendations based on user preferences.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import traceback
from typing import Dict, Any

from services.mal_service import MALService
from services.simple_recommendation_engine import SimpleAnimeRecommendationEngine
from models.anime import RecommendationRequest, RecommendationResponse
from utils.validation import RequestValidator, ValidationError, ResponseFormatter


class AnimeRecommendationAPI:
    """Flask API wrapper for anime recommendation system"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for React frontend
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.mal_service = MALService(rate_limit_delay=0.3)
        self.recommendation_engine = SimpleAnimeRecommendationEngine(self.mal_service)
        
        # Setup routes
        self._setup_routes()
        
        # Initialize database on startup
        self._initialize_system()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Root endpoint with API information"""
            return jsonify({
                'message': '🎌 Anime Recommendation API',
                'version': '1.0.0',
                'status': 'running',
                'endpoints': {
                    'health': '/health',
                    'recommendations': '/api/recommendations (POST)',
                    'trending': '/api/trending (GET)',
                    'search': '/api/anime/search?q=QUERY (GET)',
                    'stats': '/api/database/stats (GET)'
                },
                'documentation': 'See REACT_INTEGRATION.md for usage examples'
            })
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'database_size': len(self.recommendation_engine.anime_database)
            })
        
        @self.app.route('/api/recommendations', methods=['POST'])
        def get_recommendations():
            """
            Get anime recommendations based on input anime titles.
            
            Request body:
            {
                "anime_titles": ["Attack on Titan", "Death Note"],
                "max_recommendations": 10,
                "min_score": 7.0,
                "exclude_genres": ["Horror"],
                "include_genres": ["Action"]
            }
            """
            try:
                start_time = time.time()
                
                # Validate request
                if not request.is_json:
                    return jsonify(ResponseFormatter.validation_error_response(
                        'Request must be JSON'
                    )), 400
                
                data = request.get_json()
                
                if not data:
                    return jsonify(ResponseFormatter.validation_error_response(
                        'Request body cannot be empty'
                    )), 400
                
                # Validate and sanitize input
                try:
                    anime_titles = RequestValidator.validate_anime_titles(
                        data.get('anime_titles')
                    )
                    max_recommendations = RequestValidator.validate_max_recommendations(
                        data.get('max_recommendations', 10)
                    )
                    min_score = RequestValidator.validate_min_score(
                        data.get('min_score', 0.0)
                    )
                    exclude_genres = RequestValidator.validate_genres(
                        data.get('exclude_genres'), 'exclude_genres'
                    )
                    include_genres = RequestValidator.validate_genres(
                        data.get('include_genres'), 'include_genres'
                    )
                    
                except ValidationError as ve:
                    return jsonify(ResponseFormatter.validation_error_response(
                        str(ve)
                    )), 400
                
                # Get recommendations
                recommendations = self.recommendation_engine.get_recommendations(
                    input_anime_titles=anime_titles,
                    max_recommendations=max_recommendations,
                    min_score=min_score,
                    exclude_genres=exclude_genres,
                    include_genres=include_genres
                )
                
                # Track which input anime were found
                input_anime = self.recommendation_engine._find_input_anime(anime_titles)
                input_anime_found = [anime.title for anime in input_anime]
                input_anime_not_found = [title for title in anime_titles 
                                       if not any(self.recommendation_engine._titles_match(title, anime) 
                                                for anime in input_anime)]
                
                # Create response
                processing_time = time.time() - start_time
                response = RecommendationResponse(
                    recommendations=recommendations,
                    total_found=len(recommendations),
                    processing_time=processing_time,
                    input_anime_found=input_anime_found,
                    input_anime_not_found=input_anime_not_found
                )
                
                self.logger.info(f"Generated {len(recommendations)} recommendations in {processing_time:.2f}s")
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error processing recommendations: {e}")
                self.logger.error(traceback.format_exc())
                return jsonify(ResponseFormatter.error_response(
                    'Internal server error', str(e)
                )), 500
        
        @self.app.route('/api/trending', methods=['GET'])
        def get_trending():
            """Get trending anime recommendations"""
            try:
                # Validate limit parameter
                try:
                    limit = RequestValidator.validate_limit_parameter(
                        request.args.get('limit', 10)
                    )
                except ValidationError as ve:
                    return jsonify(ResponseFormatter.validation_error_response(
                        str(ve)
                    )), 400
                
                recommendations = self.recommendation_engine.get_trending_recommendations(limit=limit)
                
                return jsonify(ResponseFormatter.success_response({
                    'recommendations': [rec.to_dict() for rec in recommendations],
                    'total_found': len(recommendations)
                }))
                
            except Exception as e:
                self.logger.error(f"Error fetching trending anime: {e}")
                return jsonify(ResponseFormatter.error_response(
                    'Internal server error', str(e)
                )), 500
        
        @self.app.route('/api/anime/search', methods=['GET'])
        def search_anime():
            """Search for anime by title"""
            try:
                # Validate query parameter
                try:
                    query = RequestValidator.validate_search_query(
                        request.args.get('q', '')
                    )
                except ValidationError as ve:
                    return jsonify(ResponseFormatter.validation_error_response(
                        str(ve)
                    )), 400
                
                # Search anime
                anime_data = self.mal_service.search_anime(query)
                
                if anime_data:
                    return jsonify(ResponseFormatter.success_response({
                        'anime': anime_data
                    }))
                else:
                    return jsonify(ResponseFormatter.error_response(
                        'No anime found with that title',
                        error_code='NOT_FOUND'
                    )), 404
                    
            except Exception as e:
                self.logger.error(f"Error searching anime: {e}")
                return jsonify(ResponseFormatter.error_response(
                    'Internal server error', str(e)
                )), 500
        
        @self.app.route('/api/database/stats', methods=['GET'])
        def get_database_stats():
            """Get database statistics"""
            try:
                anime_db = self.recommendation_engine.anime_database
                
                if not anime_db:
                    return jsonify({
                        'error': 'Database not initialized'
                    }), 503
                
                # Calculate statistics
                total_anime = len(anime_db)
                avg_score = sum(anime.score for anime in anime_db if anime.score > 0) / total_anime
                
                # Genre distribution
                genre_count = {}
                for anime in anime_db:
                    for genre in anime.genres:
                        genre_count[genre] = genre_count.get(genre, 0) + 1
                
                top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Score distribution
                score_ranges = {
                    '9.0+': len([a for a in anime_db if a.score >= 9.0]),
                    '8.0-8.9': len([a for a in anime_db if 8.0 <= a.score < 9.0]),
                    '7.0-7.9': len([a for a in anime_db if 7.0 <= a.score < 8.0]),
                    '6.0-6.9': len([a for a in anime_db if 6.0 <= a.score < 7.0]),
                    'Below 6.0': len([a for a in anime_db if 0 < a.score < 6.0])
                }
                
                return jsonify({
                    'total_anime': total_anime,
                    'average_score': round(avg_score, 2),
                    'top_genres': top_genres,
                    'score_distribution': score_ranges,
                    'status': 'success'
                })
                
            except Exception as e:
                self.logger.error(f"Error getting database stats: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'message': str(e)
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'error': 'Endpoint not found',
                'message': 'The requested endpoint does not exist'
            }), 404
        
        @self.app.errorhandler(405)
        def method_not_allowed(error):
            return jsonify({
                'error': 'Method not allowed',
                'message': 'The request method is not allowed for this endpoint'
            }), 405
    
    def _initialize_system(self):
        """Initialize the recommendation system"""
        try:
            self.logger.info("System ready - database will initialize on first request")
            # Don't initialize database immediately to avoid blocking startup
            # self.recommendation_engine.initialize_database()
        except Exception as e:
            self.logger.error(f"Error during system initialization: {e}")
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the Flask application"""
        self.logger.info(f"Starting Anime Recommendation API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)