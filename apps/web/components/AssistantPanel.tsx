"use client";

import { Button } from "@docmorph/ui";
import { CircleAlert, CircleCheck, Loader2, Sparkles, Wand2 } from "lucide-react";
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
      <div className="assistant__head">
        <span className="assistant__badge" aria-hidden="true">
          <Sparkles size={14} />
        </span>
        <div>
          <h2 className="assistant__title">AI design assistant</h2>
          <p className="assistant__sub">Design only. Your text never changes.</p>
        </div>
      </div>
      <div className="prompt-box">
        <label htmlFor="assistant-prompt" className="sr-only">
          Describe changes…
        </label>
        <textarea
          id="assistant-prompt"
          value={prompt}
          placeholder="Describe the look you want, e.g. a modern magazine with a teal accent"
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void submit();
          }}
        />
        <div className="prompt-box__row">
          <kbd className="kbd" aria-hidden="true">
            ⌘ ↵
          </kbd>
          <Button variant="primary" size="sm" disabled={busy || prompt.trim().length < 2} onClick={() => void submit()}>
            {busy ? <Loader2 size={14} className="spin" aria-hidden /> : <Wand2 size={14} aria-hidden />}
            {busy ? "Generating…" : "Generate"}
          </Button>
        </div>
      </div>
      <div className="chips" aria-label="Suggestions">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" onClick={() => void submit(s)} disabled={busy}>
            {s}
          </button>
        ))}
      </div>
      {result && (
        <p role="status" className={`assistant__result${result.ok ? "" : " is-error"}`}>
          {result.ok ? <CircleCheck size={15} aria-hidden /> : <CircleAlert size={15} aria-hidden />}
          <span>{result.text}</span>
        </p>
      )}
    </div>
  );
}
