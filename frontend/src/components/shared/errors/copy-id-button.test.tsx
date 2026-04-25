import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CopyIdButton } from "./copy-id-button";

describe("CopyIdButton", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("renders the correlation ID in monospace text so users can read it aloud", () => {
    render(<CopyIdButton correlationId="01HX3ABCDEF" />);
    expect(screen.getByLabelText("Error correlation ID")).toHaveTextContent("01HX3ABCDEF");
  });

  it("copies to clipboard on click and shows a 'Copied' affordance", async () => {
    const user = userEvent.setup();
    render(<CopyIdButton correlationId="01HX3ABCDEF" />);
    await user.click(screen.getByRole("button", { name: /copy correlation id/i }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("01HX3ABCDEF");
    expect(await screen.findByText("Copied")).toBeInTheDocument();
  });
});
