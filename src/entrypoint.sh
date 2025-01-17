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

# Start Docker in the background with specific storage driver
dockerd --storage-driver=fuse-overlayfs &

# Wait for Docker to start
for i in {1..30}; do
    if docker info >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Rest of your original entrypoint.sh content...
export RUNNER_ALLOW_RUNASROOT=1
BASE_RUNNER_NAME=${RUNNER_NAME:-"dind-runner"}
RUNNER_URL=${RUNNER_URL}
GITHUB_PAT=${GITHUB_PAT}

# Generate timestamp in the required format
TIMESTAMP=$(date +%Y%m%d%H%M%S)
# Generate random number between 0-9
RANDOM_NUM=$((RANDOM % 10))
# Construct the final runner name
RUNNER_NAME="${BASE_RUNNER_NAME}-${TIMESTAMP}-${RANDOM_NUM}"

# Validate required environment variables
if [[ -z "$RUNNER_URL" || -z "$GITHUB_PAT" ]]; then
    echo "ERROR: RUNNER_URL and GITHUB_PAT environment variables must be set."
    exit 1
fi

# Print the generated runner name
echo "Generated runner name: $RUNNER_NAME"

# Function to clean up offline runners
cleanup_runners() {
    echo "Cleaning up offline runners..."
    python3 /actions-runner/tools/delete_offline_runners.py "$RUNNER_URL" "$GITHUB_PAT"
}

# Start the cleanup script in a loop in the background
(
    while true; do
        cleanup_runners
        sleep 300  # Sleep for 5 minutes (300 seconds)
    done
) &

# Initial cleanup at startup
cleanup_runners

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
./config.sh --url "$RUNNER_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --unattended

# Start the GitHub Actions runner
./run.sh