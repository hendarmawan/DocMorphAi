"use client";

import type { DocumentSummary, TemplateSummary } from "@docmorph/shared-types";
import { ArrowRight, CircleAlert, Download, FileText, ScanText, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { TemplatePreview } from "@/components/TemplatePreview";
import { TopNav } from "@/components/TopNav";
import { UploadDropzone } from "@/components/UploadDropzone";
import { api } from "@/lib/api";
import { timeAgo } from "@/lib/format";

const STEPS = [
  { icon: ScanText, title: "Understands structure", text: "Headings, lists, tables and images become a clean, canonical document." },
  { icon: Sparkles, title: "Restyle with a prompt", text: "Describe the look you want. Every change is a reversible design version." },
  { icon: Download, title: "Export anywhere", text: "Download a responsive, self-contained HTML page that reads well on any screen." },
];

export default function HomePage() {
  const router = useRouter();
  const picker = useRef<HTMLInputElement>(null);
  const [docs, setDocs] = useState<DocumentSummary[] | null>(null);
  const [templates, setTemplates] = useState<TemplateSummary[] | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listDocuments()
      .then(setDocs)
      .catch(() => setApiError("The DocMorph API is not reachable. Start it with `pnpm dev:api`."));
    api
      .listTemplates()
      .then(setTemplates)
      .catch(() => setTemplates([]));
  }, []);

  async function upload(file: File) {
    const res = await api.upload(file, file.name);
    router.push(`/studio/${res.document.id}`);
  }

  return (
    <>
      <TopNav onNew={() => picker.current?.click()} />
      <main className="home">
        <section className="hero">
          <div className="hero__glow" aria-hidden="true" />
          <span className="eyebrow">
            <Sparkles size={13} aria-hidden /> AI design studio for documents
          </span>
          <h1>
            Intelligent documents, <span className="gradient-text">beautiful experiences</span>
          </h1>
          <p className="lede">
            Upload a document and DocMorph turns it into a responsive, interactive web page you can restyle with a
            prompt.
          </p>
          <UploadDropzone onUpload={upload} inputRef={picker} />
          {apiError && (
            <p className="error banner" role="alert">
              <CircleAlert size={16} aria-hidden /> {apiError}
            </p>
          )}
        </section>

        <section className="section" id="library" aria-labelledby="library-title">
          <div className="section__head">
            <div>
              <h2 id="library-title">Recent documents</h2>
              <p className="muted">Pick up where you left off.</p>
            </div>
            {docs && docs.length > 0 && <span className="count-pill">{docs.length}</span>}
          </div>
          {docs === null && !apiError && (
            <div className="doc-grid" aria-busy="true">
              {[0, 1, 2].map((i) => (
                <div key={i} className="doc-card is-skeleton" />
              ))}
            </div>
          )}
          {docs && docs.length === 0 && (
            <div className="empty">
              <FileText size={20} aria-hidden />
              <strong>No documents yet</strong>
              <p className="muted">Your converted documents will appear here.</p>
            </div>
          )}
          {docs && docs.length > 0 && (
            <ul className="doc-grid">
              {docs.map((d) => (
                <li key={d.id}>
                  <Link href={`/studio/${d.id}`} className="doc-card">
                    <span className={`doc-card__thumb fmt-${d.source_format}`} aria-hidden="true">
                      <FileText size={18} />
                      <b>{d.source_format.toUpperCase()}</b>
                    </span>
                    <span className="doc-card__body">
                      <span className="doc-card__title">{d.title}</span>
                      <small>
                        {d.fidelity === "partial" && <span className="dm-badge dm-badge--warning">Partial</span>}
                        Edited {timeAgo(d.created_at)}
                      </small>
                    </span>
                    <ArrowRight size={16} className="doc-card__arrow" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="section" id="templates" aria-labelledby="templates-title">
          <div className="section__head">
            <div>
              <h2 id="templates-title">Templates</h2>
              <p className="muted">Starting points tuned for different kinds of documents. Switch any time in the studio.</p>
            </div>
          </div>
          <ul className="tpl-grid">
            {(templates ?? []).map((t) => (
              <li key={t.id} className="tpl-card">
                <TemplatePreview design={t.design} />
                <div className="tpl-card__body">
                  <strong>{t.name}</strong>
                  <p className="muted">{t.description}</p>
                  <div className="tags">
                    {t.suited_for.slice(0, 3).map((s) => (
                      <span key={s} className="tag">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="section" id="how-it-works" aria-labelledby="how-title">
          <div className="section__head">
            <div>
              <h2 id="how-title">How it works</h2>
            </div>
          </div>
          <ol className="steps">
            {STEPS.map(({ icon: Icon, title, text }, i) => (
              <li key={title} className="step">
                <span className="step__icon" aria-hidden="true">
                  <Icon size={18} />
                </span>
                <span className="step__num">0{i + 1}</span>
                <strong>{title}</strong>
                <p className="muted">{text}</p>
              </li>
            ))}
          </ol>
        </section>

        <footer className="site-footer">
          <span>© {new Date().getFullYear()} DocMorph AI</span>
          <span className="muted">Intelligent Documents, Beautiful Experiences</span>
        </footer>
      </main>
    </>
  );
}
