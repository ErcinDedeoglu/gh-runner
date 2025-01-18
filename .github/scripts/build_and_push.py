#!/usr/bin/env python3

import os
import subprocess
import json
import sys
from pathlib import Path

class DockerBuildAndPush:
    def __init__(self):
        # Get all environment variables from GitHub Actions
        self.image_name = os.getenv("IMAGE_NAME")
        self.docker_username = os.getenv("DOCKER_USERNAME")
        self.docker_token = os.getenv("DOCKER_TOKEN")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.platforms = os.getenv("PLATFORMS")
        self.github_repository = os.getenv("GITHUB_REPOSITORY")
        self.github_repository_owner = self.github_repository.split('/')[0].lower()
        self.github_server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")
        self.github_actor = os.getenv("GITHUB_ACTOR")
        self.github_ref = os.getenv("GITHUB_REF")

    def run_command(self, command, shell=True):
        print(f"Executing: {command}")
        result = subprocess.run(command, shell=shell, text=True, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")
        print(result.stdout)
        return result.stdout.strip()

    def update_version(self):
        print("Updating version...")
        result = self.run_command("python .github/scripts/update_version.py")
        # Assuming update_version.py outputs version info in a specific format
        self.full_version = os.getenv("FULL_VERSION")  # Set by update_version.py
        return result

    def setup_docker(self):
        print("Setting up Docker...")
        self.run_command("docker buildx create --use")
        self.run_command("docker run --rm --privileged multiarch/qemu-user-static --reset -p yes")

    def docker_login(self):
        print("Logging into Docker registries...")
        # Docker Hub login
        self.run_command(f"echo {self.docker_token} | docker login -u {self.docker_username} --password-stdin")
        # GitHub Container Registry login
        self.run_command(f"echo {self.github_token} | docker login ghcr.io -u {self.github_actor} --password-stdin")

    def build_and_push(self):
        print("Building and pushing Docker image...")
        # Generate tags
        version_tags = json.loads(os.getenv("DOCKER_TAGS", "[]"))
        dockerhub_tags = [f"{self.docker_username}/{self.image_name}:{tag}" for tag in version_tags]
        ghcr_tags = [f"ghcr.io/{self.github_repository_owner}/{self.image_name}:{tag}" for tag in version_tags]
        all_tags = dockerhub_tags + ghcr_tags
        tag_args = " ".join([f"-t {tag}" for tag in all_tags])

        build_cmd = f"""
        docker buildx build \
            --platform {self.platforms} \
            --push \
            {tag_args} \
            --label org.opencontainers.image.title={self.image_name} \
            --label org.opencontainers.image.version={self.full_version} \
            --label org.opencontainers.image.source={self.github_server_url}/{self.github_repository} \
            src
        """
        self.run_command(build_cmd)

    def save_and_generate_reports(self):
        print("Saving Docker image and generating reports...")
        # Save Docker image
        ghcr_tag = f"ghcr.io/{self.github_repository_owner}/{self.image_name}:{self.full_version}"
        self.run_command(f"docker pull {ghcr_tag}")
        self.run_command(f"docker save {ghcr_tag} -o {self.image_name}.tar")

        # Generate reports
        self.run_command("python .github/scripts/generate_sbom.py")
        self.run_command("python .github/scripts/generate_vulnerability_report.py")

    def create_release(self):
        print("Creating release and uploading assets...")
        self.run_command("python .github/scripts/publish_release.py")
        
        # Prepare and upload assets
        self.run_command("cp .vulnerability_report.txt vulnerability_report.txt")
        assets = [
            f"{self.image_name}.tar",
            ".sbom/sbom.json",
            ".sbom/sbom.txt",
            "vulnerability_report.txt"
        ]
        
        for asset in assets:
            self.run_command(f"gh release upload {self.full_version} {asset}")

    def run(self):
        try:
            self.update_version()
            self.setup_docker()
            self.docker_login()
            self.build_and_push()
            self.save_and_generate_reports()
            self.create_release()
            print("Workflow completed successfully")
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    workflow = DockerBuildAndPush()
    workflow.run()