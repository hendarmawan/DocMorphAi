# Deployment

Release 1 ships as two containers (`web`, `api`) plus managed PostgreSQL,
S3-compatible object storage and Redis. The same images serve all three
editions; the edition is a property of the tenant, not of the build.

| Target | Status | Notes |
|---|---|---|
| Local (Docker Compose) | ✅ M1 | `infrastructure/docker/compose.yaml` |
| SaaS (Creator Cloud) | M5 | Container platform + managed Postgres/Redis + S3 |
| Private deployment (Enterprise) | Release 3 | Helm chart / Terraform module, customer-managed inference via AI adapters |

Configuration is environment-only (`DOCMORPH_*`, see `.env.example`). Secrets
(`DOCMORPH_S3_SECRET_KEY`, `ANTHROPIC_API_KEY`, database credentials) must come
from the platform's secret store, never from images or the repository.
