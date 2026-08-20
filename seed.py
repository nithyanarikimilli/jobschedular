import sys
import os

# Resolve paths to backend
root_path = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(root_path, "backend")
sys.path.append(backend_path)

from app.seeder import seed_db

if __name__ == "__main__":
    print("SmartQueue Demo Seeder")
    seed_db()
