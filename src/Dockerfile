FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install only what is strictly required
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        jq \
        openssh-client \
        docker.io \
        libicu-dev \
        python3 \
        python3-venv \
        kmod \
        fuse-overlayfs \
        iptables \
        gh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG RUNNER_ARCH="x64"
RUN RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/^v//') \
    && mkdir -p /actions-runner && cd /actions-runner \
    && curl -fsSL -o runner.tar.gz \
       https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && tar xzf runner.tar.gz \
    && rm -f runner.tar.gz

# Use system Python instead of venv to reduce layers
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip && \
    pip3 install --break-system-packages --no-cache-dir requests && \
    apt-get remove -y python3-pip && apt-get autoremove -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH /actions-runner/tools
RUN mkdir -p /actions-runner/tools
COPY tools/*.py /actions-runner/tools/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]