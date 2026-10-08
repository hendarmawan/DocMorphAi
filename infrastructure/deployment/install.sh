#!/usr/bin/env bash
# Prepare a fresh Ubuntu or Debian server to run DocMorph.
#
#   sudo ./install.sh --domain docmorph.example.com --deploy-user ubuntu
#
# Installs Docker, creates /opt/docmorph with the stack files and a generated .env
# (database password, gate password), and opens ports 80/443 if ufw is active.
# Safe to re-run: an existing .env is kept.
set -euo pipefail

domain=":80"
gate_user="admin"
target="/opt/docmorph"
deploy_user="${SUDO_USER:-}"

usage() {
  sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
  echo "Options: --domain NAME  --gate-user NAME (default admin)  --dir PATH (default /opt/docmorph)  --deploy-user USER"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain) domain="$2"; shift 2 ;;
    --gate-user) gate_user="$2"; shift 2 ;;
    --dir) target="$2"; shift 2 ;;
    --deploy-user) deploy_user="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

[[ $EUID -eq 0 ]] || { echo "Run as root (sudo)." >&2; exit 1; }
here="$(cd "$(dirname "$0")" && pwd)"

if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  echo "==> Installing Docker"
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl openssl
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker >/dev/null 2>&1 || true

echo "==> Preparing $target"
mkdir -p "$target"
for f in compose.prod.yaml compose.build.yaml Caddyfile deploy.sh .env.production.example; do
  if [[ -f "$here/$f" && "$here" != "$target" ]]; then
    cp "$here/$f" "$target/$f"
  fi
done
chmod +x "$target/deploy.sh" 2>/dev/null || true

gate_password=""
if [[ ! -f "$target/.env" ]]; then
  echo "==> Generating $target/.env"
  gate_password="$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-20)"
  gate_hash="$(docker run --rm caddy:2.10-alpine caddy hash-password --plaintext "$gate_password")"
  cat > "$target/.env" <<ENV
DOCMORPH_SITE_ADDRESS=$domain
DOCMORPH_BASIC_AUTH_USER=$gate_user
DOCMORPH_BASIC_AUTH_HASH='$gate_hash'
POSTGRES_PASSWORD=$(openssl rand -hex 24)
DOCMORPH_VERSION=latest
DOCMORPH_STORAGE_BACKEND=local
DOCMORPH_AI_PROVIDER=heuristic
ANTHROPIC_API_KEY=
ENV
  chmod 600 "$target/.env"
else
  echo "==> Keeping existing $target/.env"
fi

if [[ -n "$deploy_user" ]] && id "$deploy_user" >/dev/null 2>&1; then
  usermod -aG docker "$deploy_user"
  chown -R "$deploy_user" "$target"
fi

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp >/dev/null
  ufw allow 443/tcp >/dev/null
  ufw allow 443/udp >/dev/null
fi

echo
echo "Server is ready. Stack directory: $target"
if [[ -n "$gate_password" ]]; then
  echo "Sign-in for the site:  user '$gate_user'  password '$gate_password'"
  echo "(Shown once. Change it by replacing DOCMORPH_BASIC_AUTH_HASH in $target/.env.)"
fi
echo "Next: run the Deploy workflow in GitHub Actions, or ./deploy.sh in $target after 'docker login ghcr.io'."
