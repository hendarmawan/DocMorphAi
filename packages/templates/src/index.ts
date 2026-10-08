import type { DesignConfig } from "@docmorph/document-schema";
import academic from "../templates/academic.json" with { type: "json" };
import bilingual from "../templates/bilingual.json" with { type: "json" };
import corporate from "../templates/corporate.json" with { type: "json" };
import presentation from "../templates/presentation.json" with { type: "json" };

export interface TemplateDefinition {
  id: string;
  name: string;
  description: string;
  suited_for: string[];
  design: DesignConfig;
}

export const templates: TemplateDefinition[] = [
  academic as TemplateDefinition,
  corporate as TemplateDefinition,
  bilingual as TemplateDefinition,
  presentation as TemplateDefinition,
];

export function getTemplate(id: string): TemplateDefinition | undefined {
  return templates.find((t) => t.id === id);
}
