# syntax=docker/dockerfile:1.7
# Build context: repository root.

FROM node:22-bookworm-slim AS reader
WORKDIR /repo
RUN corepack enable
COPY . .
RUN pnpm install --frozen-lockfile && pnpm --filter @docmorph/reader build

FROM python:3.13-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY apps/api apps/api
COPY services services
COPY packages/document-schema packages/document-schema
COPY packages/templates/templates packages/templates/templates
COPY --from=reader /repo/packages/reader/dist packages/reader/dist
# The Claude adapter is included so DOCMORPH_AI_PROVIDER=anthropic works without a rebuild.
RUN uv sync --frozen --no-dev --package docmorph-api --extra anthropic
RUN useradd --create-home --uid 10001 docmorph && mkdir -p /data && chown docmorph /data
USER docmorph
ENV PATH="/app/.venv/bin:$PATH" \
    DOCMORPH_STORAGE_LOCAL_PATH=/data/storage \
    DOCMORPH_DATABASE_URL=sqlite:////data/docmorph.db
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"
CMD ["uvicorn", "docmorph_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
