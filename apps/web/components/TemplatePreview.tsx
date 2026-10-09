import type { DesignConfig } from "@docmorph/document-schema";
import type { CSSProperties } from "react";
import { previewStyle } from "@/lib/format";

/** A miniature page drawn with a template's colors and fonts. Decorative only. */
export function TemplatePreview({ design, title = "Aa" }: { design: DesignConfig; title?: string }) {
  const columns = design.layout.columns > 1;
  return (
    <div className="tpl-preview" style={previewStyle(design) as CSSProperties} aria-hidden="true">
      {design.layout.cover && <div className="tpl-preview__cover" />}
      <div className="tpl-preview__title">{title}</div>
      <div className="tpl-preview__rule" />
      <div className={columns ? "tpl-preview__body is-columns" : "tpl-preview__body"}>
        <span />
        <span />
        <span className="is-short" />
        {columns && <span />}
        <span />
        <span className="is-short" />
      </div>
      <div className="tpl-preview__chip" />
    </div>
  );
}
