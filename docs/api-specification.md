# API specification (v1)

Machine-readable spec: [`openapi.json`](./openapi.json) (generated from the app;
a test fails if it drifts). Interactive docs: `http://localhost:8000/docs`.
TypeScript contracts and client: `packages/shared-types`.

## Conventions
- Base path `/v1`. JSON in and out, except upload (multipart), render and export (HTML).
- Tenant: `X-Tenant-ID` header (`[a-z0-9][a-z0-9_-]{0,63}`). Optional outside
  production (falls back to `default`), required in production until auth lands
  unless `DOCMORPH_REQUIRE_TENANT_HEADER=false`.
- Errors always use one shape:
  ```json
  { "error": { "code": "unsupported_format", "message": "Unsupported file type .exe; ..." } }
  ```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness: database, storage, Redis (if configured). 503 when degraded |
| GET | `/v1/templates` | Available templates with their design configs |
| POST | `/v1/documents` | Upload (`file` form field). Returns summary + structure. 201 |
| GET | `/v1/documents` | List the tenant's documents |
| GET | `/v1/documents/{id}` | Document summary |
| DELETE | `/v1/documents/{id}` | Delete document, versions and stored original |
| GET | `/v1/documents/{id}/content` | Canonical document JSON (`document.v1`) |
| GET | `/v1/documents/{id}/structure` | Outline, block counts, word count, warnings, AI analysis |
| GET | `/v1/documents/{id}/render?reader_mode=` | Rendered HTML preview (sandboxed CSP) |
| GET | `/v1/documents/{id}/export` | Standalone HTML download |
| GET | `/v1/documents/{id}/design` | Current design + `can_undo` / `can_redo` |
| PUT | `/v1/documents/{id}/design` | Replace design (manual controls) |
| GET | `/v1/documents/{id}/design/versions` | Design history |
| POST | `/v1/documents/{id}/design/template` | `{template_id}` apply a template |
| POST | `/v1/documents/{id}/design/prompt` | `{prompt}` AI design change → patch + new version |
| POST | `/v1/documents/{id}/design/undo` | Move back one version (409 if none) |
| POST | `/v1/documents/{id}/design/redo` | Move forward one version (409 if none) |
| POST | `/v1/documents/{id}/design/restore` | `{version}` append a copy of an earlier version |

## Error codes

| Code | HTTP | When |
|---|---|---|
| `unsupported_format` | 415 | Extension not in .docx .pdf .md .markdown .txt |
| `content_mismatch` | 415 | File content doesn't match its extension |
| `bad_encoding` | 422 | Text file is not UTF-8 |
| `empty_file` / `empty_document` | 422 | Nothing to convert |
| `unsafe_archive` | 422 | DOCX zip bomb, path traversal or too many parts |
| `encrypted_pdf` / `too_many_pages` | 422 | PDF limits |
| `file_too_large` | 413 | Over `DOCMORPH_MAX_UPLOAD_BYTES` (default 25 MB) |
| `conversion_failed` | 422 | Valid file the parser could not read |
| `document_not_found` | 404 | Missing, or owned by another tenant |
| `template_not_found` / `version_not_found` | 404 | Unknown id |
| `content_edit_refused` | 422 | Prompt asked to change text, not design |
| `no_design_change` | 422 | Prompt didn't map to a design change |
| `invalid_patch` | 422 | AI patch failed validation |
| `nothing_to_undo` / `nothing_to_redo` | 409 | History boundary |
| `invalid_request` | 422 | Request body validation |
| `tenant_required` / `invalid_tenant` / `unknown_tenant` | 401/400/403 | Tenancy |

## Example: the vertical slice

```bash
API=http://localhost:8000
DOC=$(curl -s -F file=@tests/fixtures/files/quarterly-report.docx $API/v1/documents | jq -r .document.id)
curl -s $API/v1/documents/$DOC/structure | jq '.outline, .analysis'
curl -s -X POST $API/v1/documents/$DOC/design/template -H 'content-type: application/json' -d '{"template_id":"academic"}'
curl -s -X POST $API/v1/documents/$DOC/design/prompt -H 'content-type: application/json' \
     -d '{"prompt":"dark mode, bigger serif text, swipe like slides"}' | jq .patch
curl -s -X POST $API/v1/documents/$DOC/design/undo
curl -s -OJ $API/v1/documents/$DOC/export
```
