#!/usr/bin/env python3
import os
import subprocess
import logging
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

def main():
    """Main function to orchestrate SBOM generation."""
    try:
        setup_output_directory()
        docker_login()
        generate_sbom()
    except Exception as e:
        logger.error(f"SBOM generation failed: {e}")
        raise

if __name__ == "__main__":
    main()