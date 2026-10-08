// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Button, Panel, SegmentedControl } from "./index";

describe("ui primitives", () => {
  it("renders a button that defaults to type=button", () => {
    render(<Button>Export</Button>);
    expect(screen.getByRole("button", { name: "Export" }).getAttribute("type")).toBe("button");
  });

  it("renders a titled panel", () => {
    render(<Panel title="Document">body</Panel>);
    expect(screen.getByRole("heading", { name: "Document" })).toBeTruthy();
  });

  it("reports segmented control changes", () => {
    const onChange = vi.fn();
    render(
      <SegmentedControl
        label="Device"
        value="desktop"
        onChange={onChange}
        options={[
          { value: "desktop", label: "Desktop" },
          { value: "mobile", label: "Mobile" },
        ]}
      />,
    );
    expect(screen.getByRole("radio", { name: "Desktop" }).getAttribute("aria-checked")).toBe("true");
    fireEvent.click(screen.getByRole("radio", { name: "Mobile" }));
    expect(onChange).toHaveBeenCalledWith("mobile");
  });
});
