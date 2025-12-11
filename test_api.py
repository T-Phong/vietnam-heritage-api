"""
Test script để kiểm tra ứng dụng cục bộ
Chạy: python test_api.py
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if GROQ_API_KEY is set
if not os.environ.get('GROQ_API_KEY'):
    print("❌ ERROR: GROQ_API_KEY not found in .env")
    print("Please create .env file with GROQ_API_KEY=your_key")
    sys.exit(1)

print("✅ GROQ_API_KEY found")

# Test local Flask server
BASE_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("\n📋 Testing GET /health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed:", response.json())
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Flask is running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_home():
    """Test home endpoint"""
    print("\n📋 Testing GET /...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Home endpoint:", json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Home endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ask(question="Nguyễn Trãi là ai?"):
    """Test ask endpoint"""
    print(f"\n📋 Testing POST /ask with question: '{question}'")
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"question": question},
            timeout=300  # 5 minutes timeout for first request
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Question:", data.get('question'))
            print("✅ Answer:", data.get('answer'))
            return True
        else:
            print(f"❌ Ask endpoint failed: {response.status_code}")
            print("Response:", response.text)
            return False
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (first request takes 30-60s due to model loading)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Flask is running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_request():
    """Test invalid request handling"""
    print("\n📋 Testing POST /ask with invalid request...")
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"invalid_field": "test"},
            timeout=5
        )
        if response.status_code == 400:
            print("✅ Invalid request correctly rejected:", response.json())
            return True
        else:
            print(f"❌ Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Vietnam Heritage API - Local Test Suite")
    print("=" * 60)
    print("\n⚠️  Make sure Flask server is running:")
    print("   Run: python app.py")
    print("\n")
    
    results = []
    
    # Test health
    results.append(("Health Check", test_health()))
    
    # Test home
    results.append(("Home Endpoint", test_home()))
    
    # Test invalid request
    results.append(("Invalid Request Handling", test_invalid_request()))
    
    # Test ask (takes longer due to model loading)
    results.append(("Ask Endpoint", test_ask()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
