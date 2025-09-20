"""
AI-powered anime recommendation algorithm.
Uses content-based filtering with genre analysis, rating weights, and popularity scoring.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
import logging
import time
from collections import Counter

from models.anime import Anime, AnimeRecommendation
from services.mal_service import MALService


class AnimeRecommendationEngine:
    """
    AI-powered anime recommendation engine using hybrid approach:
    1. Content-based filtering (genres, synopsis)
    2. Collaborative filtering (ratings, popularity)
    3. Semantic similarity (synopsis analysis)
    """
    
    def __init__(self, mal_service: MALService):
        self.mal_service = mal_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize ML models
        self.genre_vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        self.synopsis_vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))
        self.scaler = MinMaxScaler()
        
        # Initialize sentence transformer for semantic similarity (lazy loading)
        self._sentence_model = None
        
        # Anime database cache
        self.anime_database = []
        self.genre_matrix = None
        self.synopsis_matrix = None
        self.features_scaled = None
        
        # Weights for different factors
        self.weights = {
            'genre_similarity': 0.35,
            'synopsis_similarity': 0.25,
            'rating_score': 0.20,
            'popularity_score': 0.15,
            'semantic_similarity': 0.05
        }
    
    @property
    def sentence_model(self):
        """Lazy loading of sentence transformer model"""
        if self._sentence_model is None:
            try:
                self._sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                self.logger.warning(f"Could not load sentence transformer: {e}")
                self._sentence_model = None
        return self._sentence_model
    
    def initialize_database(self, force_refresh: bool = False) -> None:
        """
        Initialize the anime database with top anime from MAL.
        
        Args:
            force_refresh: Force refresh of database even if already loaded
        """
        if self.anime_database and not force_refresh:
            return
            
        self.logger.info("Initializing anime database...")
        start_time = time.time()
        
        try:
            # Get top anime from MAL
            top_anime_data = self.mal_service.get_top_anime(limit=500)
            
            # Convert to Anime objects
            self.anime_database = []
            for anime_data in top_anime_data:
                if anime_data:
                    anime = Anime.from_dict(anime_data)
                    # Filter out anime with insufficient data
                    if anime.score > 0 and anime.genres and anime.synopsis:
                        self.anime_database.append(anime)
            
            self.logger.info(f"Loaded {len(self.anime_database)} anime into database")
            
            # Prepare ML features
            self._prepare_features()
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Database initialization completed in {elapsed_time:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def _prepare_features(self) -> None:
        """Prepare ML features for recommendation algorithm"""
        if not self.anime_database:
            return
            
        # Prepare genre features
        genre_texts = [' '.join(anime.genres) for anime in self.anime_database]
        self.genre_matrix = self.genre_vectorizer.fit_transform(genre_texts)
        
        # Prepare synopsis features
        synopsis_texts = [anime.synopsis or '' for anime in self.anime_database]
        self.synopsis_matrix = self.synopsis_vectorizer.fit_transform(synopsis_texts)
        
        # Prepare numerical features (score, popularity, members)
        features = []
        for anime in self.anime_database:
            # Normalize popularity (lower is better, so invert)
            popularity_score = 1.0 / (anime.popularity or 1000) if anime.popularity else 0.001
            features.append([
                anime.score or 0.0,
                popularity_score,
                np.log1p(anime.members or 1),  # Log transform for members
                np.log1p(anime.favorites or 1)  # Log transform for favorites
            ])
        
        self.features_scaled = self.scaler.fit_transform(features)
    
    def get_recommendations(self, input_anime_titles: List[str], max_recommendations: int = 10,
                          min_score: float = 7.0, exclude_genres: List[str] = None,
                          include_genres: List[str] = None) -> List[AnimeRecommendation]:
        """
        Generate anime recommendations based on input anime titles.
        
        Args:
            input_anime_titles: List of anime titles user likes
            max_recommendations: Maximum number of recommendations to return
            min_score: Minimum score threshold
            exclude_genres: Genres to exclude from recommendations
            include_genres: Genres that must be included in recommendations
            
        Returns:
            List of AnimeRecommendation objects
        """
        if not self.anime_database:
            self.initialize_database()
        
        exclude_genres = exclude_genres or []
        include_genres = include_genres or []
        
        # Find input anime in database
        input_anime = self._find_input_anime(input_anime_titles)
        
        if not input_anime:
            self.logger.warning("No input anime found in database")
            return []
        
        # Calculate recommendation scores for all anime
        recommendations = []
        input_anime_ids = {anime.mal_id for anime in input_anime}
        
        for i, candidate_anime in enumerate(self.anime_database):
            # Skip anime that are in the input list
            if candidate_anime.mal_id in input_anime_ids:
                continue
            
            # Apply filters
            if candidate_anime.score < min_score:
                continue
            
            if exclude_genres and any(genre in candidate_anime.genres for genre in exclude_genres):
                continue
            
            if include_genres and not any(genre in candidate_anime.genres for genre in include_genres):
                continue
            
            # Calculate similarity score
            similarity_score, reasons = self._calculate_similarity(input_anime, candidate_anime, i)
            
            # Calculate confidence score based on data quality
            confidence_score = self._calculate_confidence(candidate_anime)
            
            recommendation = AnimeRecommendation(
                anime=candidate_anime,
                similarity_score=similarity_score,
                confidence_score=confidence_score,
                reasons=reasons
            )
            
            recommendations.append(recommendation)
        
        # Sort by similarity score and return top recommendations
        recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return recommendations[:max_recommendations]
    
    def _find_input_anime(self, titles: List[str]) -> List[Anime]:
        """Find input anime in the database or search MAL"""
        input_anime = []
        
        for title in titles:
            # First, try to find in existing database
            found = False
            for anime in self.anime_database:
                if self._titles_match(title, anime):
                    input_anime.append(anime)
                    found = True
                    break
            
            # If not found in database, search MAL
            if not found:
                anime_data = self.mal_service.search_anime(title)
                if anime_data:
                    anime = Anime.from_dict(anime_data)
                    input_anime.append(anime)
                    # Add to database for future use
                    if anime.score > 0 and anime.genres and anime.synopsis:
                        self.anime_database.append(anime)
                        # Re-prepare features if database is updated
                        self._prepare_features()
        
        return input_anime
    
    def _titles_match(self, search_title: str, anime: Anime) -> bool:
        """Check if search title matches any of the anime's titles"""
        search_lower = search_title.lower().strip()
        
        titles_to_check = [
            anime.title,
            anime.title_english,
            anime.title_japanese
        ]
        
        for title in titles_to_check:
            if title and search_lower in title.lower():
                return True
            if title and title.lower() in search_lower:
                return True
        
        return False
    
    def _calculate_similarity(self, input_anime: List[Anime], candidate_anime: Anime, 
                            candidate_index: int) -> Tuple[float, List[str]]:
        """Calculate similarity score between input anime and candidate"""
        total_score = 0.0
        reasons = []
        
        # 1. Genre similarity
        genre_sim = self._calculate_genre_similarity(input_anime, candidate_anime, candidate_index)
        total_score += genre_sim * self.weights['genre_similarity']
        if genre_sim > 0.5:
            common_genres = self._get_common_genres(input_anime, candidate_anime)
            reasons.append(f"Similar genres: {', '.join(common_genres[:3])}")
        
        # 2. Synopsis similarity
        synopsis_sim = self._calculate_synopsis_similarity(input_anime, candidate_anime, candidate_index)
        total_score += synopsis_sim * self.weights['synopsis_similarity']
        if synopsis_sim > 0.3:
            reasons.append("Similar themes and story elements")
        
        # 3. Rating score
        rating_sim = self._calculate_rating_similarity(input_anime, candidate_anime)
        total_score += rating_sim * self.weights['rating_score']
        if candidate_anime.score >= 8.0:
            reasons.append(f"Highly rated ({candidate_anime.score}/10)")
        
        # 4. Popularity score
        popularity_sim = self._calculate_popularity_similarity(input_anime, candidate_anime)
        total_score += popularity_sim * self.weights['popularity_score']
        if candidate_anime.popularity and candidate_anime.popularity <= 100:
            reasons.append(f"Very popular (rank #{candidate_anime.popularity})")
        
        # 5. Semantic similarity (if available)
        if self.sentence_model:
            semantic_sim = self._calculate_semantic_similarity(input_anime, candidate_anime)
            total_score += semantic_sim * self.weights['semantic_similarity']
            if semantic_sim > 0.7:
                reasons.append("Similar story concepts")
        
        if not reasons:
            reasons.append("Recommended based on overall similarity")
        
        return total_score, reasons
    
    def _calculate_genre_similarity(self, input_anime: List[Anime], candidate_anime: Anime, 
                                  candidate_index: int) -> float:
        """Calculate genre-based similarity"""
        if candidate_index >= self.genre_matrix.shape[0]:
            return 0.0
            
        candidate_genres = self.genre_matrix[candidate_index:candidate_index+1]
        similarities = []
        
        for input_anim in input_anime:
            # Find input anime in database to get its genre vector
            input_genres_text = ' '.join(input_anim.genres)
            input_vector = self.genre_vectorizer.transform([input_genres_text])
            
            sim = cosine_similarity(input_vector, candidate_genres)[0, 0]
            similarities.append(sim)
        
        return max(similarities) if similarities else 0.0
    
    def _calculate_synopsis_similarity(self, input_anime: List[Anime], candidate_anime: Anime,
                                     candidate_index: int) -> float:
        """Calculate synopsis-based similarity"""
        if candidate_index >= self.synopsis_matrix.shape[0]:
            return 0.0
            
        candidate_synopsis = self.synopsis_matrix[candidate_index:candidate_index+1]
        similarities = []
        
        for input_anim in input_anime:
            input_synopsis_text = input_anim.synopsis or ''
            input_vector = self.synopsis_vectorizer.transform([input_synopsis_text])
            
            sim = cosine_similarity(input_vector, candidate_synopsis)[0, 0]
            similarities.append(sim)
        
        return max(similarities) if similarities else 0.0
    
    def _calculate_rating_similarity(self, input_anime: List[Anime], candidate_anime: Anime) -> float:
        """Calculate rating-based similarity"""
        input_scores = [anime.score for anime in input_anime if anime.score > 0]
        
        if not input_scores:
            return 0.5  # Neutral if no scores available
        
        avg_input_score = np.mean(input_scores)
        score_diff = abs(candidate_anime.score - avg_input_score)
        
        # Convert difference to similarity (closer scores = higher similarity)
        similarity = max(0, 1.0 - (score_diff / 5.0))  # Normalize by max possible difference
        
        return similarity
    
    def _calculate_popularity_similarity(self, input_anime: List[Anime], candidate_anime: Anime) -> float:
        """Calculate popularity-based similarity"""
        # Favor popular anime (lower popularity rank is better)
        if not candidate_anime.popularity:
            return 0.3  # Neutral for unknown popularity
        
        # Normalize popularity rank (1-1000+ range)
        normalized_popularity = max(0, min(1.0, 1.0 - (candidate_anime.popularity / 1000)))
        
        return normalized_popularity
    
    def _calculate_semantic_similarity(self, input_anime: List[Anime], candidate_anime: Anime) -> float:
        """Calculate semantic similarity using sentence transformers"""
        try:
            input_texts = [anime.synopsis[:500] for anime in input_anime if anime.synopsis]
            candidate_text = candidate_anime.synopsis[:500] if candidate_anime.synopsis else ""
            
            if not input_texts or not candidate_text:
                return 0.0
            
            # Get embeddings
            input_embeddings = self.sentence_model.encode(input_texts)
            candidate_embedding = self.sentence_model.encode([candidate_text])
            
            # Calculate similarities
            similarities = cosine_similarity(input_embeddings, candidate_embedding)
            
            return float(np.max(similarities))
            
        except Exception as e:
            self.logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _get_common_genres(self, input_anime: List[Anime], candidate_anime: Anime) -> List[str]:
        """Get common genres between input anime and candidate"""
        input_genres = set()
        for anime in input_anime:
            input_genres.update(anime.genres)
        
        candidate_genres = set(candidate_anime.genres)
        common = list(input_genres.intersection(candidate_genres))
        
        return common
    
    def _calculate_confidence(self, anime: Anime) -> float:
        """Calculate confidence score based on data completeness and quality"""
        score = 0.0
        
        # Score availability and quality
        if anime.score > 0:
            score += 0.3
        if anime.scored_by > 1000:
            score += 0.2
        
        # Popularity and member count
        if anime.popularity and anime.popularity <= 1000:
            score += 0.2
        if anime.members > 10000:
            score += 0.1
        
        # Data completeness
        if anime.genres:
            score += 0.1
        if anime.synopsis and len(anime.synopsis) > 100:
            score += 0.1
        
        return min(1.0, score)
    
    def get_trending_recommendations(self, limit: int = 10) -> List[AnimeRecommendation]:
        """Get trending anime recommendations based on recent popularity"""
        if not self.anime_database:
            self.initialize_database()
        
        # Filter for recent, highly-rated anime
        recent_anime = []
        for anime in self.anime_database:
            if (anime.year and anime.year >= 2020 and 
                anime.score >= 7.5 and 
                anime.members > 50000):
                recent_anime.append(anime)
        
        # Sort by a combination of score and popularity
        recent_anime.sort(key=lambda x: (x.score * 0.7 + (1000 - (x.popularity or 1000)) / 1000 * 0.3), reverse=True)
        
        recommendations = []
        for anime in recent_anime[:limit]:
            recommendation = AnimeRecommendation(
                anime=anime,
                similarity_score=anime.score / 10.0,
                confidence_score=self._calculate_confidence(anime),
                reasons=[f"Trending anime with {anime.score}/10 rating"]
            )
            recommendations.append(recommendation)
        
        return recommendations