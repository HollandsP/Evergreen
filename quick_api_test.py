#!/usr/bin/env python3
"""
Quick API test script - Test the API without browser
"""
import requests
import json

API_BASE = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            except:
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Response length: {len(response.text)} characters")
            if len(response.text) < 500:
                print(f"Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"\n{method} {endpoint}")
        print(f"Error: {e}")
        return False

def main():
    print("🔍 Testing AI Content Pipeline API...")
    
    # Test basic endpoints
    endpoints = [
        "/",
        "/health", 
        "/api/v1/openapi.json",
        "/api/v1/docs",
        "/api/v1/projects",
    ]
    
    working = 0
    total = len(endpoints)
    
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            working += 1
    
    print(f"\n📊 Results: {working}/{total} endpoints working")
    
    if working >= 3:
        print("✅ API is operational!")
        print("\n🎯 Use these URLs:")
        print("   • Health: http://localhost:8000/health")
        print("   • API Schema: http://localhost:8000/api/v1/openapi.json")
        print("   • Docs: http://localhost:8000/api/v1/docs")
        print("   • Flower: http://localhost:5556 (admin/admin)")
    else:
        print("❌ API has issues")

if __name__ == "__main__":
    main()