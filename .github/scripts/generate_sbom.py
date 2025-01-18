#!/usr/bin/env python3
import os
import subprocess
import logging
import base64
import requests
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_output_directory():
    """Create output directory for SBOM if it doesn't exist."""
    output_dir = Path('sbom_output')
    output_dir.mkdir(exist_ok=True)
    return output_dir

def docker_login():
    """Login to GitHub Container Registry."""
    try:
        github_token = os.environ['GITHUB_TOKEN']
        github_actor = os.environ['GITHUB_ACTOR']
        
        login_cmd = [
            'docker', 'login', 'ghcr.io',
            '-u', github_actor,
            '--password-stdin'
        ]
        
        subprocess.run(
            login_cmd,
            input=github_token.encode(),
            check=True,
            capture_output=True
        )
        logger.info("Successfully logged in to GitHub Container Registry")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to login to GitHub Container Registry: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        raise

def generate_sbom():
    """Generate SBOM using sbominify Docker container."""
    try:
        # Get required environment variables
        repo_owner = os.environ['GITHUB_REPOSITORY_OWNER'].lower()
        image_name = os.environ['IMAGE_NAME']
        full_version = os.environ['FULL_VERSION']
        
        # Construct image tag
        image_tag = f"ghcr.io/{repo_owner}/{image_name}:{full_version}"
        
        # Prepare Docker command for SBOM generation
        sbom_cmd = [
            'docker', 'run', '--rm',
            '-e', f'IMAGES={image_tag}',
            '-e', 'FILE_PREFIX=',
            '-e', 'FILE_SUFFIX=',
            '-e', 'FILE_NAME=sbom',
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '-v', f'{os.getcwd()}/sbom_output:/output',
            '-v', f'{os.environ["HOME"]}/.docker/config.json:/root/.docker/config.json:ro',
            'ghcr.io/dockforge/sbominify:latest'
        ]
        
        # Run SBOM generation
        subprocess.run(sbom_cmd, check=True)
        logger.info("Successfully generated SBOM")
        
        # List generated files
        output_dir = Path('sbom_output')
        logger.info("Generated SBOM files:")
        for file in output_dir.iterdir():
            logger.info(f"- {file.name}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate SBOM: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        raise

def upload_to_github(file_path: Path, github_path: str):
    """Upload a file to GitHub repository."""
    try:
        github_token = os.environ['GITHUB_TOKEN']
        repo = os.environ['GITHUB_REPOSITORY']
        ref = os.environ.get('GITHUB_SHA', 'main')  # Default to 'main' if SHA not available

        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # API base URL
        api_url = f'https://api.github.com/repos/{repo}/contents/{github_path}'

        # Read file content
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode()

        # Check if file exists
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            # File exists, get its SHA
            sha = response.json()['sha']
            exists = True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                exists = False
            else:
                raise

        # Prepare the request data
        data = {
            'message': f'Update {github_path}',
            'content': content,
            'branch': ref
        }

        if exists:
            data['sha'] = sha

        # Upload file
        response = requests.put(api_url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"Successfully uploaded {github_path}")

    except Exception as e:
        logger.error(f"Failed to upload {github_path}: {e}")
        raise

def main():
    """Main function to orchestrate SBOM generation and upload."""
    try:
        setup_output_directory()
        docker_login()
        generate_sbom()

        # Upload files to GitHub
        output_dir = Path('sbom_output')
        
        # Upload sbom.json to root
        json_file = output_dir / 'sbom.json'
        if json_file.exists():
            upload_to_github(json_file, 'sbom.json')

        # Create sbom directory and upload sbom.txt
        txt_file = output_dir / 'sbom.txt'
        if txt_file.exists():
            upload_to_github(txt_file, 'sbom/sbom.txt')

    except Exception as e:
        logger.error(f"SBOM generation and upload failed: {e}")
        raise

if __name__ == "__main__":
    main()