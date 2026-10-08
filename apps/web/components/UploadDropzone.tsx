"use client";

import { Button } from "@docmorph/ui";
import { useRef, useState, type DragEvent } from "react";
import { ACCEPTED_EXTENSIONS, MAX_UPLOAD_MB, validateFile } from "@/lib/api";

export interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
}

export function UploadDropzone({ onUpload }: UploadDropzoneProps) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handle(file: File | undefined) {
    if (!file) return;
    const problem = validateFile(file);
    setError(problem);
    if (problem) return;
    setBusy(true);
    try {
      await onUpload(file);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setOver(false);
    void handle(e.dataTransfer.files[0]);
  };

  return (
    <div
      className={`dropzone${over ? " is-over" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
    >
      <strong>Drop a document to transform it</strong>
      <p>
        PDF, DOCX, Markdown or TXT · up to {MAX_UPLOAD_MB} MB
      </p>
      <Button variant="primary" disabled={busy} onClick={() => input.current?.click()}>
        {busy ? "Converting…" : "Choose file"}
      </Button>
      <input
        ref={input}
        type="file"
        hidden
        aria-label="Upload document"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        onChange={(e) => void handle(e.target.files?.[0])}
      />
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </div>
  );
}
