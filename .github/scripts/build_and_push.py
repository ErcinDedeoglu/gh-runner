#!/usr/bin/env python3

import os
import subprocess
import json
import sys
from pathlib import Path

print("Script started...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Contents of current directory: {os.listdir('.')}")

class DockerBuildAndPush:
    def __init__(self):
        print("Initializing DockerBuildAndPush...")
        # Initialize with the exact environment variables from the workflow
        self.image_name = os.getenv("IMAGE_NAME")
        self.docker_username = os.getenv("DOCKER_USERNAME")
        self.docker_token = os.getenv("DOCKER_TOKEN")
        self.gh_token = os.getenv("GH_TOKEN")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.platforms = os.getenv("PLATFORMS")
        self.github_repository = os.getenv("GITHUB_REPOSITORY")
        self.github_actor = os.getenv("GITHUB_ACTOR")
        self.github_ref = os.getenv("GITHUB_REF")
        self.github_repository_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "").lower()
        
        print("Environment variables loaded:")
        print(f"IMAGE_NAME: {self.image_name}")
        print(f"PLATFORMS: {self.platforms}")
        print(f"GITHUB_REPOSITORY: {self.github_repository}")
        print(f"GITHUB_ACTOR: {self.github_actor}")

    def run_command(self, command, shell=True, env=None):
        """Execute a command and handle its output"""
        if env is None:
            env = os.environ.copy()
        
        print(f"Executing: {command}")
        
        # If it's a Python script, run it with python explicitly
        if command.endswith('.py'):
            command = f"python {command}"
        
        result = subprocess.run(
            command,
            shell=shell,
            text=True,
            capture_output=True,
            env=env
        )
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")
        return result.stdout.strip()

    def update_version(self):
        """Update version using update_version.py"""
        env = os.environ.copy()
        env['GH_TOKEN'] = self.gh_token
        return self.run_command(".github/scripts/update_version.py", env=env)

    def setup_qemu(self):
        """Set up QEMU for multi-platform builds"""
        self.run_command("docker run --rm --privileged multiarch/qemu-user-static --reset -p yes")

    def setup_buildx(self):
        """Set up Docker Buildx"""
        self.run_command("docker buildx create --use")

    def docker_login(self):
        """Log in to both Docker Hub and GitHub Container Registry"""
        # Docker Hub login
        self.run_command(f"echo {self.docker_token} | docker login -u {self.docker_username} --password-stdin")
        # GitHub Container Registry login
        self.run_command(f"echo {self.github_token} | docker login ghcr.io -u {self.github_actor} --password-stdin")

    def generate_docker_tags(self, version_output):
        """Generate Docker tags based on version information"""
        tags_json = json.loads(version_output.get('tags', '[]'))
        dockerhub_tags = [f"{self.docker_username}/{self.image_name}:{tag}" for tag in tags_json]
        ghcr_tags = [f"ghcr.io/{self.github_repository_owner}/{self.image_name}:{tag}" for tag in tags_json]
        return ",".join(dockerhub_tags + ghcr_tags)

    def build_and_push(self, tags, version):
        """Build and push Docker image"""
        # Split tags string into list and create --tag arguments
        tag_list = tags.split(',')
        tag_args = ' '.join([f'--tag {tag}' for tag in tag_list])
        
        build_cmd = f"""docker buildx build \
            --platform {self.platforms} \
            --push \
            {tag_args} \
            --label "org.opencontainers.image.title={self.image_name}" \
            --label "org.opencontainers.image.version={version}" \
            --label "org.opencontainers.image.source=https://github.com/{self.github_repository}" \
            --cache-from type=gha \
            --cache-to type=gha,mode=max \
            src"""
        
        self.run_command(build_cmd)

    def save_docker_image(self, version):
        """Save Docker image to tar file"""
        ghcr_tag = f"ghcr.io/{self.github_repository_owner}/{self.image_name}:{version}"
        self.run_command(f"docker pull {ghcr_tag}")
        self.run_command(f"docker save {ghcr_tag} -o {self.image_name}.tar")

    def generate_reports(self, version):
        """Generate SBOM and vulnerability reports"""
        env = os.environ.copy()
        env['GITHUB_TOKEN'] = self.github_token
        env['FULL_VERSION'] = version

        # Generate SBOM
        self.run_command(".github/scripts/generate_sbom.py", env=env)
        
        # Generate vulnerability report
        self.run_command(".github/scripts/generate_vulnerability_report.py", env=env)

    def create_release(self, version):
        """Create release and upload assets"""
        # Create release
        env = os.environ.copy()
        env['GITHUB_TOKEN'] = self.github_token
        self.run_command(".github/scripts/publish_release.py", env=env)

        # Prepare and upload assets
        self.run_command("cp .vulnerability_report.txt vulnerability_report.txt")
        
        assets = [
            f"{self.image_name}.tar",
            ".sbom/sbom.json",
            ".sbom/sbom.txt",
            "vulnerability_report.txt"
        ]

        for asset in assets:
            self.run_command(f"gh release upload {version} {asset}")

    def run(self):
        """Execute all steps in sequence"""
        try:
            # Step 1: Update version
            version_info = self.update_version()
            version = os.getenv("FULL_VERSION")  # Set by update_version.py
            print(f"Version info: {version_info}")
            print(f"Full version: {version}")

            # Step 2: Setup Docker
            self.setup_qemu()
            self.setup_buildx()
            
            # Step 3: Docker login
            self.docker_login()
            
            # Step 4: Generate tags and build/push
            # Use a default tag structure since version_info is not JSON
            tags = f"{self.docker_username}/{self.image_name}:latest,ghcr.io/{self.github_repository_owner}/{self.image_name}:latest"
            if version:
                tags += f",{self.docker_username}/{self.image_name}:{version},ghcr.io/{self.github_repository_owner}/{self.image_name}:{version}"
            
            print(f"Generated tags: {tags}")
            self.build_and_push(tags, version or 'latest')
            
            # Step 5: Save Docker image
            self.save_docker_image(version or 'latest')
            
            # Step 6: Generate reports
            self.generate_reports(version or 'latest')
            
            # Step 7: Create release and upload assets
            self.create_release(version or 'latest')
            
            print("Workflow completed successfully")
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    # Verify required environment variables
    required_vars = ["IMAGE_NAME", "DOCKER_USERNAME", "DOCKER_TOKEN", "GH_TOKEN", "PLATFORMS"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    workflow = DockerBuildAndPush()
    workflow.run()