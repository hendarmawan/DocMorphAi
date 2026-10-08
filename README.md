# DocMorph AI

**Intelligent Documents, Beautiful Experiences.** DocMorph AI turns static
documents (PDF, DOCX, Markdown, TXT) into responsive, interactive web
experiences you can restyle with a prompt and export as a single HTML file.

One platform, three editions (Personal Studio, Creator Cloud, Enterprise
Intelligence) on shared document-processing and rendering infrastructure.

## What works today (M1 + first vertical slice)

Upload a DOCX → inspect its structure → pick a template → live HTML preview →
change the design with a prompt → undo/redo/restore → export standalone HTML.

- Conversion of DOCX (headings, marks, links, lists, tables, images), Markdown,
  TXT and PDF (text layer, flagged *partial*) into one canonical schema
- Four templates: Academic, Corporate, Bilingual, Presentation
- Reader modes: scroll, pagination, swipe (touch + keyboard)
- AI design assistant: prompts become validated design patches; requests to
  change the text itself are refused, so content is never silently altered
- Tenant-scoped storage and queries from day one

## Repository layout

```
apps/web                 Next.js Document Studio
apps/api                 FastAPI backend (modular monolith)
packages/document-schema Canonical document + design schema (JSON Schema, TS, Python)
packages/templates       Template definitions
packages/reader          Interactive reading engine
packages/ui              Shared React components
packages/shared-types    API contracts + typed client
services/converter       Document parsing and upload validation
services/ai-engine       Topic analysis and reprompting (provider adapters)
services/renderer        Deterministic, sanitized HTML generation
services/publisher       Export and publishing
infrastructure/docker    Dockerfiles + Compose stack (Postgres, Redis, MinIO)
tests/                   unit · integration · security (pytest) · e2e (Playwright)
docs/                    architecture, product requirements, API spec, roadmap
```

## Quick start

Requirements: Node 22+, pnpm 10, Python 3.12+, [uv](https://docs.astral.sh/uv/).

```bash
pnpm install && uv sync      # JS and Python workspaces
pnpm build                   # builds packages (incl. the reader bundle) and the web app

pnpm dev:api                 # API on http://localhost:8000 (SQLite + local storage in ./var)
pnpm dev                     # Studio on http://localhost:3000
```

Open http://localhost:3000 and drop in `tests/fixtures/files/quarterly-report.docx`.

Full stack with PostgreSQL, Redis and MinIO:

```bash
docker compose -f infrastructure/docker/compose.yaml up --build
```

Configuration is via `DOCMORPH_*` environment variables; see `.env.example`.
The default AI provider is an offline, deterministic one. To use Claude for
reprompting, run `uv sync --all-packages --all-extras`, then set
`DOCMORPH_AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`.

## Tests

```bash
pnpm test            # TypeScript unit tests (Vitest) across packages and the web app
pnpm typecheck
pnpm test:py         # Python unit, integration and security tests (pytest)
pnpm lint:py         # ruff lint + format check
pnpm test:e2e        # Playwright: starts API + web and runs the vertical slice in a browser
```

CI (`.github/workflows/ci.yml`) runs all of the above plus a Docker Compose
build-and-health job against Postgres, Redis and MinIO.

## Documentation

- [Architecture](docs/architecture.md)
- [Product requirements](docs/product-requirements.md)
- [API specification](docs/api-specification.md) · [OpenAPI](docs/openapi.json)
- [Roadmap](docs/roadmap.md)
