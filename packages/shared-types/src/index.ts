import type {
  DesignConfig,
  DesignPatch,
  DocMorphDocument,
  OutlineEntry,
  SourceFormat,
} from "@docmorph/document-schema";

/* ---------- API contracts (mirror apps/api/docmorph_api/schemas.py) ---------- */

export interface ApiErrorBody {
  error: { code: string; message: string };
}

export interface DocumentSummary {
  id: string;
  title: string;
  source_format: SourceFormat;
  filename: string;
  size_bytes: number;
  fidelity: "full" | "partial";
  created_at: string;
  current_version: number;
  current_design_version: number;
}

export interface DocumentAnalysis {
  topic: string;
  keywords: string[];
  document_type: string;
  suggested_template: string;
  suggested_reader_mode: "scroll" | "paginate" | "swipe";
  rationale: string;
  provider: string;
}

export interface StructureResponse {
  document_id: string;
  version: number;
  outline: OutlineEntry[];
  counts: Record<string, number>;
  word_count: number;
  warnings: string[];
  analysis: DocumentAnalysis;
}

export interface TemplateSummary {
  id: string;
  name: string;
  description: string;
  suited_for: string[];
  design: DesignConfig;
}

export interface DesignVersion {
  version: number;
  design: DesignConfig;
  origin: "template" | "manual" | "ai" | "restore";
  summary: string;
  created_at: string;
  is_current: boolean;
}

export interface DesignState {
  current: DesignVersion;
  can_undo: boolean;
  can_redo: boolean;
}

export interface PromptResult {
  patch: DesignPatch;
  design: DesignVersion;
  content_unchanged: boolean;
  provider: string;
}

export interface UploadResponse {
  document: DocumentSummary;
  structure: StructureResponse;
}

export type { DocMorphDocument, DesignConfig, DesignPatch };

/* ---------- client ---------- */

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface ClientOptions {
  baseUrl: string;
  tenantId?: string;
  fetch?: typeof fetch;
}

export function createClient({ baseUrl, tenantId, fetch: f = fetch }: ClientOptions) {
  const base = baseUrl.replace(/\/$/, "");
  const headers = (extra: Record<string, string> = {}) => ({
    ...(tenantId ? { "X-Tenant-ID": tenantId } : {}),
    ...extra,
  });

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const res = await f(`${base}${path}`, {
      ...init,
      headers: headers(init.headers as Record<string, string> | undefined),
    });
    if (!res.ok) {
      let code = "http_error";
      let message = res.statusText;
      try {
        const body = (await res.json()) as ApiErrorBody;
        code = body.error.code;
        message = body.error.message;
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(res.status, code, message);
    }
    const type = res.headers.get("content-type") ?? "";
    return (type.includes("application/json") ? res.json() : res.text()) as Promise<T>;
  }

  const json = (body: unknown): RequestInit => ({
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
  });

  return {
    health: () => request<{ status: string; version: string }>("/health"),
    listTemplates: () => request<TemplateSummary[]>("/v1/templates"),
    listDocuments: () => request<DocumentSummary[]>("/v1/documents"),
    getSummary: (id: string) => request<DocumentSummary>(`/v1/documents/${id}`),
    getDocument: (id: string) => request<DocMorphDocument>(`/v1/documents/${id}/content`),
    upload: (file: Blob, filename: string) => {
      const form = new FormData();
      form.append("file", file, filename);
      return request<UploadResponse>("/v1/documents", { method: "POST", body: form });
    },
    structure: (id: string) => request<StructureResponse>(`/v1/documents/${id}/structure`),
    design: (id: string) => request<DesignState>(`/v1/documents/${id}/design`),
    designHistory: (id: string) => request<DesignVersion[]>(`/v1/documents/${id}/design/versions`),
    applyTemplate: (id: string, templateId: string) =>
      request<DesignState>(`/v1/documents/${id}/design/template`, json({ template_id: templateId })),
    updateDesign: (id: string, design: DesignConfig, summary = "Manual edit") =>
      request<DesignState>(`/v1/documents/${id}/design`, { ...json({ design, summary }), method: "PUT" }),
    prompt: (id: string, prompt: string) =>
      request<PromptResult>(`/v1/documents/${id}/design/prompt`, json({ prompt })),
    undo: (id: string) => request<DesignState>(`/v1/documents/${id}/design/undo`, json({})),
    redo: (id: string) => request<DesignState>(`/v1/documents/${id}/design/redo`, json({})),
    restore: (id: string, version: number) =>
      request<DesignState>(`/v1/documents/${id}/design/restore`, json({ version })),
    renderUrl: (id: string, mode?: string) =>
      `${base}/v1/documents/${id}/render${mode ? `?reader_mode=${encodeURIComponent(mode)}` : ""}`,
    exportUrl: (id: string) => `${base}/v1/documents/${id}/export`,
  };
}

export type DocMorphClient = ReturnType<typeof createClient>;
