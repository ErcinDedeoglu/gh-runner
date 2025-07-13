#!/bin/bash

# Function to safely try loading kernel modules
load_kernel_module() {
    module_name=$1
    if lsmod | grep -q "^$module_name"; then
        echo "Module $module_name already loaded"
    else
        modprobe $module_name 2>/dev/null || true
    fi
}

# Attempt to load kernel modules silently
load_kernel_module bridge
load_kernel_module br_netfilter

# Try to set network parameters, but don't fail if they don't exist
(echo 1 > /proc/sys/net/bridge/bridge-nf-call-iptables 2>/dev/null || true) &>/dev/null
(echo 1 > /proc/sys/net/bridge/bridge-nf-call-ip6tables 2>/dev/null || true) &>/dev/null

# Ensure a Docker daemon is available.
# If the host Docker socket is mounted into the container we use it directly.
# Otherwise, fall back to starting our own DinD daemon.
if [ ! -S /var/run/docker.sock ]; then
    echo "Docker socket not found; starting internal Docker daemon..."
    dockerd --storage-driver=fuse-overlayfs &
    # Wait for Docker to start
    for i in {1..30}; do
        if docker info >/dev/null 2>&1; then
            echo "Docker daemon started successfully"
            break
        fi
        sleep 1
    done
else
    echo "Detected host Docker socket – skipping internal daemon startup"
fi

# Disable the root/sudo check for the GitHub Actions runner
export RUNNER_ALLOW_RUNASROOT=1

# Read environment variables for configuration
BASE_RUNNER_NAME=${RUNNER_NAME:-"dind-runner"}
RUNNER_URL=${RUNNER_URL}
GITHUB_PAT=${GITHUB_PAT}
RUNNER_LABELS=${RUNNER_LABELS:-""}

# Generate timestamp in the required format
TIMESTAMP=$(date +%Y%m%d%H%M%S)
RUNNER_NAME="${BASE_RUNNER_NAME}-${TIMESTAMP}"

# Validate required environment variables
if [[ -z "$RUNNER_URL" || -z "$GITHUB_PAT" ]]; then
    echo "ERROR: RUNNER_URL and GITHUB_PAT environment variables must be set."
    exit 1
fi

# Print the generated runner name and labels
echo "Generated runner name: $RUNNER_NAME"
echo "Runner labels: $RUNNER_LABELS"

# Start background cleanup process
python3 /actions-runner/tools/background_cleanup.py "$RUNNER_URL" "$GITHUB_PAT" &

# Get runner token
echo "Getting runner token from GitHub API..."
RUNNER_TOKEN=$(python3 /actions-runner/tools/get_runner_token.py "$RUNNER_URL" "$GITHUB_PAT")
if [ $? -ne 0 ]; then
    echo "Failed to get runner token"
    exit 1
fi
echo "Successfully obtained runner token"

# Configure the GitHub Actions runner
cd /actions-runner
if [ -z "$RUNNER_LABELS" ]; then
    ./config.sh --url "$RUNNER_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --unattended
else
    ./config.sh --url "$RUNNER_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --labels "$RUNNER_LABELS" --unattended
fi

# Start the GitHub Actions runner
./run.sh