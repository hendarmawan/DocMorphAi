import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AssistantPanel } from "./AssistantPanel";

describe("AssistantPanel", () => {
  it("sends the prompt and shows the change summary", async () => {
    const onPrompt = vi.fn(async () => "Applied a dark palette");
    render(<AssistantPanel onPrompt={onPrompt} />);
    fireEvent.change(screen.getByLabelText("Describe changes…"), { target: { value: "make it dark" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));
    expect((await screen.findByRole("status")).textContent).toBe("Applied a dark palette");
    expect(onPrompt).toHaveBeenCalledWith("make it dark");
  });

  it("surfaces refusals as errors", async () => {
    const onPrompt = vi.fn(async () => {
      throw new Error("Design prompts change presentation only.");
    });
    render(<AssistantPanel onPrompt={onPrompt} />);
    fireEvent.click(screen.getByRole("button", { name: "Swipe through it like slides" }));
    const status = await screen.findByRole("status");
    expect(status.className).toContain("is-error");
  });
});
