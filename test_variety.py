import requests

BASE_URL = "https://anime-recommend-backend.vercel.app"

def test_different_inputs():
    """Test with different types of anime to see recommendation variety"""
    
    test_cases = [
        {
            "name": "Romance Fan (Toradora)",
            "anime_ids": [2167],  # Toradora
        },
        {
            "name": "Comedy Fan (Konosuba)", 
            "anime_ids": [30831],  # Konosuba
        },
        {
            "name": "Sports Fan (Haikyuu)",
            "anime_ids": [20583],  # Haikyuu!!
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"Input: {test['anime_ids']}")
        
        payload = {
            "user_anime_list": test["anime_ids"],
            "max_recommendations": 6
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/recommendations", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    recs = data["recommendations"]
                    
                    print(f"✅ Got {len(recs)} recommendations:")
                    ranks = []
                    for i, rec in enumerate(recs, 1):
                        rank = rec.get('rank', 999999)
                        ranks.append(rank if rank != 999999 else None)
                        print(f"  {i}. {rec['title']} (Rank: {rank if rank != 999999 else 'Unranked'}, Score: {rec['score']}, Sim: {rec['similarity_score']})")
                        print(f"     Genres: {', '.join(rec['genres'][:3])}")
                    
                    # Analysis
                    valid_ranks = [r for r in ranks if r is not None]
                    top_50_count = len([r for r in valid_ranks if r <= 50])
                    unranked_count = ranks.count(None)
                    
                    print(f"\n   📊 Rank Analysis:")
                    print(f"     Top 50 MAL: {top_50_count}/{len(recs)}")
                    print(f"     Unranked/Lower: {unranked_count + len([r for r in valid_ranks if r > 50])}/{len(recs)}")
                    print(f"     Processing time: {data.get('processing_time', 'N/A')}s")
                    
                    if unranked_count > 0 or len([r for r in valid_ranks if r > 100]) > 0:
                        print("   ✅ Good diversity - includes less popular anime")
                    else:
                        print("   ⚠️  Still dominated by top MAL rankings")
                else:
                    print(f"❌ Error: {data}")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_different_inputs()