export interface Pager {
  readonly count: number;
  readonly index: number;
  next(): number;
  prev(): number;
  goTo(index: number): number;
  readonly atStart: boolean;
  readonly atEnd: boolean;
}

/** Bounded page cursor shared by the paginate and swipe modes. */
export function createPager(count: number, start = 0): Pager {
  const clamp = (i: number) => Math.min(Math.max(i, 0), Math.max(count - 1, 0));
  let index = clamp(start);
  return {
    count,
    get index() {
      return index;
    },
    next() {
      index = clamp(index + 1);
      return index;
    },
    prev() {
      index = clamp(index - 1);
      return index;
    },
    goTo(i: number) {
      index = clamp(i);
      return index;
    },
    get atStart() {
      return index === 0;
    },
    get atEnd() {
      return index >= count - 1;
    },
  };
}

export type SwipeDirection = "next" | "prev" | null;

/**
 * Classifies a touch gesture. Horizontal travel must exceed the threshold and
 * dominate vertical travel, so ordinary vertical scrolling never flips pages.
 */
export function classifySwipe(
  start: { x: number; y: number },
  end: { x: number; y: number },
  threshold = 50,
): SwipeDirection {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  if (Math.abs(dx) < threshold || Math.abs(dx) < Math.abs(dy) * 1.5) return null;
  return dx < 0 ? "next" : "prev";
}

/** Fraction (0..1) of the document read in scroll mode. */
export function scrollProgress(scrollTop: number, scrollHeight: number, viewport: number): number {
  const max = scrollHeight - viewport;
  if (max <= 0) return 1;
  return Math.min(Math.max(scrollTop / max, 0), 1);
}
