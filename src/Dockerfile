FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
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
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /venv
RUN /venv/bin/pip install requests

ENV PATH="/venv/bin:$PATH"

ARG RUNNER_VERSION="2.321.0"
ARG RUNNER_ARCH="x64"
RUN mkdir -p /actions-runner && cd /actions-runner \
    && curl -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && tar xzf ./actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && rm -f actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz

RUN mkdir -p /actions-runner/tools
COPY tools/*.py /actions-runner/tools/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
