import { createClient } from "@docmorph/shared-types";

/** Browser-side API client. Requests go through the Next.js /api rewrite. */
export const api = createClient({ baseUrl: "/api" });

export const ACCEPTED_EXTENSIONS = [".docx", ".pdf", ".md", ".markdown", ".txt"] as const;
export const MAX_UPLOAD_MB = 25;

export function validateFile(file: { name: string; size: number }): string | null {
  const lower = file.name.toLowerCase();
  if (!ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext))) {
    return "Upload a PDF, DOCX, Markdown or TXT file.";
  }
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `Files are limited to ${MAX_UPLOAD_MB} MB.`;
  return null;
}
