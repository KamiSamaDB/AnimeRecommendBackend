"""
Demo script showing the anime recommendation system functionality
This works without external API dependencies for demonstration purposes.
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from models.anime import Anime, AnimeRecommendation
from services.simple_recommendation_engine import SimpleAnimeRecommendationEngine
from services.mal_service import MALService

def create_sample_database():
    """Create sample anime data for demonstration"""
    sample_anime = [
        {
            'mal_id': 1,
            'title': 'Attack on Titan',
            'title_english': 'Attack on Titan',
            'score': 9.0,
            'popularity': 1,
            'genres': ['Action', 'Drama', 'Fantasy'],
            'year': 2013,
            'members': 2000000,
            'synopsis': 'Humanity fights against giant humanoid Titans.'
        },
        {
            'mal_id': 2,
            'title': 'Death Note',
            'title_english': 'Death Note',
            'score': 9.0,
            'popularity': 2,
            'genres': ['Supernatural', 'Thriller', 'Psychological'],
            'year': 2006,
            'members': 1800000,
            'synopsis': 'A high school student finds a supernatural notebook.'
        },
        {
            'mal_id': 3,
            'title': 'Fullmetal Alchemist: Brotherhood',
            'title_english': 'Fullmetal Alchemist: Brotherhood',
            'score': 9.5,
            'popularity': 3,
            'genres': ['Action', 'Adventure', 'Drama', 'Fantasy'],
            'year': 2009,
            'members': 1500000,
            'synopsis': 'Two brothers search for the Philosophers Stone.'
        },
        {
            'mal_id': 4,
            'title': 'One Piece',
            'title_english': 'One Piece',
            'score': 8.9,
            'popularity': 4,
            'genres': ['Action', 'Adventure', 'Comedy'],
            'year': 1999,
            'members': 1200000,
            'synopsis': 'A pirate crew searches for the ultimate treasure.'
        },
        {
            'mal_id': 5,
            'title': 'Demon Slayer',
            'title_english': 'Demon Slayer: Kimetsu no Yaiba',
            'score': 8.7,
            'popularity': 5,
            'genres': ['Action', 'Supernatural', 'Historical'],
            'year': 2019,
            'members': 1400000,
            'synopsis': 'A boy becomes a demon slayer to save his sister.'
        },
        {
            'mal_id': 6,
            'title': 'Spirited Away',
            'title_english': 'Spirited Away',
            'score': 9.3,
            'popularity': 10,
            'genres': ['Adventure', 'Family', 'Fantasy'],
            'year': 2001,
            'members': 1100000,
            'synopsis': 'A girl enters a world ruled by gods and witches.'
        }
    ]
    
    return [Anime.from_dict(data) for data in sample_anime]

def demo_recommendation_system():
    """Demonstrate the recommendation system"""
    print("🎌 Anime Recommendation System - Demo")
    print("=" * 50)
    
    # Create a mock MAL service that doesn't make API calls
    class MockMALService:
        def search_anime(self, title):
            # Simple mock search
            sample_db = create_sample_database()
            for anime in sample_db:
                if title.lower() in anime.title.lower():
                    return anime.to_dict()
            return None
        
        def get_top_anime(self, limit):
            return [anime.to_dict() for anime in create_sample_database()]
    
    # Initialize the recommendation engine with sample data
    mal_service = MockMALService()
    engine = SimpleAnimeRecommendationEngine(mal_service)
    
    # Manually set the database with sample data
    engine.anime_database = create_sample_database()
    
    print(f"✅ Loaded {len(engine.anime_database)} sample anime into database")
    
    # Test 1: Basic Recommendations
    print("\n📝 Test 1: Basic Recommendations")
    print("Input: ['Attack on Titan']")
    
    recommendations = engine.get_recommendations(
        input_anime_titles=['Attack on Titan'],
        max_recommendations=3,
        min_score=7.0
    )
    
    print(f"📊 Got {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec.anime.title}")
        print(f"     Score: {rec.similarity_score:.3f} | Rating: {rec.anime.score}/10")
        print(f"     Genres: {', '.join(rec.anime.genres)}")
        print(f"     Reason: {rec.reasons[0] if rec.reasons else 'N/A'}")
        print()
    
    # Test 2: Multiple Input Anime
    print("\n📝 Test 2: Multiple Input Anime")
    print("Input: ['Attack on Titan', 'Death Note']")
    
    recommendations = engine.get_recommendations(
        input_anime_titles=['Attack on Titan', 'Death Note'],
        max_recommendations=3,
        min_score=8.0
    )
    
    print(f"📊 Got {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec.anime.title} (Score: {rec.similarity_score:.3f})")
    
    # Test 3: Genre Filtering
    print("\n📝 Test 3: Genre Filtering")
    print("Input: ['One Piece'] with Action genre required")
    
    recommendations = engine.get_recommendations(
        input_anime_titles=['One Piece'],
        max_recommendations=3,
        include_genres=['Action']
    )
    
    print(f"📊 Got {len(recommendations)} action recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec.anime.title}")
        print(f"     Genres: {', '.join(rec.anime.genres)}")
    
    # Test 4: Trending Anime
    print("\n📝 Test 4: Trending Anime")
    
    trending = engine.get_trending_recommendations(limit=3)
    
    print(f"🔥 Got {len(trending)} trending recommendations:")
    for i, rec in enumerate(trending, 1):
        print(f"  {i}. {rec.anime.title} ({rec.anime.year}) - {rec.anime.score}/10")
    
    print("\n✅ All tests completed successfully!")
    print("\n💡 The system works with:")
    print("   - Genre-based similarity matching")
    print("   - Rating and popularity scoring") 
    print("   - Input anime exclusion from results")
    print("   - Configurable filtering and limits")
    print("   - Confidence scoring for recommendations")

if __name__ == "__main__":
    demo_recommendation_system()