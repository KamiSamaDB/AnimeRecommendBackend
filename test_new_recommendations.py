import requests
import json

BASE_URL = "https://anime-recommend-backend.vercel.app"

def test_recommendation_diversity():
    """Test that recommendations are diverse and not just top MAL anime"""
    print("=== Testing Recommendation Algorithm Diversity ===\n")
    
    test_cases = [
        {
            "name": "Action/Adventure Fan (Naruto + One Piece)",
            "user_anime_list": [20, 21],  # Naruto, One Piece
            "expected_genres": ["Action", "Adventure", "Fantasy"]
        },
        {
            "name": "Romance/Drama Fan (Clannad + Your Name)", 
            "user_anime_list": [2167, 32281],  # Clannad, Your Name
            "expected_genres": ["Romance", "Drama", "Slice of Life"]
        },
        {
            "name": "Psychological Thriller Fan (Death Note + Steins;Gate)",
            "user_anime_list": [1535, 9253],  # Death Note, Steins;Gate
            "expected_genres": ["Psychological", "Thriller", "Sci-Fi"]
        },
        {
            "name": "Single Anime Test (Attack on Titan)",
            "user_anime_list": [16498],  # Attack on Titan
            "expected_genres": ["Action", "Drama"]
        }
    ]
    
    for test_case in test_cases:
        print(f"🧪 Testing: {test_case['name']}")
        print(f"Input anime IDs: {test_case['user_anime_list']}")
        
        payload = {
            "user_anime_list": test_case["user_anime_list"],
            "max_recommendations": 8
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/recommendations", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    recommendations = data["recommendations"]
                    
                    print(f"✅ Got {len(recommendations)} recommendations")
                    
                    # Check diversity metrics
                    unique_genres = set()
                    unique_studios = set()
                    score_ranges = {"high": 0, "medium": 0, "low": 0}
                    popularity_ranges = {"very_popular": 0, "popular": 0, "niche": 0}
                    
                    print("\n📋 Recommendations:")
                    for i, rec in enumerate(recommendations[:5], 1):
                        print(f"  {i}. {rec['title']} (Score: {rec['score']}, Similarity: {rec['similarity_score']})")
                        print(f"     Genres: {', '.join(rec['genres'][:3])}")
                        print(f"     Reason: {rec['reason']}")
                        print(f"     Rank: {rec.get('rank', 'N/A')}, Popularity: {rec.get('popularity', 'N/A')}")
                        
                        # Collect metrics
                        unique_genres.update(rec['genres'])
                        unique_studios.update(rec['studios'])
                        
                        # Score categorization
                        score = rec.get('score', 0)
                        if score >= 8.5:
                            score_ranges["high"] += 1
                        elif score >= 7.5:
                            score_ranges["medium"] += 1
                        else:
                            score_ranges["low"] += 1
                        
                        # Popularity categorization
                        pop = rec.get('popularity', 999999)
                        if pop <= 100:
                            popularity_ranges["very_popular"] += 1
                        elif pop <= 1000:
                            popularity_ranges["popular"] += 1
                        else:
                            popularity_ranges["niche"] += 1
                        
                        print()
                    
                    # Diversity analysis
                    print(f"📊 Diversity Analysis:")
                    print(f"   Unique genres found: {len(unique_genres)} ({', '.join(list(unique_genres)[:8])})")
                    print(f"   Unique studios: {len(unique_studios)}")
                    print(f"   Score distribution - High(8.5+): {score_ranges['high']}, Medium(7.5-8.5): {score_ranges['medium']}, Lower(<7.5): {score_ranges['low']}")
                    print(f"   Popularity spread - Very Popular(≤100): {popularity_ranges['very_popular']}, Popular(≤1000): {popularity_ranges['popular']}, Niche(>1000): {popularity_ranges['niche']}")
                    
                    # Check if we're getting only top MAL anime (ranks 1-50)
                    top_mal_count = sum(1 for rec in recommendations if rec.get('rank', 999) <= 50)
                    print(f"   Top 50 MAL anime count: {top_mal_count}/{len(recommendations)} ({top_mal_count/len(recommendations)*100:.1f}%)")
                    
                    # Quality check
                    if len(unique_genres) >= 3:
                        print("   ✅ Good genre diversity")
                    else:
                        print("   ⚠️  Limited genre diversity")
                    
                    if top_mal_count < len(recommendations) * 0.8:
                        print("   ✅ Not dominated by top MAL anime")
                    else:
                        print("   ⚠️  Too many top MAL anime")
                    
                else:
                    print(f"❌ API Error: {data}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        print("\n" + "="*80 + "\n")

def test_algorithm_timing():
    """Test response time of new algorithm"""
    print("⏱️ Testing Algorithm Performance...")
    
    payload = {
        "user_anime_list": [20, 21, 1535],  # Naruto, One Piece, Death Note
        "max_recommendations": 10
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/recommendations", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                processing_time = data.get("processing_time", "N/A")
                print(f"✅ Processing time: {processing_time} seconds")
                if isinstance(processing_time, (int, float)) and processing_time < 10:
                    print("   ✅ Good performance")
                else:
                    print("   ⚠️  Slow performance")
            else:
                print(f"❌ API Error: {data}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    test_recommendation_diversity()
    test_algorithm_timing()