import requests
import json

BASE_URL = "https://anime-recommend-backend.vercel.app"

def test_input_sensitivity():
    """Test that different inputs produce genuinely different recommendations"""
    
    test_cases = [
        {
            "name": "Psychological Thriller (Death Note)",
            "anime_ids": [1535],  # Death Note
            "expected_themes": ["psychological", "thriller", "mystery", "drama", "suspense"]
        },
        {
            "name": "Slice of Life (K-On!)",
            "anime_ids": [5680],  # K-On!
            "expected_themes": ["slice of life", "music", "school", "comedy"]
        },
        {
            "name": "Mecha (Gundam)",
            "anime_ids": [80],    # Mobile Suit Gundam
            "expected_themes": ["mecha", "military", "space", "drama"]
        },
        {
            "name": "Horror (Another)",
            "anime_ids": [11111], # Another
            "expected_themes": ["horror", "mystery", "supernatural", "school"]
        }
    ]
    
    all_results = {}
    
    for test in test_cases:
        print(f"\n🧪 {test['name']}")
        print(f"Input: {test['anime_ids']}")
        
        payload = {
            "user_anime_list": test["anime_ids"],
            "max_recommendations": 5
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/recommendations", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    recs = data["recommendations"]
                    all_results[test["name"]] = recs
                    
                    print(f"✅ Got {len(recs)} recommendations:")
                    all_genres = set()
                    all_titles = []
                    
                    for i, rec in enumerate(recs, 1):
                        print(f"  {i}. {rec['title']}")
                        print(f"     Genres: {', '.join(rec['genres'])}")
                        print(f"     Similarity: {rec['similarity_score']}")
                        all_genres.update([g.lower() for g in rec['genres']])
                        all_titles.append(rec['title'])
                    
                    # Check theme matching
                    theme_matches = sum(1 for theme in test["expected_themes"] 
                                      if any(theme in genre for genre in all_genres))
                    
                    print(f"\n   📊 Theme Analysis:")
                    print(f"     Expected themes found: {theme_matches}/{len(test['expected_themes'])}")
                    print(f"     All genres: {', '.join(sorted(all_genres))}")
                    
                    if theme_matches >= len(test["expected_themes"]) * 0.5:
                        print("   ✅ Good theme matching")
                    else:
                        print("   ⚠️  Weak theme matching")
                        
                else:
                    print(f"❌ API Error: {data}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        print("="*60)
    
    # Cross-comparison analysis
    print("\n🔍 Cross-Comparison Analysis:")
    if len(all_results) >= 2:
        result_items = list(all_results.items())
        for i in range(len(result_items)):
            for j in range(i+1, len(result_items)):
                name1, recs1 = result_items[i]
                name2, recs2 = result_items[j]
                
                titles1 = {rec['title'] for rec in recs1}
                titles2 = {rec['title'] for rec in recs2}
                
                overlap = len(titles1.intersection(titles2))
                total_unique = len(titles1.union(titles2))
                diversity_score = 1 - (overlap / total_unique) if total_unique > 0 else 0
                
                print(f"  {name1} vs {name2}:")
                print(f"    Shared recommendations: {overlap}/{min(len(titles1), len(titles2))}")
                print(f"    Diversity score: {diversity_score:.2f} (higher = more different)")
                
                if diversity_score >= 0.7:
                    print("    ✅ Good diversity between inputs")
                elif diversity_score >= 0.4:
                    print("    🟡 Moderate diversity")
                else:
                    print("    ⚠️  Low diversity - results too similar")
                print()

if __name__ == "__main__":
    test_input_sensitivity()