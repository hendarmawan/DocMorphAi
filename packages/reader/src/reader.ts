import { classifySwipe, createPager, scrollProgress, type Pager } from "./pager";

export type ReaderMode = "scroll" | "paginate" | "swipe";

export interface ReaderHandle {
  mode: ReaderMode;
  pager: Pager | null;
  destroy(): void;
}

const SECTION_SELECTOR = ".dm-section";

/**
 * Attaches reading behaviour to a document produced by the DocMorph renderer.
 * The rendered HTML is fully readable without this script (scroll mode); the
 * reader only adds progressive enhancements.
 */
export function mountReader(root: HTMLElement, mode?: ReaderMode): ReaderHandle {
  const resolved = (mode ?? (root.dataset.readerMode as ReaderMode | undefined) ?? "scroll") as ReaderMode;
  const doc = root.ownerDocument;
  const win = doc.defaultView;
  const cleanups: Array<() => void> = [];
  root.dataset.readerMode = resolved;
  root.classList.add("dm-reader", `dm-reader--${resolved}`);

  const progress = doc.createElement("div");
  progress.className = "dm-progress";
  progress.setAttribute("aria-hidden", "true");
  root.prepend(progress);
  cleanups.push(() => progress.remove());

  if (resolved === "scroll") {
    const onScroll = () => {
      const el = doc.scrollingElement ?? doc.documentElement;
      const value = scrollProgress(el.scrollTop, el.scrollHeight, win?.innerHeight ?? 0);
      progress.style.transform = `scaleX(${value})`;
    };
    win?.addEventListener("scroll", onScroll, { passive: true });
    cleanups.push(() => win?.removeEventListener("scroll", onScroll));
    onScroll();
    return { mode: resolved, pager: null, destroy: () => cleanups.forEach((c) => c()) };
  }

  const sections = Array.from(root.querySelectorAll<HTMLElement>(SECTION_SELECTOR));
  const pager = createPager(sections.length);

  const nav = doc.createElement("nav");
  nav.className = "dm-pager";
  nav.setAttribute("aria-label", "Page navigation");
  const prevBtn = doc.createElement("button");
  prevBtn.type = "button";
  prevBtn.textContent = "‹ Previous";
  prevBtn.setAttribute("aria-label", "Previous page");
  const status = doc.createElement("span");
  status.className = "dm-pager__status";
  status.setAttribute("aria-live", "polite");
  const nextBtn = doc.createElement("button");
  nextBtn.type = "button";
  nextBtn.textContent = "Next ›";
  nextBtn.setAttribute("aria-label", "Next page");
  nav.append(prevBtn, status, nextBtn);
  root.append(nav);
  cleanups.push(() => nav.remove());

  const render = () => {
    sections.forEach((s, i) => {
      const active = i === pager.index;
      s.hidden = !active;
      s.classList.toggle("dm-section--active", active);
    });
    status.textContent = `${pager.index + 1} / ${Math.max(sections.length, 1)}`;
    prevBtn.disabled = pager.atStart;
    nextBtn.disabled = pager.atEnd;
    progress.style.transform = `scaleX(${sections.length ? (pager.index + 1) / sections.length : 1})`;
  };

  const go = (dir: "next" | "prev") => {
    if (dir === "next") pager.next();
    else pager.prev();
    render();
  };

  prevBtn.addEventListener("click", () => go("prev"));
  nextBtn.addEventListener("click", () => go("next"));

  const onKey = (e: KeyboardEvent) => {
    if (e.key === "ArrowRight" || e.key === "PageDown") go("next");
    if (e.key === "ArrowLeft" || e.key === "PageUp") go("prev");
  };
  doc.addEventListener("keydown", onKey);
  cleanups.push(() => doc.removeEventListener("keydown", onKey));

  if (resolved === "swipe") {
    let start: { x: number; y: number } | null = null;
    const onStart = (e: TouchEvent) => {
      const t = e.touches[0];
      if (t) start = { x: t.clientX, y: t.clientY };
    };
    const onEnd = (e: TouchEvent) => {
      const t = e.changedTouches[0];
      if (!start || !t) return;
      const dir = classifySwipe(start, { x: t.clientX, y: t.clientY });
      start = null;
      if (dir) go(dir);
    };
    root.addEventListener("touchstart", onStart, { passive: true });
    root.addEventListener("touchend", onEnd);
    cleanups.push(() => {
      root.removeEventListener("touchstart", onStart);
      root.removeEventListener("touchend", onEnd);
    });
  }

  render();
  cleanups.push(() => sections.forEach((s) => (s.hidden = false)));
  return { mode: resolved, pager, destroy: () => cleanups.reverse().forEach((c) => c()) };
}
