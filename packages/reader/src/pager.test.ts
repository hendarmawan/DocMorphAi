import { describe, expect, it } from "vitest";
import { classifySwipe, createPager, scrollProgress } from "./pager";

describe("createPager", () => {
  it("clamps navigation to the available pages", () => {
    const p = createPager(3);
    expect(p.atStart).toBe(true);
    expect(p.prev()).toBe(0);
    expect(p.next()).toBe(1);
    expect(p.next()).toBe(2);
    expect(p.next()).toBe(2);
    expect(p.atEnd).toBe(true);
    expect(p.goTo(-5)).toBe(0);
  });

  it("handles empty documents", () => {
    const p = createPager(0);
    expect(p.index).toBe(0);
    expect(p.next()).toBe(0);
  });
});

describe("classifySwipe", () => {
  it("detects horizontal swipes", () => {
    expect(classifySwipe({ x: 300, y: 100 }, { x: 100, y: 110 })).toBe("next");
    expect(classifySwipe({ x: 100, y: 100 }, { x: 300, y: 90 })).toBe("prev");
  });

  it("ignores short or mostly-vertical gestures", () => {
    expect(classifySwipe({ x: 100, y: 100 }, { x: 120, y: 100 })).toBeNull();
    expect(classifySwipe({ x: 100, y: 100 }, { x: 180, y: 400 })).toBeNull();
  });
});

describe("scrollProgress", () => {
  it("returns a bounded fraction", () => {
    expect(scrollProgress(0, 2000, 1000)).toBe(0);
    expect(scrollProgress(500, 2000, 1000)).toBe(0.5);
    expect(scrollProgress(5000, 2000, 1000)).toBe(1);
    expect(scrollProgress(0, 500, 1000)).toBe(1);
  });
});
