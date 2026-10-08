"use client";

import { Button } from "@docmorph/ui";
import { useState } from "react";

const SUGGESTIONS = [
  "Dark mode with a gold accent",
  "Bigger serif text, more space",
  "Swipe through it like slides",
  "Two columns, justified",
];

export interface AssistantPanelProps {
  onPrompt: (prompt: string) => Promise<string>;
}

export function AssistantPanel({ onPrompt }: AssistantPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);

  async function submit(text = prompt) {
    if (text.trim().length < 2) return;
    setBusy(true);
    setResult(null);
    try {
      setResult({ ok: true, text: await onPrompt(text.trim()) });
      setPrompt("");
    } catch (e) {
      setResult({ ok: false, text: e instanceof Error ? e.message : "Something went wrong" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="assistant">
      <label htmlFor="assistant-prompt" className="muted">
        Describe changes…
      </label>
      <textarea
        id="assistant-prompt"
        value={prompt}
        placeholder="e.g. make it feel like a modern magazine with a teal accent"
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void submit();
        }}
      />
      <div className="assistant__row">
        <span className="muted">Design only, your text never changes.</span>
        <Button variant="primary" disabled={busy || prompt.trim().length < 2} onClick={() => void submit()}>
          {busy ? "Generating…" : "Generate"}
        </Button>
      </div>
      <div className="chips">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" onClick={() => void submit(s)} disabled={busy}>
            {s}
          </button>
        ))}
      </div>
      {result && (
        <p role="status" className={`assistant__result${result.ok ? "" : " is-error"}`}>
          {result.text}
        </p>
      )}
    </div>
  );
}
