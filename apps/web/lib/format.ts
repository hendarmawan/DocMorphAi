import type { DesignConfig, FontFamily } from "@docmorph/document-schema";

const UNITS: Array<[Intl.RelativeTimeFormatUnit, number]> = [
  ["year", 365 * 24 * 3600],
  ["month", 30 * 24 * 3600],
  ["week", 7 * 24 * 3600],
  ["day", 24 * 3600],
  ["hour", 3600],
  ["minute", 60],
];

/** "3 hours ago", "yesterday", "just now". */
export function timeAgo(iso: string, now: Date = new Date()): string {
  const seconds = Math.round((new Date(iso).getTime() - now.getTime()) / 1000);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
  }
  return "just now";
}

/** CSS font stacks matching the renderer's font families, for UI previews. */
export const FONT_STACKS: Record<FontFamily, string> = {
  serif: 'Charter, "Bitstream Charter", "Iowan Old Style", Georgia, serif',
  sans: '"Inter Variable", Inter, system-ui, sans-serif',
  humanist: 'Seravek, "Gill Sans Nova", Ubuntu, Calibri, "DejaVu Sans", source-sans-pro, sans-serif',
  slab: 'Rockwell, "Rockwell Nova", "Roboto Slab", "DejaVu Serif", serif',
  mono: 'ui-monospace, "SF Mono", "Cascadia Code", Menlo, monospace',
};

export function previewStyle(design: DesignConfig): Record<string, string> {
  return {
    "--tp-bg": design.colors.background,
    "--tp-text": design.colors.text,
    "--tp-accent": design.colors.accent,
    "--tp-muted": design.colors.muted,
    "--tp-surface": design.colors.surface,
    "--tp-heading-font": FONT_STACKS[design.typography.heading_font],
    "--tp-body-font": FONT_STACKS[design.typography.body_font],
  };
}
