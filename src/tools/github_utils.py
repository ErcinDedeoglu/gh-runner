def identify_url_type(url):
    """Identify if the URL is for an organization or repository."""
    try:
        if "/" in url.split("github.com/")[1]:
            return "repo"
        return "org"
    except IndexError:
        raise ValueError("Invalid GitHub URL format")

def get_base_url(url):
    """Extract and clean base URL from GitHub URL."""
    try:
        base_url = url.split("github.com/")[1]
        return base_url.rstrip("/")
    except IndexError:
        raise ValueError("Invalid GitHub URL format")

def create_headers(personal_access_token):
    """Create standard headers for GitHub API requests."""
    return {
        "Authorization": f"Bearer {personal_access_token}",
        "Accept": "application/vnd.github.v3+json"
    }