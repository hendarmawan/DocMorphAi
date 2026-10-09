"use client";

import type { DesignConfig, FontFamily } from "@docmorph/document-schema";
import { SegmentedControl } from "@docmorph/ui";
import { Check, Palette, SlidersHorizontal, Type } from "lucide-react";
import type { CSSProperties } from "react";
import { FONT_STACKS } from "@/lib/format";

const FONTS: FontFamily[] = ["serif", "sans", "humanist", "slab", "mono"];
const FONT_NAMES: Record<FontFamily, string> = {
  serif: "Serif",
  sans: "Sans",
  humanist: "Humanist",
  slab: "Slab",
  mono: "Mono",
};
const ACCENTS = ["#4f46e5", "#0b5cad", "#0f766e", "#15803d", "#b45309", "#c2410c", "#be123c", "#7e22ce"];

export interface DesignControlsProps {
  design: DesignConfig;
  onChange: (design: DesignConfig, summary: string) => void;
}

export function DesignControls({ design, onChange }: DesignControlsProps) {
  const t = design.typography;
  const set = <K extends keyof DesignConfig>(key: K, value: DesignConfig[K], summary: string) =>
    onChange({ ...design, [key]: value }, summary);
  const accent = design.colors.accent.toLowerCase();
  const sizePct = ((t.base_size_px - 12) / (28 - 12)) * 100;

  return (
    <div className="controls">
      <h2 className="side-title">
        <Type size={14} aria-hidden /> Typography
      </h2>
      <div className="field-row">
        <div className="field">
          <label htmlFor="heading-font">Heading font</label>
          <select
            id="heading-font"
            value={t.heading_font}
            style={{ fontFamily: FONT_STACKS[t.heading_font] }}
            onChange={(e) =>
              set("typography", { ...t, heading_font: e.target.value as FontFamily }, `Heading font: ${e.target.value}`)
            }
          >
            {FONTS.map((f) => (
              <option key={f} value={f}>
                {FONT_NAMES[f]}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="body-font">Body font</label>
          <select
            id="body-font"
            value={t.body_font}
            style={{ fontFamily: FONT_STACKS[t.body_font] }}
            onChange={(e) => set("typography", { ...t, body_font: e.target.value as FontFamily }, `Body font: ${e.target.value}`)}
          >
            {FONTS.map((f) => (
              <option key={f} value={f}>
                {FONT_NAMES[f]}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="field">
        <label htmlFor="base-size">
          Text size <span className="field__value">{t.base_size_px}px</span>
        </label>
        <input
          id="base-size"
          type="range"
          className="range"
          min={12}
          max={28}
          value={t.base_size_px}
          style={{ "--range-pct": `${sizePct}%` } as CSSProperties}
          onChange={(e) =>
            set("typography", { ...t, base_size_px: Number(e.target.value) }, `Text size: ${e.target.value}px`)
          }
        />
      </div>

      <h2 className="side-title">
        <Palette size={14} aria-hidden /> Accent color
      </h2>
      <div className="swatches" role="radiogroup" aria-label="Accent presets">
        {ACCENTS.map((c) => (
          <button
            key={c}
            type="button"
            role="radio"
            aria-checked={accent === c}
            aria-label={`Accent ${c}`}
            className="swatch"
            style={{ background: c }}
            onClick={() => set("colors", { ...design.colors, accent: c }, `Accent: ${c}`)}
          >
            {accent === c && <Check size={13} aria-hidden />}
          </button>
        ))}
        <label className="swatch swatch--custom" title="Custom color">
          <span className="sr-only">Accent</span>
          <input
            id="accent"
            type="color"
            value={design.colors.accent}
            onChange={(e) => set("colors", { ...design.colors, accent: e.target.value }, `Accent: ${e.target.value}`)}
          />
        </label>
      </div>

      <h2 className="side-title">
        <SlidersHorizontal size={14} aria-hidden /> Layout
      </h2>
      <div className="field">
        <span className="field__label">Spacing</span>
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
        <span className="field__label">Reading mode</span>
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
    </div>
  );
}
