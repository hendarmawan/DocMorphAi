"use client";

import type { DocumentSummary } from "@docmorph/shared-types";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { UploadDropzone } from "@/components/UploadDropzone";
import { api } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [docs, setDocs] = useState<DocumentSummary[] | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listDocuments()
      .then(setDocs)
      .catch(() => setApiError("The DocMorph API is not reachable. Start it with `pnpm dev:api`."));
  }, []);

  async function upload(file: File) {
    const res = await api.upload(file, file.name);
    router.push(`/studio/${res.document.id}`);
  }

  return (
    <main className="home">
      <h1>Intelligent documents, beautiful experiences</h1>
      <p className="lede">Upload a document and DocMorph turns it into a responsive, interactive web page you can restyle with a prompt.</p>
      <UploadDropzone onUpload={upload} />
      {apiError && <p className="error">{apiError}</p>}
      <section className="doclist" id="library">
        <h2>Recent documents</h2>
        {docs && docs.length === 0 && <p className="muted">Nothing here yet.</p>}
        {docs && docs.length > 0 && (
          <ul>
            {docs.map((d) => (
              <li key={d.id}>
                <Link href={`/studio/${d.id}`}>
                  <span>{d.title}</span>
                  <small>
                    {d.source_format.toUpperCase()} · {d.fidelity === "partial" ? "partial fidelity · " : ""}
                    {new Date(d.created_at).toLocaleDateString()}
                  </small>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
