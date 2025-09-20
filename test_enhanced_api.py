import requests
import json

# Test the enhanced API with new data fields
BASE_URL = "https://anime-recommend-backend.vercel.app"

def test_search():
    print("Testing search endpoint...")
    response = requests.get(f"{BASE_URL}/api/search", params={"q": "naruto", "limit": 1})
    data = response.json()
    
    if response.status_code == 200 and data["status"] == "success":
        result = data["results"][0]
        print("✓ Search successful")
        print(f"Title: {result['title']}")
        print(f"Rank: {result.get('rank', 'N/A')}")
        print(f"Popularity: {result.get('popularity', 'N/A')}")
        print(f"Members: {result.get('members', 'N/A'):,}" if result.get('members') else "Members: N/A")
        print(f"Favorites: {result.get('favorites', 'N/A'):,}" if result.get('favorites') else "Favorites: N/A")
        print(f"Studios: {', '.join(result.get('studios', []))}")
        print(f"Episodes: {result.get('episodes', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print()
    else:
        print(f"✗ Search failed: {data}")
        print()

def test_recommendations():
    print("Testing recommendations endpoint...")
    payload = {
        "user_anime_list": [20],  # Naruto
        "max_recommendations": 2
    }
    
    response = requests.post(f"{BASE_URL}/api/recommendations", json=payload)
    data = response.json()
    
    if response.status_code == 200 and data["status"] == "success":
        print("✓ Recommendations successful")
        for i, rec in enumerate(data["recommendations"][:1], 1):
            print(f"\nRecommendation {i}:")
            print(f"  Title: {rec['title']}")
            print(f"  Rank: {rec.get('rank', 'N/A')}")
            print(f"  Popularity: {rec.get('popularity', 'N/A')}")
            print(f"  Members: {rec.get('members', 'N/A'):,}" if rec.get('members') else "  Members: N/A")
            print(f"  Favorites: {rec.get('favorites', 'N/A'):,}" if rec.get('favorites') else "  Favorites: N/A")
            print(f"  Similarity Score: {rec['similarity_score']}")
            print(f"  Studios: {', '.join(rec.get('studios', []))}")
            print(f"  Episodes: {rec.get('episodes', 'N/A')}")
        print()
    else:
        print(f"✗ Recommendations failed: {data}")
        print()

def test_trending():
    print("Testing trending endpoint...")
    response = requests.get(f"{BASE_URL}/api/trending", params={"limit": 1})
    data = response.json()
    
    if response.status_code == 200 and data["status"] == "success":
        result = data["trending"][0]
        print("✓ Trending successful")
        print(f"Title: {result['title']}")
        print(f"Rank: {result.get('rank', 'N/A')}")
        print(f"Popularity: {result.get('popularity', 'N/A')}")
        print(f"Members: {result.get('members', 'N/A'):,}" if result.get('members') else "Members: N/A")
        print(f"Favorites: {result.get('favorites', 'N/A'):,}" if result.get('favorites') else "Favorites: N/A")
        print(f"Studios: {', '.join(result.get('studios', []))}")
        print(f"Episodes: {result.get('episodes', 'N/A')}")
        print()
    else:
        print(f"✗ Trending failed: {data}")
        print()

if __name__ == "__main__":
    test_search()
    test_recommendations()
    test_trending()