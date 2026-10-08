# Docker

`compose.yaml` runs the whole platform locally: `web` (Next.js standalone),
`api` (FastAPI), PostgreSQL 17, Redis 7 and MinIO (S3-compatible) with the
`docmorph` bucket created automatically.

```bash
docker compose -f infrastructure/docker/compose.yaml up --build
# web  http://localhost:3000
# api  http://localhost:8000/docs
# minio console http://localhost:9001 (docmorph / docmorph-secret, dev only)
```

Both Dockerfiles use the repository root as build context.
