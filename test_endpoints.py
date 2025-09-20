import requests
import json

def test_all_endpoints():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing All API Endpoints")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1️⃣ Testing Root Endpoint (GET /):")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Health endpoint
    print("\n2️⃣ Testing Health Endpoint (GET /health):")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Recommendations endpoint
    print("\n3️⃣ Testing Recommendations Endpoint (POST /api/recommendations):")
    try:
        payload = {
            "anime_titles": ["Attack on Titan"]
        }
        response = requests.post(f"{base_url}/api/recommendations", json=payload)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: Got {len(data.get('recommendations', []))} recommendations")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Search endpoint
    print("\n4️⃣ Testing Search Endpoint (GET /api/anime/search):")
    try:
        response = requests.get(f"{base_url}/api/anime/search?q=Naruto")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            anime = data.get('data', {}).get('anime')
            if anime:
                print(f"   Success: Found '{anime.get('title', 'Unknown')}'")
            else:
                print(f"   No anime found")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Trending endpoint
    print("\n5️⃣ Testing Trending Endpoint (GET /api/trending):")
    try:
        response = requests.get(f"{base_url}/api/trending?limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            recs = data.get('data', {}).get('recommendations', [])
            print(f"   Success: Got {len(recs)} trending anime")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Endpoint testing completed!")
    print("\n💡 If you see '404 Endpoint not found', please:")
    print("   1. Make sure the server is running")
    print("   2. Check you're using the correct URL")
    print("   3. Verify the endpoint path is correct")

if __name__ == "__main__":
    test_all_endpoints()