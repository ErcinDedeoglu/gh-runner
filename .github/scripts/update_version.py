#!/usr/bin/env python3
import os
import sys
import json
import base64
import re
from typing import List, Dict
import requests

def get_version_parts(branch: str) -> tuple[str, str, str]:
    """Extract version parts from branch name."""
    pattern = r'^(v[0-9]+(\.[0-9]+)*)([-][a-zA-Z0-9._-]+)?$'
    match = re.match(pattern, branch)
    if match:
        version_part = match.group(1)
        suffix = match.group(3) or ''
        return version_part, version_part.lstrip('v'), suffix
    return 'v0.0', '0.0', ''

def generate_tags(version_nums: str, suffix: str, build_number: int) -> List[str]:
    """Generate Docker tags."""
    tags = []
    parts = version_nums.split('.')
    current = 'v'
    # Add incremental version tags
    for part in parts:
        current += part
        tags.append(f"{current}{suffix}")
        current += '.'
    # Add full version tag
    full_version = f"v{version_nums}.{build_number}{suffix}"
    tags.append(full_version)
    # Add latest or suffix tag
    tags.append(suffix.lstrip('-') if suffix else 'latest')
    return tags

def get_existing_version_file(headers: Dict, github_repo: str) -> tuple[str, Dict, str]:
    """Find the most recent version file in the repository."""
    url = f"https://api.github.com/repos/{github_repo}/contents"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json()
        version_files = [f for f in files if f['name'].startswith('version_') and f['name'].endswith('.json')]
        if version_files:
            # Get the latest version file
            latest_file = sorted(version_files, key=lambda x: x['name'])[-1]
            file_response = requests.get(latest_file['url'], headers=headers)
            if file_response.status_code == 200:
                content = json.loads(base64.b64decode(file_response.json()['content']))
                return latest_file['name'], content, file_response.json()['sha']
    return None, None, None

def main():
    # Get environment variables
    github_token = os.environ['GH_TOKEN']
    github_repo = os.environ['GITHUB_REPOSITORY']
    branch = os.environ['GITHUB_REF'].replace('refs/heads/', '')

    # Get version information
    version_part, version_nums, suffix = get_version_parts(branch)
    print(f"Branch: {branch}")
    print(f"Version part: {version_part}")
    print(f"Suffix: {suffix}")

    # Setup API
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get existing version file if it exists
    _, existing_content, _ = get_existing_version_file(headers, github_repo)
    build_number = (existing_content['build_number'] + 1) if existing_content else 1

    # Generate version information
    full_version = f"{version_part}.{build_number}{suffix}"
    tags = generate_tags(version_nums, suffix, build_number)

    # Create version file content
    version_data = {
        'branch': branch,
        'build_number': build_number,
        'version': full_version,
        'tags': tags
    }

    # Create new version file
    new_filename = f"version_{full_version}.json"
    url = f"https://api.github.com/repos/{github_repo}/contents/{new_filename}"
    
    content = base64.b64encode(json.dumps(version_data, indent=2).encode()).decode()
    data = {
        'message': f'Update version to {full_version}',
        'content': content,
    }

    response = requests.put(url, headers=headers, json=data)
    if not response.ok:
        print(f"Error updating file: {response.status_code}")
        print(response.text)
        sys.exit(1)

    # Set GitHub Actions outputs
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"full_version={full_version}\n")
        f.write("tags<<EOF\n")
        f.write(json.dumps(tags))
        f.write("\nEOF\n")

if __name__ == '__main__':
    main()