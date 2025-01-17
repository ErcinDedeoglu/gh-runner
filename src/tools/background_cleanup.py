import time
import sys
from delete_offline_runners import main as cleanup_runners
from datetime import datetime

def run_periodic_cleanup():
    while True:
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{current_time} - Running scheduled cleanup...")
            cleanup_runners()
            time.sleep(300)
        except Exception as e:
            print(f"Error during cleanup: {e}", file=sys.stderr)
            time.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python background_cleanup.py <url> <personal_access_token>")
        sys.exit(1)
    
    run_periodic_cleanup()