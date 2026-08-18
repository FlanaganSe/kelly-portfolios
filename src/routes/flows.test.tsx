import { MetaProvider } from "@solidjs/meta";
import { createMemoryHistory, MemoryRouter, Route } from "@solidjs/router";
import { cleanup, fireEvent, render, screen } from "@solidjs/testing-library";
import type { JSX } from "solid-js";
import { afterEach, describe, expect, it } from "vitest";
import Lab from "~/routes/lab";
import ResearchDetail from "~/routes/research-detail";

afterEach(cleanup);

/**
 * The flows a reader actually performs, rather than the pages they land on.
 *
 * These drive real controls. They exist because every one of them crosses a seam — URL
 * to state, state to arithmetic, one page's vocabulary to another's — and a seam is
 * where a refactor breaks something no unit test is watching.
 */

function mount(path: string, pattern: string, component: () => JSX.Element) {
  const history = createMemoryHistory();
  history.set({ value: path });
  return render(() => (
    <MetaProvider>
      <MemoryRouter history={history}>
        <Route path={pattern} component={component} />
      </MemoryRouter>
    </MetaProvider>
  ));
}

describe("editing a portfolio in the lab", () => {
  it("flags a total that is not 100%, and normalising fixes it", async () => {
    mount("/lab?p=VTI:60,VEA:20", "/lab", Lab);

    const totalOf = () => screen.getByText("Total weight").parentElement?.textContent ?? "";
    await screen.findByText("Total weight");
    expect(totalOf()).toContain("80%");

    fireEvent.click(screen.getByRole("button", { name: /normalise to 100/i }));
    expect(totalOf()).toContain("100%");
  });

  it("removes a holding and drops it from the weighted cost", async () => {
    mount("/lab?p=VTI:50,DFIV:50", "/lab", Lab);

    // 3 bp and 27 bp at half each: 15.00 bp.
    expect(await screen.findByText("15.00")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /remove dfiv/i }));
    expect(await screen.findByText("1.50")).toBeInTheDocument();
  });

  it("warns about a fund the shelf has never priced rather than pretending it is free", async () => {
    mount("/lab?p=VTI:50,ZZZZ:50", "/lab", Lab);
    expect((await screen.findAllByText(/not on this shelf/i)).length).toBeGreaterThan(0);
  });
});

describe("a shared link", () => {
  it("recovers the whole experiment, including the benchmark it was measured against", async () => {
    mount("/lab?p=AVLV:100&e=109&te=46&h=10&b=self", "/lab", Lab);

    expect(await screen.findByLabelText(/measured against/i)).toHaveValue("own-counterfactual");
    // 109 bp against 46 bp is settled long before ten years.
    expect(document.body.textContent).toContain("100.0%");
    expect(screen.getAllByRole("link", { name: "AVLV" }).length).toBeGreaterThan(0);
  });
});

describe("moving between a strategy and the portfolios that use it", () => {
  it("links a family to a portfolio and to the funds audited under it", async () => {
    mount("/research/value", "/research/:slug", ResearchDetail);

    expect(await screen.findByRole("link", { name: /the evidence-led tilt/i })).toHaveAttribute(
      "href",
      "/portfolios/evidence-led"
    );
    expect(screen.getByRole("link", { name: "AVLV" })).toHaveAttribute("href", "/funds/AVLV");
  });
});
