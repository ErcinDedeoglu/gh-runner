import requests
import sys
from github_utils import identify_url_type, get_base_url, create_headers

def get_runner_token(url_type, base_url, headers):
    """Get runner registration token from GitHub API."""
    if url_type == "repo":
        api_url = f"https://api.github.com/repos/{base_url}/actions/runners/registration-token"
    else:
        api_url = f"https://api.github.com/orgs/{base_url}/actions/runners/registration-token"
    
    response = requests.post(api_url, headers=headers)
    
    if response.status_code == 201:
        return response.json().get("token")
    else:
        print(f"Error getting runner token: {response.status_code} - {response.text}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python get_runner_token.py <url> <personal_access_token>")
        sys.exit(1)

    url = sys.argv[1]
    personal_access_token = sys.argv[2]

    base_url = get_base_url(url)
    url_type = identify_url_type(url)
    headers = create_headers(personal_access_token)

    token = get_runner_token(url_type, base_url, headers)
    
    if token:
        print(token)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()