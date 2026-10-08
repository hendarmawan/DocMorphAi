"use client";

import type { DesignConfig, FontFamily } from "@docmorph/document-schema";
import { SegmentedControl } from "@docmorph/ui";

const FONTS: FontFamily[] = ["serif", "sans", "humanist", "slab", "mono"];

export interface DesignControlsProps {
  design: DesignConfig;
  onChange: (design: DesignConfig, summary: string) => void;
}

export function DesignControls({ design, onChange }: DesignControlsProps) {
  const t = design.typography;
  const set = <K extends keyof DesignConfig>(key: K, value: DesignConfig[K], summary: string) =>
    onChange({ ...design, [key]: value }, summary);

  return (
    <>
      <h3 className="dm-panel__title">Typography</h3>
      <div className="field">
        <label htmlFor="body-font">Body font</label>
        <select
          id="body-font"
          value={t.body_font}
          onChange={(e) => set("typography", { ...t, body_font: e.target.value as FontFamily }, `Body font: ${e.target.value}`)}
        >
          {FONTS.map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="heading-font">Heading font</label>
        <select
          id="heading-font"
          value={t.heading_font}
          onChange={(e) =>
            set("typography", { ...t, heading_font: e.target.value as FontFamily }, `Heading font: ${e.target.value}`)
          }
        >
          {FONTS.map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="base-size">Text size · {t.base_size_px}px</label>
        <input
          id="base-size"
          type="range"
          min={12}
          max={28}
          value={t.base_size_px}
          onChange={(e) =>
            set("typography", { ...t, base_size_px: Number(e.target.value) }, `Text size: ${e.target.value}px`)
          }
        />
      </div>

      <h3 className="dm-panel__title">Colors</h3>
      <div className="field">
        <label htmlFor="accent">Accent</label>
        <input
          id="accent"
          type="color"
          value={design.colors.accent}
          onChange={(e) => set("colors", { ...design.colors, accent: e.target.value }, `Accent: ${e.target.value}`)}
        />
      </div>

      <h3 className="dm-panel__title">Layout</h3>
      <div className="field">
        <label>Spacing</label>
        <SegmentedControl
          label="Spacing"
          value={design.layout.spacing}
          options={[
            { value: "compact", label: "Compact" },
            { value: "normal", label: "Normal" },
            { value: "relaxed", label: "Relaxed" },
          ]}
          onChange={(v) => set("layout", { ...design.layout, spacing: v }, `Spacing: ${v}`)}
        />
      </div>
      <div className="field">
        <label>Reading</label>
        <SegmentedControl
          label="Reading mode"
          value={design.reader.mode}
          options={[
            { value: "scroll", label: "Scroll" },
            { value: "paginate", label: "Pages" },
            { value: "swipe", label: "Swipe" },
          ]}
          onChange={(v) => set("reader", { mode: v }, `Reading mode: ${v}`)}
        />
      </div>
    </>
  );
}
