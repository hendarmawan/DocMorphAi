# Roadmap

## Engineering milestones (Release 1)

| Milestone | Scope | Exit requirement | Status |
|---|---|---|---|
| **M1 Foundation** | Monorepo, UI shell, backend, storage, CI | App starts locally and passes baseline tests | ✅ Done, plus the first vertical slice |
| M2 Document Engine | Upload, parsing, structured schema, HTML renderer | Real documents convert successfully | ◐ Pipeline exists; next: fidelity corpus, Alembic, async conversion jobs (Redis), DOCX footnotes/nested lists, PDF layout + OCR evaluation |
| M3 Design Studio | Templates, visual customization, live preview | Users change designs without losing content | ◐ Four templates + controls; next: template gallery previews, more tokens, custom brand palettes, contrast checks |
| M4 AI + Reader | Topic understanding, reprompting, swipe reader, versioning | AI edits validated and reversible | ◐ Heuristic + Claude adapters, reader engine, design history; next: hosted-model evals, reviewed content patches, content versioning |
| M5 Release | Auth, publishing, exports, security, deployment | End-to-end workflows pass release checks | ○ Auth/tenancy from identity, share links (create/revoke), rate limits, audit log, SaaS deployment |

### First vertical slice (done in M1)
Upload a DOCX → inspect its structure → select a template → render HTML →
change the design through a prompt → export. Covered by
`tests/integration/test_api_workflow.py` and `tests/e2e/vertical-slice.spec.ts`.

## Platform releases

- **Release 2 — Creator Cloud:** team workspaces, custom domains, branded
  publishing, reusable template collections, analytics, subscription billing.
- **Release 3 — Enterprise Intelligence:** SSO/SAML, RBAC, audit trails,
  retention policies, approval workflows, enterprise APIs, private deployment.
- **Release 4 — Intelligent Knowledge Experiences:** retrieval-augmented
  document assistants, cross-document search, interactive learning,
  semantic navigation, specialized agents.
