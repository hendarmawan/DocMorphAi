# Docker

`compose.yaml` runs the whole platform locally: `web` (Next.js standalone),
`api` (FastAPI), PostgreSQL 17, Redis 7 and an S3-compatible object store
([S3Mock](https://github.com/adobe/S3Mock), development only) with the `docmorph`
bucket created automatically. Deployments point `DOCMORPH_S3_*` at AWS S3, R2 or
any other S3-compatible service.

```bash
docker compose -f infrastructure/docker/compose.yaml up --build
# web  http://localhost:3000
# api  http://localhost:8000/docs
# s3   http://localhost:9090 (S3 API, dev only)
```

Both Dockerfiles use the repository root as build context.
