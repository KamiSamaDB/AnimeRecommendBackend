# Example usage script for the Anime Recommendation API

import requests
import json

# API base URL
BASE_URL = "http://localhost:5000"

def test_recommendations():
    """Test the recommendations endpoint with example data"""
    
    print("🎌 Anime Recommendation API - Example Usage")
    print("=" * 50)
    
    # Example 1: Basic recommendation
    print("\n📝 Example 1: Basic Recommendations")
    payload = {
        "anime_titles": ["Attack on Titan", "Death Note", "One Piece"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/recommendations", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data['recommendations']
            
            print(f"✅ Got {len(recommendations)} recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec['title']}")
                print(f"     Score: {rec['similarity_score']:.3f} | Rating: {rec['score']}/10")
                print(f"     Genres: {', '.join(rec['genres'][:3])}")
                print(f"     Reason: {rec['reasons'][0] if rec['reasons'] else 'N/A'}")
                print()
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # Example 2: Filtered recommendations
    print("\n📝 Example 2: Filtered Recommendations")
    payload = {
        "anime_titles": ["Demon Slayer", "Jujutsu Kaisen"],
        "max_recommendations": 5,
        "min_score": 8.0,
        "include_genres": ["Action"],
        "exclude_genres": ["Horror", "Ecchi"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/recommendations", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data['recommendations']
            
            print(f"✅ Got {len(recommendations)} filtered recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['title']} - {rec['score']}/10")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

    # Example 3: Search anime
    print("\n📝 Example 3: Search Anime")
    search_queries = ["Fullmetal Alchemist", "Studio Ghibli", "Spirited Away"]
    
    for query in search_queries:
        try:
            response = requests.get(f"{BASE_URL}/api/anime/search", params={"q": query})
            
            if response.status_code == 200:
                data = response.json()
                anime = data['anime']
                
                if anime:
                    print(f"🔍 Found: {anime['title']}")
                    print(f"   Score: {anime['score']}/10 | Episodes: {anime['episodes']}")
                    print(f"   Genres: {', '.join(anime['genres'][:4])}")
                else:
                    print(f"❌ No anime found for: {query}")
            else:
                print(f"❌ Search error for '{query}': {response.status_code}")
                
        except Exception as e:
            print(f"❌ Search error: {e}")

    # Example 4: Get trending anime
    print("\n📝 Example 4: Trending Anime")
    try:
        response = requests.get(f"{BASE_URL}/api/trending?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data['recommendations']
            
            print("🔥 Trending anime:")
            for i, rec in enumerate(recommendations, 1):
                anime = rec['anime'] if 'anime' in rec else rec
                print(f"  {i}. {anime.get('title', 'Unknown')}")
                print(f"     Rating: {anime.get('score', 0)}/10")
        else:
            print(f"❌ Trending error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Trending error: {e}")

if __name__ == "__main__":
    test_recommendations()