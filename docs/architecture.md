# Architecture

DocMorph AI is a **modular monolith**: one deployable API process and one web
app, with hard internal boundaries that let any core service be extracted later
without changing its contract.

```
                       apps/web  (Next.js studio)
                            │  /api/* rewrite (same origin)
                            ▼
                       apps/api  (FastAPI)
   ┌──────────────┬─────────┴──────────┬──────────────────┐
   ▼              ▼                    ▼                  ▼
converter      ai-engine            renderer          publisher
(parse)        (analyze, patch)     (HTML)            (export, links)
   └──────────────┴──── document-schema (canonical model) ┘
                            │
             PostgreSQL · S3-compatible storage · Redis
```

## Packages and services

| Path | Language | Responsibility |
|---|---|---|
| `packages/document-schema` | JSON Schema + TS + Python | The canonical, versioned document and design models. JSON Schema is the contract; pydantic and TS types mirror it and are tested against it. |
| `packages/templates` | JSON + TS | Template definitions (Academic, Corporate, Bilingual, Presentation). Read by the renderer and the web app. |
| `packages/reader` | TS | Reading engine (scroll, pagination, swipe). Built into a small IIFE bundle that rendered/exported HTML embeds. |
| `packages/ui` | React | Shared UI primitives for every surface (studio, future reader app, admin). |
| `packages/shared-types` | TS | HTTP API contracts and a typed client. |
| `services/converter` | Python | Upload validation and DOCX/PDF/Markdown/TXT → canonical document. |
| `services/renderer` | Python | Canonical document + design → standalone semantic HTML. |
| `services/ai-engine` | Python | Document understanding and prompt → validated design patch, behind provider adapters. |
| `services/publisher` | Python | Standalone HTML export; share-link token primitives. |
| `apps/api` | Python | HTTP surface, persistence, tenancy, storage, versioning. |
| `apps/web` | TS | The Document Studio UI. |

Services never import `apps/api`; the API composes them. Each service is a
separate Python package in one `uv` workspace, so extracting one into its own
deployable is a packaging change, not a rewrite.

## Key decisions

### 1. Canonical document schema
Every format is normalized into `document.v1` (headings, paragraphs, quotes,
lists, tables, images, code, dividers; inline marks and links). Renderer, AI
and exporters only read this representation. `schema_version` is stored with
every snapshot so the model can evolve with explicit migrations.

### 2. Content and design are separate, and AI edits are validated patches
A document version (content) and a design version (presentation) are stored
independently. AI reprompting produces a `DesignPatch`: a list of `replace`
ops whose paths are restricted to `typography`, `colors`, `layout`, `reader`
and `template_id`. The patch is schema-validated before it is applied, and the
API verifies the content fingerprint is unchanged. Requests to rewrite,
translate or delete text are refused with `content_edit_refused` rather than
being silently applied. Content-changing patches will be a separate, explicitly
reviewed flow (M4+).

### 3. Deterministic rendering
No timestamps, random ids or ordering dependence: the same document version and
design produce byte-identical HTML (enforced by tests). Block ids are assigned
sequentially by the converter, so re-converting the same file is also stable.

### 4. Sanitized by construction
The renderer escapes all text at emission and only emits links with
`http`, `https`, `mailto` or `#` targets; raw HTML in Markdown is disabled at
parse time. Rendered pages carry a strict CSP (`default-src 'none'`, scripts
only by hash). The preview endpoint adds `Content-Security-Policy: sandbox`, and
the studio shows previews in a sandboxed `iframe` without same-origin access.

### 5. Tenant isolation from day one
Every customer-data row has `tenant_id`, and every query goes through a
`TenantContext` (`apps/api/docmorph_api/tenancy.py`). Object keys are prefixed
`tenants/{tenant}/…`. Looking up another tenant's document returns 404, not 403.
Until authentication lands (M5) the tenant comes from `X-Tenant-ID`, with a
default tenant outside production; production requires the header.

### 6. Provider-independent AI
`AIProvider` is a two-method protocol (`analyze`, `design_patch`).
- `heuristic`: deterministic and offline. Default for development and CI.
- `anthropic`: Claude through the official SDK, using structured outputs
  constrained to the allowed patch paths.
Enterprise-controlled inference becomes another adapter.

### 7. Versioning
Design versions form a linear history with a cursor: undo/redo move the cursor,
a new edit after an undo discards the redo branch, and restore appends a copy of
an old version (so restoring is itself undoable).

## Data model (M1)

| Table | Purpose |
|---|---|
| `tenants` | Ownership boundary; `edition` = personal / creator / enterprise |
| `documents` | Upload metadata, original's storage key, current content version, design cursor |
| `document_versions` | Immutable canonical document snapshots + content fingerprint |
| `design_versions` | Immutable design snapshots, origin (`template`/`manual`/`ai`/`restore`), applied patch |

M1 creates tables at startup; Alembic migrations arrive with M2 before any
production data exists.

## Storage
`ObjectStorage` has a local-disk implementation for development and an S3
implementation for MinIO/S3/R2. Originals are stored once per upload;
rendered HTML is computed on demand (deterministic, so cacheable by
`(document_version, design_version)` when needed).
