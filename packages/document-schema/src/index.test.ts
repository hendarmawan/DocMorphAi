import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import { describe, expect, it } from "vitest";
import { blockCounts, outline, type DocMorphDocument } from "./index";

const here = dirname(fileURLToPath(import.meta.url));
const loadSchema = (name: string) =>
  JSON.parse(readFileSync(join(here, "..", "schema", name), "utf8")) as object;

const sample: DocMorphDocument = {
  schema_version: "1.0",
  id: "doc_1",
  title: "Sample",
  language: "en",
  source: { format: "markdown", filename: "a.md", sha256: "a".repeat(64) },
  blocks: [
    { type: "heading", id: "b1", level: 1, content: [{ type: "text", text: "Intro" }] },
    { type: "paragraph", id: "b2", content: [{ type: "text", text: "Hello", marks: ["bold"] }] },
    { type: "heading", id: "b3", level: 2, content: [{ type: "text", text: "Details" }] },
  ],
  assets: {},
};

describe("document schema", () => {
  it("accepts a well-formed document", () => {
    const ajv = new Ajv2020({ allErrors: true });
    const validate = ajv.compile(loadSchema("document.v1.schema.json"));
    expect(validate(sample), JSON.stringify(validate.errors)).toBe(true);
  });

  it("rejects unknown block types", () => {
    const ajv = new Ajv2020();
    const validate = ajv.compile(loadSchema("document.v1.schema.json"));
    const bad = { ...sample, blocks: [{ type: "script", id: "x", text: "alert(1)" }] };
    expect(validate(bad)).toBe(false);
  });

  it("derives an outline and block counts", () => {
    expect(outline(sample)).toEqual([
      { id: "b1", level: 1, title: "Intro" },
      { id: "b3", level: 2, title: "Details" },
    ]);
    expect(blockCounts(sample).heading).toBe(2);
  });
});
