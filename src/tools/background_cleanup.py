import time
import sys
import os
from delete_offline_runners import main as cleanup_runners
from datetime import datetime

def run_periodic_cleanup():
    url = sys.argv[1]
    token = sys.argv[2]
    
    print(f"Starting background cleanup service for {url}")
    sys.stdout.flush()
    
    while True:
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{current_time} - Running scheduled cleanup...", flush=True)
            
            # Pass arguments explicitly instead of mutating sys.argv
            import subprocess
            # Construct the path to the delete_offline_runners.py script
            script_path = os.path.join(os.path.dirname(__file__), 'delete_offline_runners.py')
            subprocess.run([sys.executable, script_path, url, token],
                           check=True, stdout=sys.stdout, stderr=sys.stderr)
            
            time.sleep(300)
            
        except Exception as e:
            print(f"Error during cleanup: {e}", file=sys.stderr, flush=True)
            time.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python background_cleanup.py <url> <personal_access_token>")
        sys.exit(1)
    
    run_periodic_cleanup()