# Test layout

| Folder | Runner | What lives here |
|---|---|---|
| `tests/unit` | pytest | Python services in isolation: converter, renderer, AI engine, publisher, schema contract |
| `tests/integration` | pytest | The FastAPI app end to end through HTTP (the Release-1 vertical slice, tenant isolation) |
| `tests/security` | pytest | Upload restrictions, archive safety, sanitization, CSP/sandbox headers |
| `tests/e2e` | Playwright | Browser tests against the running web app + API |
| `packages/*/src/*.test.ts`, `apps/web/**/*.test.tsx` | Vitest | TypeScript unit tests, colocated with the code |

Fixtures are generated in code (`tests/fixtures/factory.py`) so they stay reviewable;
`scripts/make-sample-docx.py` regenerates the committed DOCX used by the e2e test.
