import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { validateFile } from "@/lib/api";
import { UploadDropzone } from "./UploadDropzone";

describe("validateFile", () => {
  it("accepts supported formats", () => {
    expect(validateFile({ name: "Report.DOCX", size: 10 })).toBeNull();
    expect(validateFile({ name: "notes.md", size: 10 })).toBeNull();
  });

  it("rejects unsupported, empty and oversized files", () => {
    expect(validateFile({ name: "virus.exe", size: 10 })).toMatch(/PDF, DOCX/);
    expect(validateFile({ name: "a.txt", size: 0 })).toMatch(/empty/);
    expect(validateFile({ name: "a.pdf", size: 26 * 1024 * 1024 })).toMatch(/25 MB/);
  });
});

describe("UploadDropzone", () => {
  it("uploads a valid file", async () => {
    const onUpload = vi.fn(async () => undefined);
    render(<UploadDropzone onUpload={onUpload} />);
    const file = new File(["# hi"], "hello.md", { type: "text/markdown" });
    fireEvent.change(screen.getByLabelText("Upload document"), { target: { files: [file] } });
    await waitFor(() => expect(onUpload).toHaveBeenCalledWith(file));
  });

  it("shows an error for unsupported files without uploading", async () => {
    const onUpload = vi.fn(async () => undefined);
    render(<UploadDropzone onUpload={onUpload} />);
    const file = new File(["x"], "evil.exe");
    fireEvent.change(screen.getByLabelText("Upload document"), { target: { files: [file] } });
    expect((await screen.findByRole("alert")).textContent).toMatch(/PDF, DOCX/);
    expect(onUpload).not.toHaveBeenCalled();
  });
});
