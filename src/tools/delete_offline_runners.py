import requests
import sys
from github_utils import identify_url_type, get_base_url, create_headers

def list_runners(url_type, base_url, headers):
    if url_type == "repo":
        api_url = f"https://api.github.com/repos/{base_url}/actions/runners"
    else:
        api_url = f"https://api.github.com/orgs/{base_url}/actions/runners"
    
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json().get("runners", [])
    else:
        print(f"Failed to list runners: {response.status_code} - {response.text}")
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

    for runner in runners:
        if runner["status"] == "offline":
            delete_runner(url_type, base_url, runner["id"], headers)

if __name__ == "__main__":
    main()