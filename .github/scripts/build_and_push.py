#!/usr/bin/env python3

import os
import subprocess
import json
import sys
from pathlib import Path

print("Script started...", flush=True)
print(f"Python version: {sys.version}", flush=True)
print(f"Current working directory: {os.getcwd()}", flush=True)
print(f"Contents of current directory: {os.listdir('.')}", flush=True)

class DockerBuildAndPush:
    def __init__(self):
        print("Initializing DockerBuildAndPush...", flush=True)
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
        
        print("Environment variables loaded:", flush=True)
        print(f"IMAGE_NAME: {self.image_name}", flush=True)
        print(f"PLATFORMS: {self.platforms}", flush=True)
        print(f"GITHUB_REPOSITORY: {self.github_repository}", flush=True)
        print(f"GITHUB_ACTOR: {self.github_actor}", flush=True)

    def log_step(self, message, start=True):
        """Helper method to log step boundaries"""
        border = "=" * 80
        if start:
            print(f"\n{border}", flush=True)
            print(f"🚀 STARTING STEP: {message}", flush=True)
            print(f"{border}\n", flush=True)
        else:
            print(f"\n{border}", flush=True)
            print(f"✅ COMPLETED STEP: {message}", flush=True)
            print(f"{border}\n", flush=True)

    def run_command(self, command, shell=True, env=None):
        """Execute a command and handle its output"""
        if env is None:
            env = os.environ.copy()
        
        print(f"\n=== Executing Command ===", flush=True)
        print(f"Command: {command}", flush=True)
        print(f"Shell: {shell}", flush=True)
        print(f"Environment variables:", flush=True)
        for key, value in env.items():
            if not any(secret in key.lower() for secret in ['token', 'password', 'secret']):
                print(f"  {key}: {value}", flush=True)
        print("======================\n", flush=True)
        
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
        
        print("\n=== Command Result ===", flush=True)
        print(f"Return code: {result.returncode}", flush=True)
        print("Standard output:", flush=True)
        print(result.stdout, flush=True)
        if result.stderr:
            print("Standard error:", flush=True)
            print(result.stderr, flush=True)
        print("===================\n", flush=True)
        
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
        
        print("\n=== Build Configuration ===", flush=True)
        print(f"Platforms: {self.platforms}", flush=True)
        print("Tags:", flush=True)
        for tag in tag_list:
            print(f"  - {tag}", flush=True)
        print(f"Version: {version}", flush=True)
        print("=========================\n", flush=True)
        
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
        
        print("\n=== Docker Build Command ===", flush=True)
        print(build_cmd, flush=True)
        print("=========================\n", flush=True)
    
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
            self.log_step("UPDATE VERSION")
            version_info = self.update_version()
            version = os.getenv("FULL_VERSION")  # Set by update_version.py
            print(f"Version info: {version_info}", flush=True)
            print(f"Full version: {version}", flush=True)
            self.log_step("UPDATE VERSION", start=False)

            # Step 2: Setup Docker
            self.log_step("SETUP DOCKER ENVIRONMENT")
            self.setup_qemu()
            self.setup_buildx()
            self.log_step("SETUP DOCKER ENVIRONMENT", start=False)
            
            # Step 3: Docker login
            self.log_step("DOCKER LOGIN")
            self.docker_login()
            self.log_step("DOCKER LOGIN", start=False)
            
            # Step 4: Generate tags and build/push
            self.log_step("BUILD AND PUSH DOCKER IMAGE")
            tags = f"{self.docker_username}/{self.image_name}:latest,ghcr.io/{self.github_repository_owner}/{self.image_name}:latest"
            if version:
                tags += f",{self.docker_username}/{self.image_name}:{version},ghcr.io/{self.github_repository_owner}/{self.image_name}:{version}"
            
            print(f"Generated tags: {tags}", flush=True)
            self.build_and_push(tags, version or 'latest')
            self.log_step("BUILD AND PUSH DOCKER IMAGE", start=False)
            
            # Step 5: Save Docker image
            self.log_step("SAVE DOCKER IMAGE")
            self.save_docker_image(version or 'latest')
            self.log_step("SAVE DOCKER IMAGE", start=False)
            
            # Step 6: Generate reports
            self.log_step("GENERATE REPORTS")
            self.generate_reports(version or 'latest')
            self.log_step("GENERATE REPORTS", start=False)
            
            # Step 7: Create release and upload assets
            self.log_step("CREATE AND UPLOAD RELEASE")
            self.create_release(version or 'latest')
            self.log_step("CREATE AND UPLOAD RELEASE", start=False)
            
            print("\n" + "=" * 80, flush=True)
            print("🎉 WORKFLOW COMPLETED SUCCESSFULLY 🎉", flush=True)
            print("=" * 80 + "\n", flush=True)
        except Exception as e:
            print("\n" + "=" * 80, flush=True)
            print("❌ WORKFLOW FAILED ❌", flush=True)
            print(f"Error: {str(e)}", flush=True)
            print("=" * 80 + "\n", flush=True)
            sys.exit(1)

if __name__ == "__main__":
    # Verify required environment variables
    required_vars = ["IMAGE_NAME", "DOCKER_USERNAME", "DOCKER_TOKEN", "GH_TOKEN", "PLATFORMS"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}", flush=True)
        sys.exit(1)

    workflow = DockerBuildAndPush()
    workflow.run()