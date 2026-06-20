#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/ci/local_ci.sh [act flags]

Runs the GitHub CI workflow locally through act for debugging.

Protected merges are gated by GitHub Actions runs on the configured runner
backend. This script does not publish merge-gate statuses.

Examples:
  scripts/ci/local_ci.sh
  scripts/ci/local_ci.sh -j baseline
  LOCAL_CI_EVENT=push scripts/ci/local_ci.sh

Environment:
  LOCAL_CI_EVENT                   GitHub event to simulate. Default: pull_request.
  LOCAL_CI_WORKFLOW                Workflow file to run. Default: .github/workflows/ci.yml.
  LOCAL_CI_ACT_IMAGE               Linux image for ubuntu-latest. Default: ghcr.io/catthehacker/ubuntu:act-24.04.
  LOCAL_CI_CONTAINER_ARCHITECTURE  Container architecture. Default: native Docker VM architecture.
  LOCAL_CI_CONCURRENT_JOBS         Maximum concurrent act jobs. Default: 2.
EOF
}

case "${1:-}" in
  -h|--help|help)
    usage
    exit 0
    ;;
esac

if ! command -v act >/dev/null 2>&1; then
  echo "act is required. Install it before running local GitHub workflows." >&2
  exit 127
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

default_container_architecture() {
  local arch

  arch="$(docker info --format '{{.Architecture}}' 2>/dev/null || uname -m)"

  case "${arch}" in
    aarch64|arm64)
      printf 'linux/arm64'
      ;;
    amd64|x86_64|x64)
      printf 'linux/amd64'
      ;;
    *)
      echo "Unsupported Docker architecture: ${arch}" >&2
      exit 2
      ;;
  esac
}

event="${LOCAL_CI_EVENT:-pull_request}"
workflow="${LOCAL_CI_WORKFLOW:-.github/workflows/ci.yml}"
image="${LOCAL_CI_ACT_IMAGE:-ghcr.io/catthehacker/ubuntu:act-24.04}"
architecture="${LOCAL_CI_CONTAINER_ARCHITECTURE:-$(default_container_architecture)}"
concurrent_jobs="${LOCAL_CI_CONCURRENT_JOBS:-2}"

act "${event}" \
  -W "${workflow}" \
  -P "ubuntu-latest=${image}" \
  --container-architecture "${architecture}" \
  --concurrent-jobs "${concurrent_jobs}" \
  --var 'CI_RUNNER_LABELS_JSON=["ubuntu-latest"]' \
  "$@"
