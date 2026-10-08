import { mountReader } from "./reader";

declare global {
  interface Window {
    DocMorphReader: { mountReader: typeof mountReader };
  }
}

window.DocMorphReader = { mountReader };

const boot = () => {
  const root = document.querySelector<HTMLElement>("[data-docmorph-root]");
  if (root) mountReader(root);
};

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
