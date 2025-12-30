#!/usr/bin/env python3
"""
Test available Groq models
"""

import httpx
import json

import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

def test_models():
    """Test different Groq models"""
    print("🔍 Testing available Groq models...")
    
    # Common Groq models to try
    models_to_test = [
        "llama-3.1-8b-instant",
        "llama-3.2-1b-preview",
        "llama-3.2-3b-preview", 
        "llama3-8b-8192",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it"
    ]
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    working_models = []
    
    for model in models_to_test:
        print(f"\n🧪 Testing model: {model}")
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Say hello"}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{GROQ_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    message = data["choices"][0]["message"]["content"]
                    print(f"✅ {model}: {message.strip()}")
                    working_models.append(model)
                else:
                    error_data = response.json()
                    print(f"❌ {model}: {error_data.get('error', {}).get('message', 'Unknown error')}")
                    
        except Exception as e:
            print(f"❌ {model}: Connection error - {e}")
    
    return working_models

if __name__ == "__main__":
    print("🚀 Testing Groq Models")
    print("=" * 40)
    
    working = test_models()
    
    print(f"\n📊 Results:")
    print(f"Working models: {len(working)}")
    for model in working:
        print(f"  ✅ {model}")
    
    if working:
        print(f"\n🎯 Recommended model: {working[0]}")
    else:
        print("\n❌ No working models found!")