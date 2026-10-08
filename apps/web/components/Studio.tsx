"use client";

import type { DesignConfig } from "@docmorph/document-schema";
import type {
  DesignState,
  DesignVersion,
  DocumentSummary,
  StructureResponse,
  TemplateSummary,
} from "@docmorph/shared-types";
import { Badge, Button, Panel, SegmentedControl, Toolbar } from "@docmorph/ui";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AssistantPanel } from "./AssistantPanel";
import { DesignControls } from "./DesignControls";

type Device = "desktop" | "tablet" | "mobile";
const DEVICE_WIDTH: Record<Device, string> = { desktop: "100%", tablet: "820px", mobile: "390px" };

export function Studio({ documentId }: { documentId: string }) {
  const [doc, setDoc] = useState<DocumentSummary | null>(null);
  const [structure, setStructure] = useState<StructureResponse | null>(null);
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [state, setState] = useState<DesignState | null>(null);
  const [history, setHistory] = useState<DesignVersion[]>([]);
  const [html, setHtml] = useState<string>("");
  const [device, setDevice] = useState<Device>("desktop");
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
      try {
        setState(await next);
        setError(null);
        await refreshPreview();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Update failed");
      }
    },
    [refreshPreview],
  );

  const onPrompt = async (prompt: string) => {
    const result = await api.prompt(documentId, prompt);
    setState({ current: result.design, can_undo: true, can_redo: false });
    await refreshPreview();
    return result.patch.summary;
  };

  const design = state?.current.design;

  if (error && !doc) {
    return (
      <main className="home">
        <p className="error">{error}</p>
      </main>
    );
  }

  return (
    <div className="studio">
      <aside className="studio__left" aria-label="Document">
        <Panel title="Document">
          <strong>{doc?.title ?? "Loading…"}</strong>
          {doc && (
            <p className="muted">
              {doc.source_format.toUpperCase()} · {structure?.word_count ?? "…"} words{" "}
              {doc.fidelity === "partial" && <Badge tone="warning">partial</Badge>}
            </p>
          )}
          {structure && (
            <>
              <ul className="outline" aria-label="Outline">
                {structure.outline.map((o) => (
                  <li key={o.id} className={`l${o.level}`} title={o.title}>
                    {o.title}
                  </li>
                ))}
              </ul>
              <dl className="stats">
                {(["heading", "paragraph", "list", "table", "image"] as const).map((k) => (
                  <div key={k} style={{ display: "contents" }}>
                    <dt>{k === "heading" ? "Sections" : `${k[0]!.toUpperCase()}${k.slice(1)}s`}</dt>
                    <dd>{structure.counts[k] ?? 0}</dd>
                  </div>
                ))}
              </dl>
              {structure.warnings.map((w) => (
                <p key={w} className="muted">
                  ⚠ {w}
                </p>
              ))}
            </>
          )}
        </Panel>
        <Panel title="Templates" id="templates">
          {structure && (
            <p className="analysis">
              <strong>{structure.analysis.document_type}</strong> about “{structure.analysis.topic}”. Suggested:{" "}
              {structure.analysis.suggested_template}.
            </p>
          )}
          <ul className="templates">
            {templates.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  aria-pressed={design?.template_id === t.id}
                  onClick={() => void commit(api.applyTemplate(documentId, t.id))}
                >
                  {t.name}
                  <small>{t.description}</small>
                </button>
              </li>
            ))}
          </ul>
        </Panel>
      </aside>

      <section className="studio__preview" aria-label="Live document preview">
        <iframe
          title="Live document preview"
          className="preview-frame"
          style={{ maxWidth: DEVICE_WIDTH[device] }}
          sandbox="allow-scripts"
          srcDoc={html}
        />
      </section>

      <aside className="studio__right" aria-label="AI design assistant">
        <Panel title="AI design assistant">
          <AssistantPanel onPrompt={onPrompt} />
        </Panel>
        {design && (
          <Panel>
            <DesignControls
              design={design}
              onChange={(next: DesignConfig, summary) => void commit(api.updateDesign(documentId, next, summary))}
            />
          </Panel>
        )}
        <Panel title="Versions">
          <ol className="history" reversed>
            {[...history].reverse().map((v) => (
              <li key={v.version} className={v.is_current ? "is-current" : undefined}>
                <span>
                  v{v.version} · {v.summary}
                </span>
                {!v.is_current && (
                  <Button size="sm" variant="ghost" onClick={() => void commit(api.restore(documentId, v.version))}>
                    Restore
                  </Button>
                )}
              </li>
            ))}
          </ol>
        </Panel>
      </aside>

      <footer className="studio__bar">
        <Toolbar aria-label="History">
          <Button size="sm" disabled={!state?.can_undo} onClick={() => void commit(api.undo(documentId))}>
            Undo
          </Button>
          <Button size="sm" disabled={!state?.can_redo} onClick={() => void commit(api.redo(documentId))}>
            Redo
          </Button>
          {error && (
            <span role="alert" className="error" style={{ margin: 0 }}>
              {error}
            </span>
          )}
        </Toolbar>
        <SegmentedControl<Device>
          label="Preview device"
          value={device}
          onChange={setDevice}
          options={[
            { value: "desktop", label: "Desktop" },
            { value: "tablet", label: "Tablet" },
            { value: "mobile", label: "Mobile" },
          ]}
        />
        <Toolbar aria-label="Output">
          <a className="dm-btn dm-btn--primary dm-btn--sm" href={api.exportUrl(documentId)} download>
            Export HTML
          </a>
          <Button size="sm" disabled title="Publishing links arrive in M5">
            Publish
          </Button>
        </Toolbar>
      </footer>
    </div>
  );
}
