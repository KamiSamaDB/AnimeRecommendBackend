import requests
import json

BASE_URL = "https://anime-recommend-backend.vercel.app"

def test_react_compatibility():
    """Test API response format and potential React app issues"""
    
    # Test the exact format that React app might be expecting
    test_payload = {
        "user_anime_list": [20],  # Naruto
        "max_recommendations": 10
    }
    
    print("🧪 Testing React App Compatibility...")
    print(f"Request payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/recommendations", 
            json=test_payload,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=30
        )
        
        print(f"\n📡 Response Details:")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        print(f"Content-Length: {response.headers.get('content-length', 'Not specified')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ JSON Response Structure:")
                print(f"Keys: {list(data.keys())}")
                print(f"Status: {data.get('status')}")
                print(f"Recommendations type: {type(data.get('recommendations'))}")
                print(f"Recommendations count: {len(data.get('recommendations', []))}")
                
                # Check if recommendations is actually an array
                recommendations = data.get('recommendations')
                if isinstance(recommendations, list):
                    print(f"✅ Recommendations is a proper array")
                    
                    if len(recommendations) > 0:
                        print(f"✅ Array contains {len(recommendations)} items")
                        
                        # Check first recommendation structure
                        first_rec = recommendations[0]
                        print(f"\n📋 First Recommendation Structure:")
                        for key, value in first_rec.items():
                            print(f"  {key}: {type(value)} = {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                            
                    else:
                        print("❌ EMPTY RECOMMENDATIONS ARRAY!")
                        print("This would cause React app to show no results")
                        
                else:
                    print(f"❌ Recommendations is not an array: {type(recommendations)}")
                    
                # Print full response for debugging
                print(f"\n📄 Full Response (first 500 chars):")
                response_text = json.dumps(data, indent=2)
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Decode Error: {e}")
                print(f"Raw response: {response.text[:200]}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request Exception: {e}")
        
    # Test CORS headers
    print(f"\n🔗 CORS Headers Check:")
    cors_headers = [
        'access-control-allow-origin',
        'access-control-allow-methods', 
        'access-control-allow-headers'
    ]
    
    for header in cors_headers:
        value = response.headers.get(header, 'Not present')
        print(f"  {header}: {value}")

if __name__ == "__main__":
    test_react_compatibility()