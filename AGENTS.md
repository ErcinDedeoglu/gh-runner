# AGENTS.md — gh-runner

Docker image for a self-hosted GitHub Actions runner. Ubuntu 24.04 base, bash entrypoint, small Python helpers. No application test suite.

## Layout

- `src/Dockerfile` — image definition. Downloads the latest `actions/runner` release at build time via the GitHub API (`curl` + `jq`), so every rebuild may pin a different runner version. Build context must be `src/`.
- `src/entrypoint.sh` — PID 1. Starts DinD only if `/var/run/docker.sock` is not already mounted, registers the runner, runs `./run.sh`, and owns graceful shutdown (SIGTERM/SIGINT).
- `src/tools/*.py` — copied to `/actions-runner/tools/` and run via `python3` (stdlib + `requests`, installed with `--break-system-packages`). `background_cleanup.py` is spawned by the entrypoint and deletes offline runners from GitHub every 5 minutes.
- `docker-compose.yml` — example usage, not built from source (pulls `ghcr.io/ercindedeoglu/gh-runner:latest`).
- `.sh` — personal scratch file with local build/repomix commands. Ignore; not part of the build.

## Environment contract (consumed by `entrypoint.sh`)

Required: `RUNNER_URL`, `GITHUB_PAT`. Optional: `RUNNER_NAME` (default `dind-runner`, always suffixed with a timestamp), `RUNNER_LABELS`, `RUNNER_EPHEMERAL` (`true` adds `--ephemeral`), `RUNNER_DISABLE_UPDATE` (`true` adds `--disableupdate`). Any change to these names breaks `gh-runner-maestro`.

## Build / run locally

```sh
docker build -f src/Dockerfile -t gh-runner:dev src
# shell into the image without running the runner:
docker run --rm -it --entrypoint sh gh-runner:dev
```

The entrypoint treats any positional args as a command to `exec` (see `src/entrypoint.sh` around the `if [ "$#" -gt 0 ]` check), so pass args to debug.

## Gotchas

- `ENTRYPOINT ["/entrypoint.sh"]` with `RUNNER_ALLOW_RUNASROOT=1` — the runner runs as root inside the container. Required for DinD.
- Ubuntu 24.04 ships PEP 668 Python; `pip3 install` uses `--break-system-packages`. Keep that flag when adding deps in the Dockerfile.
- Storage driver is hard-pinned to `vfs` in `/etc/docker/daemon.json` (cgroup v2 + DinD compatibility). Do not "optimize" to overlay2 without testing on cgroup v2 hosts.
- DinD is only started when the host socket is absent. Don't assume `dockerd` is always running inside the container.
- `RUNNER_NAME` from env is a *base* name; the actual registered name is `${RUNNER_NAME}-${TIMESTAMP}`. Matching on the exact env value will fail.

## CI

`.github/workflows/build-and-push.yml` delegates to `dubloksoftware/workflows/.github/workflows/build-and-push.yml@main` with `context_path: src`, platforms `linux/amd64,linux/arm64`. Only pushes touching `src/**` rebuild the image (plus nightly cron and manual dispatch). `.version_v1.0.json`, `.sbom/`, `.vulnerability_report.txt` are written back by that workflow — treat them as generated.
