// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from "vitest";
import { mountReader } from "./reader";

function fixture(mode: string) {
  document.body.innerHTML = `
    <main data-docmorph-root data-reader-mode="${mode}">
      <section class="dm-section"><h1>One</h1></section>
      <section class="dm-section"><h1>Two</h1></section>
      <section class="dm-section"><h1>Three</h1></section>
    </main>`;
  return document.querySelector<HTMLElement>("main")!;
}

describe("mountReader", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("leaves every section visible in scroll mode", () => {
    const root = fixture("scroll");
    mountReader(root);
    expect([...root.querySelectorAll("section")].every((s) => !s.hidden)).toBe(true);
  });

  it("shows one section at a time in paginate mode", () => {
    const root = fixture("paginate");
    const handle = mountReader(root);
    const visible = () => [...root.querySelectorAll("section")].filter((s) => !s.hidden);
    expect(visible()).toHaveLength(1);
    root.querySelector<HTMLButtonElement>('[aria-label="Next page"]')!.click();
    expect(handle.pager?.index).toBe(1);
    expect(visible()[0]?.textContent).toContain("Two");
    handle.destroy();
    expect(visible()).toHaveLength(3);
  });

  it("navigates with the keyboard", () => {
    const root = fixture("swipe");
    const handle = mountReader(root);
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
    expect(handle.pager?.index).toBe(1);
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft" }));
    expect(handle.pager?.index).toBe(0);
  });
});
