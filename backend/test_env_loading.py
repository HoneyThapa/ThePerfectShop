#!/usr/bin/env python3
"""
Test environment variable loading
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_loading():
    """Test if environment variables are loaded correctly"""
    print("🔍 Testing environment variable loading...")
    
    # Check if GROQ_API_KEY is loaded
    api_key = os.getenv("GROQ_API_KEY")
    
    if api_key:
        print(f"✅ GROQ_API_KEY loaded successfully")
        print(f"   Key starts with: {api_key[:10]}...")
        print(f"   Key length: {len(api_key)} characters")
        return True
    else:
        print("❌ GROQ_API_KEY not found in environment")
        print("   Make sure .env file exists in backend directory")
        print("   Make sure .env file contains: GROQ_API_KEY=your_key_here")
        return False

if __name__ == "__main__":
    print("🚀 Environment Variable Test")
    print("=" * 40)
    
    success = test_env_loading()
    
    if success:
        print("\n✅ Environment setup is working correctly!")
    else:
        print("\n❌ Environment setup needs fixing!")