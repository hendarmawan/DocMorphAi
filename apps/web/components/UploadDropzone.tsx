"use client";

import { Button } from "@docmorph/ui";
import { CircleAlert, Loader2, ShieldCheck, UploadCloud } from "lucide-react";
import { useRef, useState, type DragEvent, type RefObject } from "react";
import { ACCEPTED_EXTENSIONS, MAX_UPLOAD_MB, validateFile } from "@/lib/api";

const FORMATS = ["DOCX", "PDF", "Markdown", "TXT"];

export interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  /** Lets other controls (such as a "New document" button) open the file picker. */
  inputRef?: RefObject<HTMLInputElement | null>;
}

export function UploadDropzone({ onUpload, inputRef }: UploadDropzoneProps) {
  const ownRef = useRef<HTMLInputElement>(null);
  const input = inputRef ?? ownRef;
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handle(file: File | undefined) {
    if (!file) return;
    const problem = validateFile(file);
    setError(problem);
    if (problem) return;
    setBusy(file.name);
    try {
      await onUpload(file);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setBusy(null);
    }
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setOver(false);
    void handle(e.dataTransfer.files[0]);
  };

  return (
    <div
      className={`dropzone${over ? " is-over" : ""}${busy ? " is-busy" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
    >
      <div className="dropzone__icon" aria-hidden="true">
        {busy ? <Loader2 size={22} className="spin" /> : <UploadCloud size={22} />}
      </div>
      {busy ? (
        <>
          <strong className="dropzone__title">Converting {busy}…</strong>
          <p className="dropzone__hint">Reading structure, tables and images. This takes a few seconds.</p>
          <div className="progress" aria-hidden="true">
            <span />
          </div>
        </>
      ) : (
        <>
          <strong className="dropzone__title">Drop a document to transform it</strong>
          <p className="dropzone__hint">or choose a file from your computer, up to {MAX_UPLOAD_MB} MB</p>
          <div className="dropzone__formats" aria-label="Supported formats">
            {FORMATS.map((f) => (
              <span key={f} className="format-pill">
                {f}
              </span>
            ))}
          </div>
        </>
      )}
      <Button variant="primary" disabled={busy !== null} onClick={() => input.current?.click()}>
        {busy ? "Converting…" : "Choose file"}
      </Button>
      <p className="dropzone__trust">
        <ShieldCheck size={14} aria-hidden /> Files stay in your workspace. AI changes the design, never your words.
      </p>
      <input
        ref={input}
        type="file"
        hidden
        aria-label="Upload document"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        onChange={(e) => {
          void handle(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {error && (
        <p role="alert" className="error inline-alert">
          <CircleAlert size={15} aria-hidden /> {error}
        </p>
      )}
    </div>
  );
}
