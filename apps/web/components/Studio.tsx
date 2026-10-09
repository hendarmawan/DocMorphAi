"use client";

import type { DesignConfig } from "@docmorph/document-schema";
import type {
  DesignState,
  DesignVersion,
  DocumentSummary,
  StructureResponse,
  TemplateSummary,
} from "@docmorph/shared-types";
import { Badge, Button, SegmentedControl } from "@docmorph/ui";
import {
  ArrowLeft,
  Check,
  CircleAlert,
  Download,
  History,
  Loader2,
  Monitor,
  Redo2,
  Smartphone,
  Sparkles,
  Tablet,
  Undo2,
  X,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { AssistantPanel } from "./AssistantPanel";
import { DesignControls } from "./DesignControls";
import { LogoMark } from "./Logo";
import { TemplatePreview } from "./TemplatePreview";
import { ThemeToggle } from "./ThemeToggle";

type Device = "desktop" | "tablet" | "mobile";
const DEVICE_WIDTH: Record<Device, string> = { desktop: "100%", tablet: "820px", mobile: "390px" };
const COUNT_LABELS = [
  ["heading", "Sections"],
  ["paragraph", "Paragraphs"],
  ["list", "Lists"],
  ["table", "Tables"],
  ["image", "Images"],
] as const;

export function Studio({ documentId }: { documentId: string }) {
  const [doc, setDoc] = useState<DocumentSummary | null>(null);
  const [structure, setStructure] = useState<StructureResponse | null>(null);
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [state, setState] = useState<DesignState | null>(null);
  const [history, setHistory] = useState<DesignVersion[]>([]);
  const [html, setHtml] = useState<string>("");
  const [device, setDevice] = useState<Device>("desktop");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshPreview = useCallback(async () => {
    const res = await fetch(api.renderUrl(documentId));
    setHtml(await res.text());
    setHistory(await api.designHistory(documentId));
  }, [documentId]);

  useEffect(() => {
    Promise.all([
      api.getSummary(documentId).then(setDoc),
      api.structure(documentId).then(setStructure),
      api.listTemplates().then(setTemplates),
      api.design(documentId).then(setState),
    ])
      .then(refreshPreview)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load document"));
  }, [documentId, refreshPreview]);

  const commit = useCallback(
    async (next: Promise<DesignState>) => {
      setSaving(true);
      try {
        setState(await next);
        setError(null);
        await refreshPreview();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Update failed");
      } finally {
        setSaving(false);
      }
    },
    [refreshPreview],
  );

  const onPrompt = async (prompt: string) => {
    setSaving(true);
    try {
      const result = await api.prompt(documentId, prompt);
      setState({ current: result.design, can_undo: true, can_redo: false });
      await refreshPreview();
      return result.patch.summary;
    } finally {
      setSaving(false);
    }
  };

  const canUndo = Boolean(state?.can_undo);
  const canRedo = Boolean(state?.can_redo);

  // ⌘Z / ⌘⇧Z (Ctrl on Windows and Linux), except while typing in a field.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey) || e.key.toLowerCase() !== "z") return;
      const target = e.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable]")) return;
      if (e.shiftKey ? !canRedo : !canUndo) return;
      e.preventDefault();
      void commit(e.shiftKey ? api.redo(documentId) : api.undo(documentId));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [canUndo, canRedo, commit, documentId]);

  const design = state?.current.design;
  const current = history.find((v) => v.is_current);
  const suggested = templates.find((t) => t.id === structure?.analysis.suggested_template);

  if (error && !doc) {
    return (
      <main className="studio-error">
        <CircleAlert size={22} aria-hidden />
        <p className="error">{error}</p>
        <Link href="/" className="dm-btn dm-btn--secondary dm-btn--md">
          <ArrowLeft size={15} aria-hidden /> Back to documents
        </Link>
      </main>
    );
  }

  return (
    <div className="studio">
      <header className="studio__header">
        <div className="studio__header-left">
          <Link href="/" className="dm-btn dm-btn--ghost dm-btn--icon" aria-label="Back to documents" title="Back to documents">
            <ArrowLeft size={16} aria-hidden />
          </Link>
          <LogoMark size={22} />
          <span className="divider-v" aria-hidden="true" />
          <div className="doc-heading">
            <strong className="doc-heading__title" title={doc?.title}>
              {doc?.title ?? <span className="skeleton-text" />}
            </strong>
            {doc && <Badge>{doc.source_format.toUpperCase()}</Badge>}
            {doc?.fidelity === "partial" && <Badge tone="warning">Partial fidelity</Badge>}
          </div>
          <span className={`save-state${saving ? " is-saving" : ""}`} aria-live="polite">
            {saving ? (
              <>
                <Loader2 size={13} className="spin" aria-hidden /> Saving
              </>
            ) : current ? (
              <>
                <Check size={13} aria-hidden /> Saved · v{current.version}
              </>
            ) : null}
          </span>
        </div>

        <div className="studio__header-center">
          <SegmentedControl<Device>
            label="Preview device"
            value={device}
            onChange={setDevice}
            options={[
              { value: "desktop", label: <><Monitor size={14} aria-hidden /> Desktop</> },
              { value: "tablet", label: <><Tablet size={14} aria-hidden /> Tablet</> },
              { value: "mobile", label: <><Smartphone size={14} aria-hidden /> Mobile</> },
            ]}
          />
        </div>

        <div className="studio__header-right">
          <div className="btn-group" role="toolbar" aria-label="History">
            <Button size="icon" variant="ghost" aria-label="Undo" title="Undo (⌘Z)" disabled={!canUndo} onClick={() => void commit(api.undo(documentId))}>
              <Undo2 size={16} aria-hidden />
            </Button>
            <Button size="icon" variant="ghost" aria-label="Redo" title="Redo (⌘⇧Z)" disabled={!canRedo} onClick={() => void commit(api.redo(documentId))}>
              <Redo2 size={16} aria-hidden />
            </Button>
          </div>
          <ThemeToggle />
          <Button size="sm" disabled title="Publishing links arrive in M5">
            Publish <span className="soon">Soon</span>
          </Button>
          <a className="dm-btn dm-btn--primary dm-btn--sm" href={api.exportUrl(documentId)} download>
            <Download size={15} aria-hidden /> Export HTML
          </a>
        </div>
      </header>

      <aside className="studio__left" aria-label="Document">
        <section className="side-section">
          <h2 className="side-title">Outline</h2>
          {structure ? (
            <ul className="outline" aria-label="Outline">
              {structure.outline.map((o) => (
                <li key={o.id} className={`l${Math.min(o.level, 4)}`} title={o.title}>
                  {o.title}
                </li>
              ))}
            </ul>
          ) : (
            <div className="skeleton-lines" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
          )}
        </section>

        {structure && (
          <section className="side-section">
            <h2 className="side-title">
              Contents <span className="muted">{structure.word_count.toLocaleString()} words</span>
            </h2>
            <dl className="stats">
              {COUNT_LABELS.map(([key, label]) => (
                <div key={key} className="stat">
                  <dd>{structure.counts[key] ?? 0}</dd>
                  <dt>{label}</dt>
                </div>
              ))}
            </dl>
            {structure.warnings.map((w) => (
              <p key={w} className="warning-note">
                <CircleAlert size={14} aria-hidden /> {w}
              </p>
            ))}
          </section>
        )}

        <section className="side-section" id="templates">
          <h2 className="side-title">Templates</h2>
          {structure && (
            <div className="analysis">
              <Sparkles size={15} aria-hidden className="analysis__icon" />
              <p>
                Looks like a <strong>{structure.analysis.document_type}</strong> about “{structure.analysis.topic}”.
                {suggested && design?.template_id !== suggested.id && (
                  <>
                    {" "}
                    <button type="button" className="link-btn" onClick={() => void commit(api.applyTemplate(documentId, suggested.id))}>
                      Try {suggested.name}
                    </button>
                  </>
                )}
              </p>
            </div>
          )}
          <ul className="templates">
            {templates.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  className="tpl-option"
                  aria-pressed={design?.template_id === t.id}
                  onClick={() => void commit(api.applyTemplate(documentId, t.id))}
                >
                  <span className="tpl-option__text">
                    <span className="tpl-option__name">
                      {t.name}
                      {t.id === suggested?.id && <span className="suggested">Suggested</span>}
                    </span>
                    <small>{t.description}</small>
                  </span>
                  <TemplatePreview design={t.design} />
                  {design?.template_id === t.id && <Check size={14} className="tpl-option__check" aria-hidden />}
                </button>
              </li>
            ))}
          </ul>
        </section>
      </aside>

      <section className={`studio__canvas device-${device}`} aria-label="Live document preview">
        {saving && <div className="canvas-progress" aria-hidden="true" />}
        <div className="device-frame" style={{ maxWidth: DEVICE_WIDTH[device] }}>
          {html ? (
            <iframe title="Live document preview" className="preview-frame" sandbox="allow-scripts" srcDoc={html} />
          ) : (
            <div className="preview-loading">
              <Loader2 size={20} className="spin" aria-hidden />
              Rendering preview…
            </div>
          )}
        </div>
      </section>

      <aside className="studio__right" aria-label="AI design assistant">
        <section className="side-section">
          <AssistantPanel onPrompt={onPrompt} />
        </section>
        {design && (
          <section className="side-section">
            <DesignControls
              design={design}
              onChange={(next: DesignConfig, summary) => void commit(api.updateDesign(documentId, next, summary))}
            />
          </section>
        )}
        <section className="side-section">
          <h2 className="side-title">
            <History size={14} aria-hidden /> Versions
          </h2>
          <ol className="history" reversed>
            {[...history].reverse().map((v) => (
              <li key={v.version} className={v.is_current ? "is-current" : undefined}>
                <span className="history__dot" aria-hidden="true" />
                <span className="history__text">
                  <span>{v.summary}</span>
                  <small>
                    v{v.version} · {timeAgo(v.created_at)}
                  </small>
                </span>
                {v.is_current ? (
                  <span className="current-pill">Current</span>
                ) : (
                  <Button size="sm" variant="ghost" onClick={() => void commit(api.restore(documentId, v.version))}>
                    Restore
                  </Button>
                )}
              </li>
            ))}
          </ol>
        </section>
      </aside>

      {error && (
        <div className="toast" role="alert">
          <CircleAlert size={16} aria-hidden />
          <span>{error}</span>
          <button type="button" className="toast__close" aria-label="Dismiss" onClick={() => setError(null)}>
            <X size={14} aria-hidden />
          </button>
        </div>
      )}
    </div>
  );
}
