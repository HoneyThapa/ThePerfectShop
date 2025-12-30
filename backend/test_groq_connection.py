#!/usr/bin/env python3
"""
Test Groq API connection directly
"""

import httpx
import json

GROQ_API_KEY = "your_groq_api_key_here"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

def test_groq_direct():
    """Test Groq API directly"""
    print("🔍 Testing Groq API connection directly...")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "user", "content": "Say hello in JSON format: {\"message\": \"hello\"}"}
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ Error Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_groq_without_json_format():
    """Test without JSON format requirement"""
    print("\n🔍 Testing Groq API without JSON format...")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "user", "content": "Say hello"}
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                message = data["choices"][0]["message"]["content"]
                print(f"✅ Success! Message: {message}")
                return True
            else:
                print(f"❌ Error Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Groq API Connection")
    print("=" * 40)
    
    test1 = test_groq_direct()
    test2 = test_groq_without_json_format()
    
    if test1 or test2:
        print("\n✅ Groq API is working!")
    else:
        print("\n❌ Groq API connection failed!")