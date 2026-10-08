# Product requirements

**DocMorph AI — Intelligent Documents, Beautiful Experiences.** A platform that
turns static documents into responsive, interactive, customizable, publishable
web experiences.

## Editions

| Edition | Users | Key capabilities |
|---|---|---|
| Personal Studio | Students, researchers, professionals | Conversion, AI editing, reading, templates |
| Creator Cloud | Creators, educators, businesses | Publishing, branding, subscriptions, collaboration |
| Enterprise Intelligence | Corporations, universities, organizations | Governance, SSO, audit logs, private deployment, APIs |

All editions share the same document processing and rendering infrastructure;
the edition is a tenant attribute.

## Release 1: Core Document Studio

Studio layout: document panel (outline, templates) · live HTML preview ·
AI design assistant (prompt, typography, colors, layout) · toolbar (undo, redo,
desktop/tablet/mobile, export, publish).

### Acceptance criteria and status

| Component | Definition of done | Status at end of M1 |
|---|---|---|
| Upload | Accept PDF, DOCX, Markdown, TXT with validation | ✅ Extension + magic bytes + UTF-8 + zip-safety checks, 25 MB limit |
| Conversion | Semantic HTML with headings, paragraphs, supported tables/images | ✅ DOCX/MD/TXT full; PDF text layer only (flagged *partial*) |
| Templates | At least four functioning templates | ✅ Academic, Corporate, Bilingual, Presentation |
| AI understanding | Topic, structure, suggested layout | ✅ Heuristic provider; hosted model adapter ready |
| Reprompting | Change typography/layout/presentation without silently changing content | ✅ Validated design patches; content edits refused |
| Reader | Scrolling, pagination, swipe | ✅ Reader engine; keyboard + touch |
| Versioning | Undo, redo, restore | ✅ Design history (content versioning lands with M4 content edits) |
| Export | Standalone HTML with required assets | ✅ Single file, inline CSS/images/reader, strict CSP |
| Publishing | Create and revoke share links | ⏳ M5 (token primitives exist) |
| Security | Sanitize, restrict file access, upload limits | ✅ Baseline; auth + rate limiting in M5 |

### Known limitations (partially supported)
- Scanned PDFs (no OCR yet), multi-column PDF layouts, PDF tables and images.
- Advanced mathematical layouts (equations are kept as text).
- Complex tables: merged cells are de-duplicated, not spanned.
- DOCX: nested list levels are flattened; text boxes, footnotes, comments and
  tracked changes are not imported yet.
- Markdown images referencing external URLs are replaced by their alt text.

## Non-goals for Release 1
Payments, marketplaces, real-time collaboration, enterprise administration.

## Quality bars
- Deterministic rendering (identical input → identical HTML).
- No uploaded content can execute script in the studio or exports.
- Every API change is reflected in `docs/openapi.json` (enforced by tests).
