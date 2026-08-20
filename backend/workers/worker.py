import sys
import os
import time
import threading

# Add parent backend directory to system path
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from app.services.scheduler import WorkerRunner, run_scheduler_daemon
from app.core.database import Base, engine

if __name__ == "__main__":
    worker_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f"Starting SmartQueue Worker: {worker_name or 'Auto-named'}")
    
    # Ensure database schema is initialized
    Base.metadata.create_all(bind=engine)
    
    # Start the scheduler daemon (reclaims orphaned tasks & runs cron schedules)
    stop_event = threading.Event()
    daemon_thread = threading.Thread(target=run_scheduler_daemon, args=(stop_event,), daemon=True)
    daemon_thread.start()

    # Launch worker instance
    worker = WorkerRunner(name=worker_name)
    worker.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutdown signal received. Shutting down gracefully...")
        worker.stop()
        stop_event.set()
        daemon_thread.join()
        print("Shutdown complete.")
