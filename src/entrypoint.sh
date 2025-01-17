#!/bin/bash

# Load required kernel modules
modprobe bridge || true
modprobe br_netfilter || true

# Enable necessary networking settings
echo 1 > /proc/sys/net/bridge/bridge-nf-call-iptables || true
echo 1 > /proc/sys/net/bridge/bridge-nf-call-ip6tables || true

# Start Docker in the background
dockerd &

# Wait for Docker to start
sleep 10

# Disable the root/sudo check for the GitHub Actions runner
export RUNNER_ALLOW_RUNASROOT=1

# Read environment variables for configuration
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

# Get runner token
echo "Getting runner token from GitHub API..."
RUNNER_TOKEN=$(python3 /actions-runner/tools/get_runner_token.py "$RUNNER_URL" "$GITHUB_PAT")

if [ $? -ne 0 ]; then
    echo "Failed to get runner token"
    exit 1
fi

echo "Successfully obtained runner token"

# Execute delete_offline_runners.py
echo "Cleaning up offline runners..."
python3 /actions-runner/tools/delete_offline_runners.py "$RUNNER_URL" "$GITHUB_PAT"

# Configure the GitHub Actions runner
cd /actions-runner
./config.sh --url "$RUNNER_URL" --token "$RUNNER_TOKEN" --name "$RUNNER_NAME" --unattended

# Start the GitHub Actions runner
./run.sh