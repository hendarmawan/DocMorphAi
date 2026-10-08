#!/usr/bin/env bash
# Pull the requested image tag and (re)start the stack. Run from this directory.
#   ./deploy.sh            # tag from .env (DOCMORPH_VERSION), default latest
#   ./deploy.sh 3f2c1ab    # a specific commit SHA or release tag
set -euo pipefail
cd "$(dirname "$0")"

[[ -f .env ]] || { echo "Missing .env: run install.sh or copy .env.production.example" >&2; exit 1; }
if [[ $# -ge 1 ]]; then
  # Remember the tag so restarts and later runs without an argument stay on it.
  if grep -q '^DOCMORPH_VERSION=' .env; then
    sed -i "s|^DOCMORPH_VERSION=.*|DOCMORPH_VERSION=$1|" .env
  else
    echo "DOCMORPH_VERSION=$1" >> .env
  fi
  export DOCMORPH_VERSION="$1"
fi

compose=(docker compose -f compose.prod.yaml)
"${compose[@]}" pull
"${compose[@]}" up -d --remove-orphans --wait --wait-timeout 300
docker image prune -f >/dev/null
"${compose[@]}" ps
