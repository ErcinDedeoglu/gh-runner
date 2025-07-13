import requests
import sys
from github_utils import identify_url_type, get_base_url, create_headers

def list_runners(url_type, base_url, headers):
    if url_type == "repo":
        api_url = f"https://api.github.com/repos/{base_url}/actions/runners"
    else:
        api_url = f"https://api.github.com/orgs/{base_url}/actions/runners"
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("runners", [])
    except requests.exceptions.RequestException as e:
        print(f"Failed to list runners: {e}")
        return []

def delete_runner(url_type, base_url, runner_id, headers):
    if url_type == "repo":
        api_url = f"https://api.github.com/repos/{base_url}/actions/runners/{runner_id}"
    else:
        api_url = f"https://api.github.com/orgs/{base_url}/actions/runners/{runner_id}"
    
    response = requests.delete(api_url, headers=headers)
    if response.status_code == 204:
        print(f"Successfully deleted runner with ID {runner_id}.")
    else:
        print(f"Failed to delete runner with ID {runner_id}: {response.status_code} - {response.text}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python delete_offline_runners.py <url> <personal_access_token>")
        return

    url = sys.argv[1]
    personal_access_token = sys.argv[2]
    
    base_url = get_base_url(url)
    url_type = identify_url_type(url)
    headers = create_headers(personal_access_token)

    runners = list_runners(url_type, base_url, headers)
    if not runners:
        print("No runners found.")
        return

    from datetime import datetime, timedelta, timezone

    def extract_runner_timestamp(runner_name):
        """Extract timestamp as datetime object from runner name.
        Example runner name: gh-runner-3-w7vflbxl-20250503082101
        Timestamp: 20250503082101 (last dash-delimited part)
        """
        parts = runner_name.split("-")
        if len(parts) < 2:
            return None
        ts_str = parts[-1]
        try:
            dt = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
            return dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            print(f"Could not parse timestamp from runner name {runner_name}: {e}")
            return None

    now = datetime.now(timezone.utc)
    for runner in runners:
        print(f"Runner: {runner['name']}, Status: {runner['status']}, Extracted timestamp: {extract_runner_timestamp(runner['name'])}")
        if runner["status"] == "offline":
            runner_dt = extract_runner_timestamp(runner["name"])
            if runner_dt is not None:
                age = now - runner_dt
                if age < timedelta(minutes=10):
                    print(f"Skipping deletion of runner {runner['name']} (offline for less than 10 minutes)")
                    continue
            delete_runner(url_type, base_url, runner["id"], headers)

if __name__ == "__main__":
    main()