#!/usr/bin/env python3
"""
Startup script for ThePerfectShop system
Starts both backend API and Streamlit UI
"""

import subprocess
import time
import sys
import os
import signal
import threading
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting Backend API Server...")
    try:
        # Start uvicorn server
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload"
        ], cwd=Path(__file__).parent)
        
        return backend_process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_ui():
    """Start the Streamlit UI"""
    print("🎨 Starting Streamlit UI...")
    try:
        # Start streamlit
        ui_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "ui_connected.py",
            "--server.port", "8501",
            "--server.address", "127.0.0.1"
        ], cwd=Path(__file__).parent)
        
        return ui_process
    except Exception as e:
        print(f"❌ Failed to start UI: {e}")
        return None

def check_backend_health():
    """Check if backend is healthy"""
    import requests
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🛒 ThePerfectShop System Startup")
    print("=" * 50)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend. Exiting.")
        return
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        if check_backend_health():
            print("✅ Backend is ready!")
            break
        time.sleep(1)
        print(f"   Checking... ({i+1}/30)")
    else:
        print("❌ Backend failed to start properly")
        backend_process.terminate()
        return
    
    # Start UI
    ui_process = start_ui()
    if not ui_process:
        print("❌ Failed to start UI")
        backend_process.terminate()
        return
    
    print("\n🎉 System Started Successfully!")
    print("=" * 50)
    print("🔗 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🎨 Streamlit UI: http://localhost:8501")
    print("\n💡 The UI will open automatically in your browser")
    print("⏹️  Press Ctrl+C to stop both servers")
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down system...")
        if backend_process:
            backend_process.terminate()
        if ui_process:
            ui_process.terminate()
        print("✅ System stopped")
        sys.exit(0)
    
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Keep the script running
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process died")
                break
            if ui_process.poll() is not None:
                print("❌ UI process died")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    # Cleanup
    if backend_process:
        backend_process.terminate()
    if ui_process:
        ui_process.terminate()

if __name__ == "__main__":
    main()