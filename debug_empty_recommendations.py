import requests
import json

BASE_URL = "https://anime-recommend-backend.vercel.app"

def test_empty_recommendations():
    """Test for empty recommendation arrays that might be affecting React app"""
    
    test_cases = [
        {"name": "Simple test", "anime_ids": [20]},  # Naruto
        {"name": "Multiple anime", "anime_ids": [20, 21]},  # Naruto + One Piece
        {"name": "Popular anime", "anime_ids": [1535]},  # Death Note
        {"name": "Recent anime", "anime_ids": [16498]},  # Attack on Titan
    ]
    
    for test in test_cases:
        print(f"\n🧪 {test['name']}: {test['anime_ids']}")
        
        payload = {
            "user_anime_list": test["anime_ids"],
            "max_recommendations": 5
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/recommendations", json=payload, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"API Status: {data.get('status')}")
                
                if data.get("status") == "success":
                    recs = data.get("recommendations", [])
                    print(f"Recommendations count: {len(recs)}")
                    
                    if len(recs) == 0:
                        print("❌ EMPTY RECOMMENDATIONS ARRAY!")
                        print(f"Error details: {data}")
                    else:
                        print("✅ Got recommendations:")
                        for i, rec in enumerate(recs[:3], 1):
                            rating = rec.get('rating', 'Unknown')
                            print(f"  {i}. {rec['title']} - Rating: {rating}")
                            print(f"     Genres: {', '.join(rec['genres'][:3])}")
                            
                            # Check for NSFW indicators
                            nsfw_indicators = ['R+', 'Rx', 'Hentai', 'Ecchi']
                            if any(indicator.lower() in rating.lower() for indicator in nsfw_indicators):
                                print(f"     ⚠️ NSFW CONTENT DETECTED: {rating}")
                else:
                    print(f"❌ API Error: {data}")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        print("="*50)

if __name__ == "__main__":
    test_empty_recommendations()