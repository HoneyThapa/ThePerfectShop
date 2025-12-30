#!/usr/bin/env python3
"""
Quick local development server for ThePerfectShop Backend
Run this to test with frontend without Docker setup
"""

import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Set environment variables for local development
    os.environ.setdefault("SKIP_DB_HEALTH_CHECK", "true")
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("SECRET_KEY", "dev-secret-key-change-in-production")
    
    print("🚀 Starting ThePerfectShop Backend API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("\n⚠️  Note: Database features disabled for quick testing")
    print("💡 Use Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )