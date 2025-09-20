"""
Validation utilities for the anime recommendation API.
"""

from typing import List, Dict, Any, Optional, Tuple
import re


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class RequestValidator:
    """Validates API requests and sanitizes input data"""
    
    @staticmethod
    def validate_anime_titles(titles: Any) -> List[str]:
        """
        Validate and sanitize anime titles.
        
        Args:
            titles: Input titles to validate
            
        Returns:
            List of validated and sanitized titles
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(titles, list):
            raise ValidationError("anime_titles must be a list")
        
        if not titles:
            raise ValidationError("anime_titles cannot be empty")
        
        if len(titles) > 10:
            raise ValidationError("Maximum 10 anime titles allowed")
        
        sanitized_titles = []
        for i, title in enumerate(titles):
            if not isinstance(title, str):
                raise ValidationError(f"Title at index {i} must be a string")
            
            # Sanitize title
            sanitized_title = RequestValidator._sanitize_title(title)
            
            if not sanitized_title:
                raise ValidationError(f"Title at index {i} is empty or invalid")
            
            if len(sanitized_title) > 200:
                raise ValidationError(f"Title at index {i} is too long (max 200 characters)")
            
            sanitized_titles.append(sanitized_title)
        
        # Remove duplicates while preserving order
        unique_titles = []
        seen = set()
        for title in sanitized_titles:
            title_lower = title.lower()
            if title_lower not in seen:
                unique_titles.append(title)
                seen.add(title_lower)
        
        return unique_titles
    
    @staticmethod
    def validate_max_recommendations(max_recs: Any) -> int:
        """
        Validate max_recommendations parameter.
        
        Args:
            max_recs: Input value to validate
            
        Returns:
            Validated integer value
            
        Raises:
            ValidationError: If validation fails
        """
        if max_recs is None:
            return 10  # Default value
        
        if not isinstance(max_recs, (int, float)):
            try:
                max_recs = int(max_recs)
            except (ValueError, TypeError):
                raise ValidationError("max_recommendations must be a number")
        
        max_recs = int(max_recs)
        
        if max_recs < 1:
            raise ValidationError("max_recommendations must be at least 1")
        
        if max_recs > 50:
            raise ValidationError("max_recommendations cannot exceed 50")
        
        return max_recs
    
    @staticmethod
    def validate_min_score(min_score: Any) -> float:
        """
        Validate min_score parameter.
        
        Args:
            min_score: Input value to validate
            
        Returns:
            Validated float value
            
        Raises:
            ValidationError: If validation fails
        """
        if min_score is None:
            return 0.0  # Default value
        
        if not isinstance(min_score, (int, float)):
            try:
                min_score = float(min_score)
            except (ValueError, TypeError):
                raise ValidationError("min_score must be a number")
        
        min_score = float(min_score)
        
        if min_score < 0.0:
            raise ValidationError("min_score cannot be negative")
        
        if min_score > 10.0:
            raise ValidationError("min_score cannot exceed 10.0")
        
        return min_score
    
    @staticmethod
    def validate_genres(genres: Any, field_name: str) -> List[str]:
        """
        Validate genre lists (exclude_genres, include_genres).
        
        Args:
            genres: Input genres to validate
            field_name: Name of the field for error messages
            
        Returns:
            List of validated and sanitized genres
            
        Raises:
            ValidationError: If validation fails
        """
        if genres is None:
            return []
        
        if not isinstance(genres, list):
            raise ValidationError(f"{field_name} must be a list")
        
        if len(genres) > 20:
            raise ValidationError(f"{field_name} cannot have more than 20 genres")
        
        sanitized_genres = []
        valid_genres = RequestValidator._get_valid_genres()
        
        for i, genre in enumerate(genres):
            if not isinstance(genre, str):
                raise ValidationError(f"Genre at index {i} in {field_name} must be a string")
            
            # Sanitize genre
            sanitized_genre = RequestValidator._sanitize_genre(genre)
            
            if not sanitized_genre:
                raise ValidationError(f"Genre at index {i} in {field_name} is empty or invalid")
            
            # Check if genre is valid (case-insensitive)
            genre_lower = sanitized_genre.lower()
            valid_genre = None
            for vg in valid_genres:
                if vg.lower() == genre_lower:
                    valid_genre = vg
                    break
            
            if valid_genre:
                sanitized_genres.append(valid_genre)
            else:
                # Allow unknown genres but log a warning
                sanitized_genres.append(sanitized_genre)
        
        # Remove duplicates while preserving order
        unique_genres = []
        seen = set()
        for genre in sanitized_genres:
            genre_lower = genre.lower()
            if genre_lower not in seen:
                unique_genres.append(genre)
                seen.add(genre_lower)
        
        return unique_genres
    
    @staticmethod
    def validate_search_query(query: Any) -> str:
        """
        Validate search query parameter.
        
        Args:
            query: Input query to validate
            
        Returns:
            Validated and sanitized query string
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(query, str):
            raise ValidationError("Query must be a string")
        
        query = query.strip()
        
        if not query:
            raise ValidationError("Query cannot be empty")
        
        if len(query) < 2:
            raise ValidationError("Query must be at least 2 characters long")
        
        if len(query) > 100:
            raise ValidationError("Query cannot exceed 100 characters")
        
        # Remove potentially harmful characters
        sanitized_query = re.sub(r'[<>"\';\\]', '', query)
        
        if not sanitized_query.strip():
            raise ValidationError("Query contains only invalid characters")
        
        return sanitized_query.strip()
    
    @staticmethod
    def validate_limit_parameter(limit: Any) -> int:
        """
        Validate limit parameter for various endpoints.
        
        Args:
            limit: Input limit to validate
            
        Returns:
            Validated integer value
            
        Raises:
            ValidationError: If validation fails
        """
        if limit is None:
            return 10  # Default value
        
        if not isinstance(limit, (int, float)):
            try:
                limit = int(limit)
            except (ValueError, TypeError):
                raise ValidationError("limit must be a number")
        
        limit = int(limit)
        
        if limit < 1:
            raise ValidationError("limit must be at least 1")
        
        if limit > 100:
            raise ValidationError("limit cannot exceed 100")
        
        return limit
    
    @staticmethod
    def _sanitize_title(title: str) -> str:
        """Sanitize anime title input"""
        if not isinstance(title, str):
            return ""
        
        # Remove leading/trailing whitespace
        title = title.strip()
        
        # Remove potentially harmful characters but keep Unicode
        # Allow letters, numbers, spaces, and common punctuation
        title = re.sub(r'[<>"\'\\]', '', title)
        
        # Normalize multiple spaces to single space
        title = re.sub(r'\s+', ' ', title)
        
        return title
    
    @staticmethod
    def _sanitize_genre(genre: str) -> str:
        """Sanitize genre input"""
        if not isinstance(genre, str):
            return ""
        
        # Remove leading/trailing whitespace
        genre = genre.strip()
        
        # Remove potentially harmful characters
        genre = re.sub(r'[<>"\'\\]', '', genre)
        
        # Capitalize first letter of each word
        genre = ' '.join(word.capitalize() for word in genre.split())
        
        return genre
    
    @staticmethod
    def _get_valid_genres() -> List[str]:
        """Get list of valid anime genres"""
        return [
            "Action", "Adventure", "Avant Garde", "Award Winning", "Boys Love", 
            "Comedy", "Drama", "Fantasy", "Girls Love", "Gourmet", "Horror",
            "Mystery", "Romance", "Sci-Fi", "Slice of Life", "Sports", "Supernatural",
            "Suspense", "Thriller", "Ecchi", "Erotica", "Hentai",
            # Themes
            "Adult Cast", "Anthropomorphic", "CGDCT", "Childcare", "Combat Sports",
            "Crossdressing", "Delinquents", "Detective", "Educational", "Gag Humor",
            "Gore", "Harem", "High Stakes Game", "Historical", "Idols (Female)",
            "Idols (Male)", "Isekai", "Iyashikei", "Love Polygon", "Magical Sex Shift",
            "Mahou Shoujo", "Martial Arts", "Mecha", "Medical", "Military", "Music",
            "Mythology", "Organized Crime", "Otaku Culture", "Parody", "Performing Arts",
            "Pets", "Psychological", "Racing", "Reincarnation", "Reverse Harem",
            "Romantic Subtext", "Samurai", "School", "Showbiz", "Space", "Strategy Game",
            "Super Power", "Survival", "Team Sports", "Time Travel", "Vampire",
            "Video Game", "Visual Arts", "Workplace",
            # Demographics
            "Josei", "Kids", "Seinen", "Shoujo", "Shounen"
        ]


class ResponseFormatter:
    """Formats API responses consistently"""
    
    @staticmethod
    def success_response(data: Dict[str, Any], message: Optional[str] = None) -> Dict[str, Any]:
        """Format successful response"""
        response = {
            'status': 'success',
            'data': data
        }
        
        if message:
            response['message'] = message
        
        return response
    
    @staticmethod
    def error_response(error: str, message: Optional[str] = None, 
                      error_code: Optional[str] = None) -> Dict[str, Any]:
        """Format error response"""
        response = {
            'status': 'error',
            'error': error
        }
        
        if message:
            response['message'] = message
        
        if error_code:
            response['error_code'] = error_code
        
        return response
    
    @staticmethod
    def validation_error_response(error: str) -> Dict[str, Any]:
        """Format validation error response"""
        return ResponseFormatter.error_response(
            error=error,
            error_code='VALIDATION_ERROR'
        )