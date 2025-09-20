"""
Test script for the Anime Recommendation API.
Tests various endpoints and functionality.
"""

import requests
import json
import time
from typing import Dict, Any

class APITester:
    """Test the Anime Recommendation API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        print("🔍 Testing health check endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed")
                print(f"   Status: {data.get('status')}")
                print(f"   Database size: {data.get('database_size')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_recommendations(self) -> bool:
        """Test the recommendations endpoint"""
        print("\n🔍 Testing recommendations endpoint...")
        
        test_cases = [
            {
                "name": "Basic recommendation test",
                "payload": {
                    "anime_titles": ["Attack on Titan", "Death Note"]
                }
            },
            {
                "name": "Recommendation with filters",
                "payload": {
                    "anime_titles": ["One Piece", "Naruto"],
                    "max_recommendations": 5,
                    "min_score": 8.0,
                    "exclude_genres": ["Horror"]
                }
            },
            {
                "name": "Single anime recommendation",
                "payload": {
                    "anime_titles": ["Demon Slayer"]
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/recommendations",
                    json=test_case['payload'],
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get('recommendations', [])
                    
                    print(f"  ✅ Got {len(recommendations)} recommendations")
                    print(f"     Processing time: {data.get('processing_time', 0):.2f}s")
                    print(f"     Input found: {data.get('input_anime_found', [])}")
                    
                    # Show top 3 recommendations
                    for i, rec in enumerate(recommendations[:3]):
                        print(f"     {i+1}. {rec.get('title')} (Score: {rec.get('similarity_score', 0):.3f})")
                
                else:
                    print(f"  ❌ Request failed: {response.status_code}")
                    print(f"     Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"  ❌ Request error: {e}")
                return False
        
        return True
    
    def test_trending(self) -> bool:
        """Test the trending endpoint"""
        print("\n🔍 Testing trending endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/trending?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                print(f"✅ Got {len(recommendations)} trending recommendations")
                
                for i, rec in enumerate(recommendations):
                    print(f"   {i+1}. {rec.get('title')} (Score: {rec.get('anime', {}).get('score', 0)}/10)")
                
                return True
            else:
                print(f"❌ Trending request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Trending request error: {e}")
            return False
    
    def test_search(self) -> bool:
        """Test the search endpoint"""
        print("\n🔍 Testing search endpoint...")
        
        test_queries = [
            "Attack on Titan",
            "Fullmetal Alchemist",
            "One Piece"
        ]
        
        for query in test_queries:
            print(f"\n  Searching for: {query}")
            
            try:
                response = self.session.get(
                    f"{self.base_url}/api/anime/search",
                    params={'q': query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    anime = data.get('anime')
                    
                    if anime:
                        print(f"  ✅ Found: {anime.get('title')}")
                        print(f"     Score: {anime.get('score', 0)}/10")
                        print(f"     Genres: {', '.join(anime.get('genres', [])[:5])}")
                    else:
                        print(f"  ⚠️  No anime found")
                        
                elif response.status_code == 404:
                    print(f"  ⚠️  No anime found with query: {query}")
                    
                else:
                    print(f"  ❌ Search failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"  ❌ Search error: {e}")
                return False
        
        return True
    
    def test_database_stats(self) -> bool:
        """Test the database stats endpoint"""
        print("\n🔍 Testing database stats endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/database/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                print("✅ Database stats retrieved")
                print(f"   Total anime: {data.get('total_anime', 0)}")
                print(f"   Average score: {data.get('average_score', 0)}")
                
                top_genres = data.get('top_genres', [])[:5]
                print("   Top genres:")
                for genre, count in top_genres:
                    print(f"     - {genre}: {count}")
                
                return True
            else:
                print(f"❌ Database stats failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Database stats error: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        print("\n🔍 Testing error handling...")
        
        error_test_cases = [
            {
                "name": "Empty anime titles",
                "payload": {"anime_titles": []},
                "expected_status": 400
            },
            {
                "name": "Invalid anime titles type",
                "payload": {"anime_titles": "not a list"},
                "expected_status": 400
            },
            {
                "name": "Too many anime titles",
                "payload": {"anime_titles": [f"Anime {i}" for i in range(15)]},
                "expected_status": 400
            },
            {
                "name": "Invalid max_recommendations",
                "payload": {"anime_titles": ["Test"], "max_recommendations": -1},
                "expected_status": 400
            }
        ]
        
        for test_case in error_test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/recommendations",
                    json=test_case['payload'],
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == test_case['expected_status']:
                    print(f"  ✅ Correctly returned status {response.status_code}")
                else:
                    print(f"  ❌ Expected {test_case['expected_status']}, got {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"  ❌ Error test failed: {e}")
                return False
        
        return True
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("🧪 Starting API Tests")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Recommendations", self.test_recommendations),
            ("Trending", self.test_trending),
            ("Search", self.test_search),
            ("Database Stats", self.test_database_stats),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            
            start_time = time.time()
            result = test_func()
            elapsed = time.time() - start_time
            
            if result:
                print(f"✅ {test_name} PASSED ({elapsed:.2f}s)")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED ({elapsed:.2f}s)")
        
        print("\n" + "=" * 50)
        print(f"🧪 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("❌ Some tests failed")
            return False


def main():
    """Run the test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test the Anime Recommendation API')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the API (default: http://localhost:5000)')
    parser.add_argument('--wait', type=int, default=10,
                       help='Seconds to wait for server startup (default: 10)')
    
    args = parser.parse_args()
    
    # Wait for server to be ready
    print(f"⏳ Waiting {args.wait} seconds for server to be ready...")
    time.sleep(args.wait)
    
    tester = APITester(args.url)
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())