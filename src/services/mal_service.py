"""
MyAnimeList API service for fetching anime data.
Uses Jikan API (unofficial MAL API) to get anime information.
"""

import requests
import time
from typing import List, Dict, Optional
import logging

class MALService:
    def __init__(self, rate_limit_delay: float = 0.5):
        self.base_url = "https://api.jikan.moe/v4"
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
    def search_anime(self, title: str) -> Optional[Dict]:
        """
        Search for anime by title and return the best match.
        
        Args:
            title: The anime title to search for
            
        Returns:
            Dictionary containing anime data or None if not found
        """
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            url = f"{self.base_url}/anime"
            params = {
                'q': title,
                'limit': 5,
                'order_by': 'popularity',
                'sort': 'asc'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                # Return the first (most popular) result
                anime = data['data'][0]
                return self._format_anime_data(anime)
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching for anime '{title}': {e}")
            
        return None
    
    def get_anime_by_id(self, anime_id: int) -> Optional[Dict]:
        """
        Get anime details by MAL ID.
        
        Args:
            anime_id: MyAnimeList anime ID
            
        Returns:
            Dictionary containing anime data or None if not found
        """
        try:
            time.sleep(self.rate_limit_delay)
            
            url = f"{self.base_url}/anime/{anime_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data'):
                return self._format_anime_data(data['data'])
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching anime with ID {anime_id}: {e}")
            
        return None
    
    def get_recommendations_by_genre(self, genres: List[str], limit: int = 50) -> List[Dict]:
        """
        Get anime recommendations based on genres.
        
        Args:
            genres: List of genre names
            limit: Maximum number of anime to return
            
        Returns:
            List of anime dictionaries
        """
        recommendations = []
        
        try:
            time.sleep(self.rate_limit_delay)
            
            # Get top anime by popularity/score
            url = f"{self.base_url}/anime"
            params = {
                'order_by': 'score',
                'sort': 'desc',
                'limit': limit,
                'status': 'complete',
                'type': 'tv'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data'):
                for anime in data['data']:
                    formatted_anime = self._format_anime_data(anime)
                    if formatted_anime:
                        recommendations.append(formatted_anime)
                        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching recommendations: {e}")
            
        return recommendations
    
    def get_top_anime(self, limit: int = 100) -> List[Dict]:
        """
        Get top-rated anime from MAL.
        
        Args:
            limit: Maximum number of anime to return
            
        Returns:
            List of anime dictionaries
        """
        anime_list = []
        
        try:
            time.sleep(self.rate_limit_delay)
            
            url = f"{self.base_url}/top/anime"
            params = {
                'limit': min(limit, 25)  # Jikan API has a max limit of 25
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data'):
                for anime in data['data']:
                    formatted_anime = self._format_anime_data(anime)
                    if formatted_anime:
                        anime_list.append(formatted_anime)
                        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching top anime: {e}")
            
        return anime_list
    
    def _format_anime_data(self, anime_data: Dict) -> Dict:
        """
        Format raw anime data from Jikan API into standardized format.
        
        Args:
            anime_data: Raw anime data from Jikan API
            
        Returns:
            Formatted anime dictionary
        """
        try:
            # Extract genres
            genres = []
            if anime_data.get('genres'):
                genres.extend([genre['name'] for genre in anime_data['genres']])
            if anime_data.get('themes'):
                genres.extend([theme['name'] for theme in anime_data['themes']])
            if anime_data.get('demographics'):
                genres.extend([demo['name'] for demo in anime_data['demographics']])
            
            # Get studio information
            studios = []
            if anime_data.get('studios'):
                studios = [studio['name'] for studio in anime_data['studios']]
            
            return {
                'mal_id': anime_data.get('mal_id'),
                'title': anime_data.get('title'),
                'title_english': anime_data.get('title_english'),
                'title_japanese': anime_data.get('title_japanese'),
                'score': anime_data.get('score', 0.0),
                'scored_by': anime_data.get('scored_by', 0),
                'rank': anime_data.get('rank'),
                'popularity': anime_data.get('popularity'),
                'members': anime_data.get('members', 0),
                'favorites': anime_data.get('favorites', 0),
                'synopsis': anime_data.get('synopsis', ''),
                'genres': genres,
                'studios': studios,
                'episodes': anime_data.get('episodes', 0),
                'status': anime_data.get('status'),
                'aired_from': anime_data.get('aired', {}).get('from'),
                'rating': anime_data.get('rating'),
                'source': anime_data.get('source'),
                'type': anime_data.get('type'),
                'year': anime_data.get('year'),
                'season': anime_data.get('season'),
                'image_url': anime_data.get('images', {}).get('jpg', {}).get('large_image_url'),
                'url': anime_data.get('url')
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting anime data: {e}")
            return None
    
    def batch_search_anime(self, titles: List[str]) -> List[Dict]:
        """
        Search for multiple anime titles and return results.
        
        Args:
            titles: List of anime titles to search for
            
        Returns:
            List of anime dictionaries (may contain None values for failed searches)
        """
        results = []
        
        for title in titles:
            anime_data = self.search_anime(title)
            if anime_data:
                results.append(anime_data)
            else:
                self.logger.warning(f"Could not find anime: {title}")
                
        return results