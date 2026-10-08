/**
 * Canonical DocMorph document model (TypeScript mirror of schema/*.schema.json).
 */

export const SCHEMA_VERSION = "1.0" as const;

export type Mark = "bold" | "italic" | "underline" | "strike" | "code" | "superscript" | "subscript";

export interface TextInline {
  type: "text";
  text: string;
  marks?: Mark[];
}

export interface LinkInline {
  type: "link";
  text: string;
  href: string;
  marks?: Mark[];
}

export interface BreakInline {
  type: "break";
}

export type Inline = TextInline | LinkInline | BreakInline;

export interface HeadingBlock {
  type: "heading";
  id: string;
  level: 1 | 2 | 3 | 4 | 5 | 6;
  content: Inline[];
}

export interface ParagraphBlock {
  type: "paragraph" | "quote";
  id: string;
  content: Inline[];
}

export interface ListBlock {
  type: "list";
  id: string;
  ordered: boolean;
  items: Inline[][];
}

export interface TableBlock {
  type: "table";
  id: string;
  header_rows?: number;
  caption?: string;
  rows: Inline[][][];
}

export interface ImageBlock {
  type: "image";
  id: string;
  asset_id: string;
  alt?: string;
  caption?: string;
}

export interface CodeBlock {
  type: "code";
  id: string;
  text: string;
  language?: string;
}

export interface DividerBlock {
  type: "divider";
  id: string;
}

export type Block =
  | HeadingBlock
  | ParagraphBlock
  | ListBlock
  | TableBlock
  | ImageBlock
  | CodeBlock
  | DividerBlock;

export type SourceFormat = "docx" | "pdf" | "markdown" | "txt";

export interface Source {
  format: SourceFormat;
  filename: string;
  sha256: string;
  fidelity?: "full" | "partial";
  warnings?: string[];
}

export interface Asset {
  id: string;
  mime_type: "image/png" | "image/jpeg" | "image/gif" | "image/webp";
  sha256: string;
  size: number;
  filename?: string;
  storage_key?: string;
  data_base64?: string;
}

export interface DocMorphDocument {
  schema_version: typeof SCHEMA_VERSION;
  id: string;
  title: string;
  language: string;
  source: Source;
  metadata?: Record<string, string>;
  blocks: Block[];
  assets: Record<string, Asset>;
}

/* ---------- design ---------- */

export type FontFamily = "serif" | "sans" | "mono" | "humanist" | "slab";

export interface Typography {
  body_font: FontFamily;
  heading_font: FontFamily;
  base_size_px: number;
  line_height: number;
  scale: number;
  heading_weight?: number;
}

export interface Colors {
  background: string;
  text: string;
  accent: string;
  muted: string;
  surface: string;
}

export interface Layout {
  max_width_px: number;
  columns: 1 | 2;
  spacing: "compact" | "normal" | "relaxed";
  align: "left" | "justify" | "center";
  show_toc?: boolean;
  cover?: boolean;
}

export type ReaderMode = "scroll" | "paginate" | "swipe";

export interface DesignConfig {
  schema_version: typeof SCHEMA_VERSION;
  template_id: string;
  typography: Typography;
  colors: Colors;
  layout: Layout;
  reader: { mode: ReaderMode };
}

export interface PatchOp {
  op: "replace";
  path: string;
  value: unknown;
}

export interface DesignPatch {
  kind: "design";
  summary: string;
  ops: PatchOp[];
}

/* ---------- helpers ---------- */

export function plainText(inlines: Inline[]): string {
  return inlines.map((n) => (n.type === "break" ? "\n" : n.text)).join("");
}

export interface OutlineEntry {
  id: string;
  level: number;
  title: string;
}

export function outline(doc: DocMorphDocument): OutlineEntry[] {
  return doc.blocks
    .filter((b): b is HeadingBlock => b.type === "heading")
    .map((h) => ({ id: h.id, level: h.level, title: plainText(h.content) }));
}

export function blockCounts(doc: DocMorphDocument): Record<Block["type"], number> {
  const counts = {
    heading: 0,
    paragraph: 0,
    quote: 0,
    list: 0,
    table: 0,
    image: 0,
    code: 0,
    divider: 0,
  } satisfies Record<Block["type"], number>;
  for (const b of doc.blocks) counts[b.type] += 1;
  return counts;
}
