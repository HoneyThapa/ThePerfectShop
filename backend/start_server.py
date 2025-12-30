#!/usr/bin/env python3
"""
Start the backend server with proper error handling
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment")
        print("   Make sure .env file exists with GROQ_API_KEY=your_key_here")
        return False
    
    print(f"✅ GROQ_API_KEY found (length: {len(api_key)})")
    
    # Check if required modules are available
    try:
        import uvicorn
        import fastapi
        print("✅ FastAPI and Uvicorn available")
    except ImportError as e:
        print(f"❌ Missing required module: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def start_server():
    """Start the FastAPI server"""
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return False
    
    print("\n🚀 Starting FastAPI server...")
    print("   Backend will be available at: http://localhost:8000")
    print("   API documentation at: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = start_server()
    if not success:
        sys.exit(1)