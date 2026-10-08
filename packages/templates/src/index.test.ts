import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import { describe, expect, it } from "vitest";
import { getTemplate, templates } from "./index";

const here = dirname(fileURLToPath(import.meta.url));
const designSchema = JSON.parse(
  readFileSync(join(here, "..", "..", "document-schema", "schema", "design.v1.schema.json"), "utf8"),
) as object;

describe("templates", () => {
  it("ships at least four templates (Release 1 acceptance)", () => {
    expect(templates.length).toBeGreaterThanOrEqual(4);
  });

  it.each(templates.map((t) => [t.id, t] as const))("%s has a valid design config", (id, t) => {
    const validate = new Ajv2020({ allErrors: true }).compile(designSchema);
    expect(validate(t.design), JSON.stringify(validate.errors)).toBe(true);
    expect(t.design.template_id).toBe(id);
  });

  it("looks templates up by id", () => {
    expect(getTemplate("academic")?.name).toBe("Academic");
    expect(getTemplate("nope")).toBeUndefined();
  });
});
