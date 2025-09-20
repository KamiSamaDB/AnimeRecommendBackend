import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    print("Testing Anime Recommendation API...")
    print("=" * 40)
    
    # Test health endpoint
    print("\n1. Testing Health Check:")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test search endpoint
    print("\n2. Testing Search:")
    try:
        response = requests.get(f"{base_url}/api/anime/search?q=Naruto")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found: {data.get('data', {}).get('anime', {}).get('title', 'No title')}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test recommendations endpoint
    print("\n3. Testing Recommendations:")
    try:
        payload = {
            "anime_titles": ["Attack on Titan", "Death Note"]
        }
        response = requests.post(f"{base_url}/api/recommendations", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            recs = data.get('data', {}).get('recommendations', [])
            print(f"Got {len(recs)} recommendations")
            for i, rec in enumerate(recs[:3], 1):
                print(f"  {i}. {rec.get('title', 'Unknown')}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()