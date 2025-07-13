# gh-runner

A simple, automated self-hosted GitHub Actions runner in Docker—built for reliability, easy cleanup, and minimal maintenance.

## What is gh-runner?

**gh-runner** makes it easy to run your own GitHub Actions runner on your own server or cloud VM using Docker. It comes with built-in automation to keep your runner registry clean by removing offline runners automatically.

---

## Features

- **Self-hosts a GitHub Actions runner** in your environment (repo or org)
- **Automatic offline runner cleanup**—no more stale runners stuck in GitHub
- **Flexible Docker strategy**—choose between host Docker socket or isolated Docker-in-Docker (DinD)
- **Runs Docker jobs** with either host Docker or containerized Docker daemon
- **Comprehensive logging**—console output and detailed diagnostic files

---

## Prebuilt Docker Images

Skip the local build! You can pull and run gh-runner using our prebuilt images:

- **GitHub Packages:**  
  https://github.com/ErcinDedeoglu/gh-runner/pkgs/container/gh-runner

- **Docker Hub:**  
  https://hub.docker.com/r/dublok/gh-runner

**Tags:**  
Images are versioned for easy pinning (examples: `v1.0.9`, `v1.0`, `v1`, `latest`, short hash tags).

**Example Usage:**

```sh
# Docker Hub example
docker pull dublok/gh-runner:latest
docker pull dublok/gh-runner:v1

# GitHub Container Registry example
docker pull ghcr.io/ercindedeoglu/gh-runner:latest
docker pull ghcr.io/ercindedeoglu/gh-runner:v1
```

You can use these in your own `docker-compose.yml` or run them directly. Both registries contain the same image versions.
- **Easy to set up:** just `docker-compose up`
- **Works with public or private GitHub repositories**

---

## Quick Start

### 1. Prerequisites

- **Docker** and **Docker Compose** installed on your server or VM.
- A **GitHub Personal Access Token (PAT)** with `repo` (for repo-level) or `admin:org` (for organization-level) and `workflow` scopes.
- Access to your GitHub repository or organization.

### 2. Download or clone this repository

```sh
git clone https://github.com/ercindedeoglu/gh-runner.git
cd gh-runner
```

### 3. Configure your environment

You will need to create or export the following environment variables:

- **GITHUB_PAT**: Your GitHub Personal Access Token
- **RUNNER_URL**: The URL of your GitHub repository or organization (examples below)
- **DOCKER_SOCK**: Choose Docker strategy (see below)
- **Optional:** You may also adjust the `RUNNER_NAME` and `RUNNER_LABELS` in `docker-compose.yml`.

#### Example repository URL:

```
https://github.com/your-org/your-repo
```

#### Example organization URL:

```
https://github.com/your-org
```

#### Docker Strategy Configuration

The runner supports two Docker execution strategies:

**Option 1: Host Docker Socket (Recommended)**
- Uses your host's Docker daemon
- Faster and more resource-efficient
- Set `DOCKER_SOCK=/var/run/docker.sock` in your environment

**Option 2: Docker-in-Docker (DinD)**
- Runs an isolated Docker daemon inside the container
- Better security isolation
- Set `DOCKER_SOCK=dind` in your environment

To set your PAT in your shell (Linux/Mac):

```sh
export GITHUB_PAT=ghp_xxxxxxx
export DOCKER_SOCK=/var/run/docker.sock  # or DOCKER_SOCK=dind
```

Or place it in a `.env` file (Docker Compose reads this automatically):

```
GITHUB_PAT=ghp_xxxxxxx
DOCKER_SOCK=/var/run/docker.sock
```

### 4. Start the runner

Run:

```sh
docker-compose up -d
```

This will launch the runner in the background.

### 5. Stopping & Updating

To stop the runner:

```sh
docker-compose down
```

To update to the latest version:

```sh
docker-compose pull
docker-compose up -d
```

---

## How Configuration Works

- **`RUNNER_NAME`**: (default: `dind-runner`) The label for your runner on GitHub. Can be any string.
- **`RUNNER_URL`**: GitHub repository or organization URL where this runner will be registered.
- **`GITHUB_PAT`**: Your Personal Access Token for registration and cleanup API calls.
- **`RUNNER_LABELS`**: List of custom labels (comma-separated, e.g. `docker,dind,ubuntu-latest,custom`).
- **`DOCKER_SOCK`**: Docker strategy selector (`/var/run/docker.sock` for host Docker, `dind` for Docker-in-Docker).

Edit these in `docker-compose.yml` or set as environment variables.

---

## How Automated Cleanup Works

Every 5 minutes, the runner checks GitHub for any self-hosted runners that have gone offline. If found, they are automatically unregistered/removed from GitHub using your PAT—no manual intervention needed.

You will see logs about cleanup activity if you run with `docker-compose logs`.

---

## Logging and Monitoring

The runner provides comprehensive logging through multiple channels:

### **Console Logs (Primary)**
```bash
# Real-time streaming
docker logs -f gh-runner-test

# Recent logs only
docker logs --tail=50 gh-runner-test
```

### **Diagnostic Logs (Detailed)**
- **Location**: `/actions-runner/_diag/` directory inside container
- **Files**: `Runner_*.log` files with timestamps
- **Content**: Detailed startup, registration, and execution logs
- **Access**:
  ```bash
  docker exec gh-runner-test ls -la /actions-runner/_diag/
  docker exec gh-runner-test cat /actions-runner/_diag/Runner_*.log
  ```

### **GitHub Web Interface**
- **Runner logs**: Repository → Settings → Actions → Runners → [Your runner] → View logs
- **Job logs**: Each workflow run's details page

### **Docker Compose Logs**
```bash
docker compose logs -f github-runner
```

---

## Troubleshooting

**Common issues:**

- **Runner does not show up on GitHub:** Double-check `GITHUB_PAT` and `RUNNER_URL`.
- **Runner goes offline or keeps unregistering:** Ensure your server has internet access and Docker is running.
- **API errors:** Verify that your GitHub PAT has the correct scopes.
- **Cannot run Docker jobs:** 
  - For host Docker socket: Ensure `/var/run/docker.sock` is mounted and accessible
  - For DinD: Ensure `DOCKER_SOCK=dind` is set and container has required privileges
- **Port already in use / Container doesn't start:** Run `docker-compose down -v` to remove volumes and try again.
- **Permission denied with host Docker socket:** Ensure the container user has access to the Docker socket on your host
- **Log access issues:** Check both console logs and diagnostic files in `/actions-runner/_diag/`

For more details, view runner logs:

```sh
docker-compose logs
```

---

## Support and License

- **Project home:** https://github.com/ercindedeoglu/gh-runner
- **License:** GNU General Public License v3.0 (GPL-3.0)
  See the [LICENSE](LICENSE) file for details.

If you find bugs or need help, please open an issue in the repository.

---

**Enjoy automated, hassle-free self-hosted runners!**