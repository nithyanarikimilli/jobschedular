import sys
import os
import requests
import redis
from sqlalchemy import create_engine, text

# Add backend directory to system path
root_path = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(root_path, "backend")
sys.path.append(backend_path)

from app.core.config import settings

def verify():
    print("====================================================")
    print("          SmartQueue Startup Verification            ")
    print("====================================================")
    
    # 1. Check PostgreSQL
    print("1. Checking PostgreSQL connection...", end="", flush=True)
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(" [OK]")
    except Exception as e:
        print(f" [FAILED]\nError: {e}")
        print("\nEnsure PostgreSQL is running and DATABASE_URL in .env is correct.")
        return False
        
    # 2. Check Database Tables
    print("2. Checking database tables...", end="", flush=True)
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )).fetchall()
            tables = [r[0] for r in result]
        required = ["users", "organizations", "projects", "queues", "jobs", "workers"]
        missing = [t for t in required if t not in tables]
        if missing:
            print(f" [FAILED]\nMissing required tables: {missing}")
            print("Run seeder script or start the backend to initialize the schema.")
            return False
        else:
            print(" [OK]")
    except Exception as e:
        print(f" [FAILED]\nError: {e}")
        return False

    # 3. Check Redis
    print("3. Checking Redis connection...", end="", flush=True)
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
        print(" [OK]")
    except Exception as e:
        print(f" [FAILED]\nError: {e}")
        print("\nEnsure Redis is running and REDIS_URL in .env is correct.")
        return False

    # 4. Check Backend API
    print("4. Checking Backend API...", end="", flush=True)
    try:
        resp = requests.get("http://localhost:8000/health", timeout=3)
        if resp.status_code == 200 and resp.json().get("status") == "healthy":
            print(" [OK]")
        else:
            print(f" [FAILED] Status Code: {resp.status_code}")
            return False
    except Exception as e:
        print(" [WARNING] (Unreachable at http://localhost:8000/health)")
        print(f"Details: {e}")

    # 5. Check Frontend
    print("5. Checking Frontend Dashboard...", end="", flush=True)
    try:
        resp = requests.get("http://localhost:3000", timeout=3)
        if resp.status_code == 200:
            print(" [OK]")
        else:
            print(f" [FAILED] Status Code: {resp.status_code}")
    except Exception as e:
        print(" [WARNING] (Unreachable at http://localhost:3000)")

    print("\nSmartQueue verification completed successfully!")
    return True

if __name__ == "__main__":
    verify()
