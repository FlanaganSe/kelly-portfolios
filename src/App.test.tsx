import { cleanup, render, screen } from "@solidjs/testing-library";
import { afterEach, describe, expect, it } from "vitest";
import App from "~/App";
import { NAV_ITEMS } from "~/lib/nav";

afterEach(cleanup);

/**
 * The shell. Routes are covered in `src/routes/routes.test.tsx`; this checks the frame
 * around them — the one place a broken import or a missing provider takes down every
 * page at once.
 */
describe("the application shell", () => {
  it("renders the masthead, every section link and the footer", async () => {
    render(() => <App />);

    expect(await screen.findByRole("link", { name: "Portfolio Edge" })).toBeInTheDocument();
    for (const item of NAV_ITEMS) {
      expect(screen.getByRole("link", { name: item.label })).toHaveAttribute("href", item.href);
    }
    expect(screen.getByRole("navigation", { name: "Sections" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main");
    expect(screen.getByRole("contentinfo")).toHaveTextContent(/no sleeve in the underlying research is promoted/i);
  });

  it("gives the collapsed section menu an expanded state a screen reader can read", async () => {
    render(() => <App />);
    const toggle = await screen.findByRole("button", { name: /sections/i });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveAttribute("aria-controls", "sections");
    toggle.click();
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });
});

describe("legacy addresses", () => {
  it("sends /portfolio to the reference construction rather than to the library", async () => {
    window.history.pushState({}, "", "/portfolio");
    render(() => <App />);
    // One character apart from /portfolios; the redirect is the whole point.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(window.location.pathname).toBe("/reference");
    window.history.pushState({}, "", "/");
  });
});
