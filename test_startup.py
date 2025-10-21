#!/usr/bin/env python3
"""
Quick test to verify the FastAPI app can start without crashing
Run this to test if Railway deployment will work
"""
import sys
import os
import requests
import time
from multiprocessing import Process

def start_server():
    """Start the FastAPI server in a separate process"""
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # Set minimal environment variables to avoid dependency failures
    os.environ.setdefault("REDIS_ENABLED", "false")

    # Import and run the app
    import uvicorn
    from api.main import app

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

def test_health_endpoint():
    """Test if the health endpoint responds"""
    # Start server in a separate process
    print("🚀 Starting test server on port 8001...")
    server_process = Process(target=start_server)
    server_process.start()

    # Give server time to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)

    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:8001/health", timeout=10)

        if response.status_code == 200:
            print("✅ SUCCESS: Health endpoint responded with 200 OK")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ FAILED: Health endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Could not connect to server: {e}")
        return False

    finally:
        # Terminate server process
        print("🛑 Stopping test server...")
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            server_process.kill()

if __name__ == "__main__":
    print("=" * 60)
    print("FastAPI Startup Test")
    print("=" * 60)

    success = test_health_endpoint()

    print("=" * 60)
    if success:
        print("✅ App can start successfully - Railway deployment should work")
        sys.exit(0)
    else:
        print("❌ App failed to start - Railway deployment will likely fail")
        print("Check the error messages above for details")
        sys.exit(1)