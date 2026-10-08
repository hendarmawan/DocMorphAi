# Deployment

Release 1 ships as two containers (`web`, `api`) plus PostgreSQL, Redis and
document storage. The same images serve all three editions; the edition is a
property of the tenant, not of the build.

| Target | Status | Notes |
|---|---|---|
| Local (Docker Compose) | ✅ M1 | `infrastructure/docker/compose.yaml` |
| Single server (VPS) | ✅ | This directory: Caddy + HTTPS + password gate |
| SaaS (Creator Cloud) | M5 | Container platform + managed Postgres/Redis + S3 |
| Private deployment (Enterprise) | Release 3 | Helm chart / Terraform module, customer-managed inference via AI adapters |

## Single server

Any Ubuntu 22.04+/Debian 12+ machine with 2 GB RAM runs the whole stack:

```
internet ──▶ caddy :80/:443 ──┬─ /api/*  ─▶ api :8000 ──▶ postgres, redis, /data volume (or S3)
            (HTTPS, password) └─ /*      ─▶ web :3000
```

- **HTTPS** is automatic (Let's Encrypt) when `DOCMORPH_SITE_ADDRESS` is a
  domain whose DNS points at the server. With `:80` it serves plain HTTP on the IP.
- **Password gate**: there are no user accounts until M5, so Caddy asks for one
  shared user/password on every page and API call. `/api/health` and `/api/ready`
  stay public for uptime monitors.
- **Single tenant**: the API runs with `DOCMORPH_REQUIRE_TENANT_HEADER=false`, so
  everyone behind the gate shares the default workspace.
- **Storage**: documents live on the `api_data` volume. Set the `DOCMORPH_S3_*`
  values in `.env` to use S3 or Cloudflare R2 instead.
- **Uploads** are capped at 25 MB by the API and 30 MB by Caddy.

### 1. Prepare the server (once)

Copy this directory to the server (or clone the repo there) and run:

```bash
sudo ./install.sh --domain docmorph.example.com --deploy-user ubuntu
```

It installs Docker, creates `/opt/docmorph` with the stack files and a generated
`.env`, and prints the site password once. Leave out `--domain` to use the IP
address over plain HTTP.

### 2. Connect GitHub Actions (once)

`.github/workflows/release.yml` builds the `api` and `web` images after CI passes
on `main`, pushes them to `ghcr.io/hendarmawan/docmorphai-{api,web}`, then deploys
over SSH. Add these in **Settings → Secrets and variables → Actions**:

| Name | Kind | Value |
|---|---|---|
| `DEPLOY_HOST` | secret | Server IP or hostname |
| `DEPLOY_USER` | secret | SSH user (the `--deploy-user` above) |
| `DEPLOY_SSH_KEY` | secret | Private key whose public half is in that user's `~/.ssh/authorized_keys` |
| `DEPLOY_KNOWN_HOSTS` | secret, optional | Output of `ssh-keyscan <host>`; without it the host key is trusted on first use |
| `DEPLOY_PATH` | variable, optional | Defaults to `/opt/docmorph` |
| `DEPLOY_URL` | variable, optional | e.g. `https://docmorph.example.com`, for the post-deploy health check |

Make a dedicated key pair for this: `ssh-keygen -t ed25519 -f docmorph-deploy -N ""`.
Without the secrets, the workflow still publishes images and skips the deploy.

### 3. Deploy

Every green push to `main` deploys automatically. To deploy by hand, run the
**Release** workflow from the Actions tab, or on the server:

```bash
cd /opt/docmorph
docker login ghcr.io          # a GitHub token with read:packages, unless the packages are public
./deploy.sh                   # or ./deploy.sh <commit-sha|v-tag> to pin or roll back
```

To build from source on the server instead of pulling images (needs ~4 GB RAM):

```bash
cd infrastructure/deployment   # in a clone of the repo
cp .env.production.example .env   # then fill it in
docker compose -f compose.prod.yaml -f compose.build.yaml up -d --build
```

### Operating it

```bash
cd /opt/docmorph
docker compose -f compose.prod.yaml ps                     # status
docker compose -f compose.prod.yaml logs -f api            # logs
docker compose -f compose.prod.yaml exec postgres \
  pg_dump -U docmorph docmorph > backup.sql                 # database backup
```

Back up the `pgdata` and `api_data` volumes (or the S3 bucket). To use Claude for
design prompts, set `DOCMORPH_AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in
`.env`, then run `./deploy.sh`. To change the password, replace
`DOCMORPH_BASIC_AUTH_HASH` with the output of
`docker run --rm caddy:2.10-alpine caddy hash-password` (keep the single quotes).

Configuration is environment-only (`DOCMORPH_*`, see `.env.production.example`).
Secrets stay in the server's `.env` and GitHub secrets, never in images or the
repository.
