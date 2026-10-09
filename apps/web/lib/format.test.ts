import { describe, expect, it } from "vitest";
import { timeAgo } from "./format";

describe("timeAgo", () => {
  const now = new Date("2026-10-09T12:00:00Z");

  it("describes recent and older times", () => {
    expect(timeAgo("2026-10-09T11:59:40Z", now)).toBe("just now");
    expect(timeAgo("2026-10-09T09:00:00Z", now)).toBe("3 hours ago");
    expect(timeAgo("2026-10-08T12:00:00Z", now)).toBe("yesterday");
    expect(timeAgo("2026-09-01T12:00:00Z", now)).toBe("last month");
  });
});
