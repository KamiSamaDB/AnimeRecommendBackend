import requests
import json

BASE_URL = "https://anime-recommend-backend.vercel.app"

def simple_test():
    """Simple test of the recommendation system"""
    print("🧪 Testing New Recommendation Algorithm...")
    
    # Test with Death Note (psychological thriller)
    payload = {
        "user_anime_list": [1535],  # Death Note
        "max_recommendations": 5
    }
    
    try:
        print("Sending request...")
        response = requests.post(f"{BASE_URL}/api/recommendations", json=payload, timeout=45)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API status: {data.get('status')}")
            
            if data["status"] == "success":
                recommendations = data["recommendations"]
                print(f"✅ Got {len(recommendations)} recommendations")
                
                print("\n📋 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"  {i}. {rec['title']}")
                    print(f"     Score: {rec['score']}, Similarity: {rec['similarity_score']}")
                    print(f"     Genres: {', '.join(rec['genres'][:4])}")
                    print(f"     Reason: {rec['reason']}")
                    print(f"     Rank: {rec.get('rank', 'N/A')}")
                    print()
                
                # Check diversity
                all_genres = set()
                ranks = []
                for rec in recommendations:
                    all_genres.update(rec['genres'])
                    if rec.get('rank'):
                        ranks.append(rec['rank'])
                
                print(f"📊 Analysis:")
                print(f"   Total unique genres: {len(all_genres)}")
                print(f"   Genre variety: {', '.join(list(all_genres)[:8])}")
                print(f"   MAL ranks: {ranks}")
                print(f"   Processing time: {data.get('processing_time', 'N/A')} seconds")
                
                # Success indicators
                if len(all_genres) >= 3:
                    print("   ✅ Good genre diversity")
                
                top_ranks = [r for r in ranks if r <= 50]
                if len(top_ranks) < len(ranks):
                    print("   ✅ Not just top MAL anime")
                else:
                    print("   ⚠️  Still mostly top MAL anime")
                    
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    simple_test()