"""
Data models for anime recommendation system.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class Anime:
    """Anime data model"""
    mal_id: int
    title: str
    title_english: Optional[str] = None
    title_japanese: Optional[str] = None
    score: float = 0.0
    scored_by: int = 0
    rank: Optional[int] = None
    popularity: Optional[int] = None
    members: int = 0
    favorites: int = 0
    synopsis: str = ""
    genres: List[str] = None
    studios: List[str] = None
    episodes: int = 0
    status: str = ""
    aired_from: Optional[str] = None
    rating: Optional[str] = None
    source: Optional[str] = None
    type: str = ""
    year: Optional[int] = None
    season: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    
    def __post_init__(self):
        if self.genres is None:
            self.genres = []
        if self.studios is None:
            self.studios = []
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Anime':
        """Create Anime instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert Anime instance to dictionary"""
        return {
            'mal_id': self.mal_id,
            'title': self.title,
            'title_english': self.title_english,
            'title_japanese': self.title_japanese,
            'score': self.score,
            'scored_by': self.scored_by,
            'rank': self.rank,
            'popularity': self.popularity,
            'members': self.members,
            'favorites': self.favorites,
            'synopsis': self.synopsis,
            'genres': self.genres,
            'studios': self.studios,
            'episodes': self.episodes,
            'status': self.status,
            'aired_from': self.aired_from,
            'rating': self.rating,
            'source': self.source,
            'type': self.type,
            'year': self.year,
            'season': self.season,
            'image_url': self.image_url,
            'url': self.url
        }
    
    def get_display_title(self) -> str:
        """Get the best available title for display"""
        if self.title_english and self.title_english != self.title:
            return f"{self.title} ({self.title_english})"
        return self.title
    
    def get_genre_string(self) -> str:
        """Get comma-separated genre string"""
        return ", ".join(self.genres)
    
    def get_studio_string(self) -> str:
        """Get comma-separated studio string"""
        return ", ".join(self.studios)


@dataclass
class AnimeRecommendation:
    """Anime recommendation with similarity score and reasoning"""
    anime: Anime
    similarity_score: float
    confidence_score: float
    reasons: List[str]
    
    def to_dict(self) -> Dict:
        """Convert recommendation to dictionary for API response"""
        return {
            'mal_id': self.anime.mal_id,
            'title': self.anime.title,
            'title_english': self.anime.title_english,
            'score': self.anime.score,
            'popularity': self.anime.popularity,
            'genres': self.anime.genres,
            'synopsis': self.anime.synopsis[:200] + "..." if len(self.anime.synopsis) > 200 else self.anime.synopsis,
            'episodes': self.anime.episodes,
            'year': self.anime.year,
            'image_url': self.anime.image_url,
            'similarity_score': round(self.similarity_score, 3),
            'confidence_score': round(self.confidence_score, 3),
            'reasons': self.reasons,
            'url': self.anime.url
        }


@dataclass
class RecommendationRequest:
    """Request model for anime recommendations"""
    anime_titles: List[str]
    max_recommendations: int = 10
    min_score: float = 0.0
    exclude_genres: List[str] = None
    include_genres: List[str] = None
    
    def __post_init__(self):
        if self.exclude_genres is None:
            self.exclude_genres = []
        if self.include_genres is None:
            self.include_genres = []
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RecommendationRequest':
        """Create request from dictionary"""
        return cls(
            anime_titles=data.get('anime_titles', []),
            max_recommendations=data.get('max_recommendations', 10),
            min_score=data.get('min_score', 0.0),
            exclude_genres=data.get('exclude_genres', []),
            include_genres=data.get('include_genres', [])
        )


@dataclass
class RecommendationResponse:
    """Response model for anime recommendations"""
    recommendations: List[AnimeRecommendation]
    total_found: int
    processing_time: float
    input_anime_found: List[str]
    input_anime_not_found: List[str]
    
    def to_dict(self) -> Dict:
        """Convert response to dictionary for API"""
        return {
            'recommendations': [rec.to_dict() for rec in self.recommendations],
            'total_found': self.total_found,
            'processing_time': round(self.processing_time, 3),
            'input_anime_found': self.input_anime_found,
            'input_anime_not_found': self.input_anime_not_found,
            'status': 'success'
        }