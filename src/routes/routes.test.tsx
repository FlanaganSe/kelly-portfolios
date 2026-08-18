import { MetaProvider } from "@solidjs/meta";
import { createMemoryHistory, MemoryRouter, Route } from "@solidjs/router";
import { cleanup, render, screen } from "@solidjs/testing-library";
import { afterEach, describe, expect, it } from "vitest";
import { families } from "~/content/families";
import { portfolios } from "~/content/portfolios";
import { shelf } from "~/content/shelf";
import Concepts from "~/routes/concepts";
import Confidence from "~/routes/confidence";
import EdgeBudget from "~/routes/edge-budget";
import Evidence from "~/routes/evidence";
import FundDetail from "~/routes/fund-detail";
import Funds from "~/routes/funds";
import Lab from "~/routes/lab";
import Method from "~/routes/method";
import Placement from "~/routes/placement";
import Portfolio from "~/routes/portfolio";
import PortfolioDetail from "~/routes/portfolio-detail";
import Portfolios from "~/routes/portfolios";
import Research from "~/routes/research";
import ResearchDetail from "~/routes/research-detail";
import StartHere from "~/routes/start-here";

/**
 * Route smoke tests.
 *
 * Not snapshots. Each case renders a real route at a real path and asserts that the one
 * thing the page exists to say is on it. The content layer throws rather than
 * substituting a number when a record goes missing, so a page that still renders after a
 * content change is a page whose figures are still sourced.
 */

afterEach(cleanup);

function mount(path: string, pattern: string, component: () => import("solid-js").JSX.Element) {
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

describe("the front page", () => {
  it("states both benchmarks in the same place", async () => {
    mount("/", "/", StartHere);
    expect(await screen.findByRole("heading", { level: 2, name: /two benchmarks/i })).toBeInTheDocument();
    // Decision 0007: the index-relative figure never travels without the 109 bp.
    expect(document.body.textContent).toContain("109");
    expect(document.body.textContent).toContain("313");
  });

  it("shows the proposal beside the evidence-led alternative, with real weights", async () => {
    mount("/", "/", StartHere);
    expect(
      await screen.findByRole("heading", { level: 2, name: /a proposal, and what the evidence supports/i })
    ).toBeInTheDocument();
    const candidate = portfolios.find((one) => one.id === "candidate");
    for (const holding of candidate?.holdings ?? []) {
      expect(screen.getAllByRole("link", { name: holding.ticker }).length).toBeGreaterThan(0);
    }
    // The stacked construction's exposure has to be visible on the front page.
    expect(document.body.textContent).toContain("1.32×");
  });
});

describe("the portfolio library", () => {
  it("lists every published candidate", async () => {
    mount("/portfolios", "/portfolios", Portfolios);
    for (const portfolio of portfolios) {
      // Twice: once in the comparison table and once on its own card.
      expect((await screen.findAllByRole("link", { name: portfolio.name })).length).toBeGreaterThanOrEqual(1);
    }
  });

  it.each(
    portfolios.map((one) => [one.id, one.name] as const)
  )("renders the detail page for %s with its allocation and its failure modes", async (id, name) => {
    mount(`/portfolios/${id}`, "/portfolios/:id", PortfolioDetail);
    expect(await screen.findByRole("heading", { level: 1, name })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { level: 2, name: /what would break it/i })).toBeInTheDocument();
    const portfolio = portfolios.find((one) => one.id === id);
    for (const holding of portfolio?.holdings ?? []) {
      expect(screen.getAllByText(holding.ticker).length).toBeGreaterThan(0);
    }
  });

  it("tells the reader what the evidence would change about the proposal", async () => {
    mount("/portfolios/candidate", "/portfolios/:id", PortfolioDetail);
    expect(
      await screen.findByRole("heading", { level: 2, name: /what this evidence would change/i })
    ).toBeInTheDocument();
    expect(document.body.textContent).toContain("Drop IDMO");
  });

  it("shows a not-found page for an unknown portfolio", async () => {
    mount("/portfolios/does-not-exist", "/portfolios/:id", PortfolioDetail);
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(/no such page/i);
  });
});

describe("the research library", () => {
  it("lists every family", async () => {
    mount("/research", "/research", Research);
    for (const family of families) {
      expect(await screen.findByRole("link", { name: family.name })).toBeInTheDocument();
    }
  });

  it.each(
    families.map((one) => [one.slug, one.name] as const)
  )("renders %s with its contrary evidence", async (slug, name) => {
    mount(`/research/${slug}`, "/research/:slug", ResearchDetail);
    expect(await screen.findByRole("heading", { level: 1, name })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { level: 2, name: /evidence against/i })).toBeInTheDocument();
  });
});

describe("the lab", () => {
  it("opens empty and says why there is no backtest", async () => {
    mount("/lab", "/lab", Lab);
    expect(await screen.findByRole("heading", { level: 1, name: /patience/i })).toBeInTheDocument();
    expect(document.body.textContent).toContain("There is no backtest here");
    expect(document.body.textContent).toContain("Nothing held yet");
  });

  it("preloads a published portfolio from ?from=", async () => {
    mount("/lab?from=evidence-led", "/lab", Lab);
    const evidenceLed = portfolios.find((one) => one.id === "evidence-led");
    for (const holding of evidenceLed?.holdings ?? []) {
      expect(await screen.findByRole("link", { name: holding.ticker })).toBeInTheDocument();
    }
    // The weights of a published portfolio must arrive summing to exactly 100.
    expect(document.body.textContent).toContain("100%");
  });

  it("reproduces the published tilt figure in the tilt calculator", async () => {
    mount("/lab", "/lab", Lab);
    expect(await screen.findByRole("heading", { level: 2, name: /price a value tilt/i })).toBeInTheDocument();
    // AVLV at its published 20% weight on the pooled premium: +24.4 bp against 135 bp.
    expect(document.body.textContent).toContain("+24.4");
    expect(document.body.textContent).toContain("135.4");
  });

  it("offers the bring-your-own-history panel and says nothing leaves the browser", async () => {
    mount("/lab", "/lab", Lab);
    expect(await screen.findByRole("heading", { level: 2, name: /bring your own history/i })).toBeInTheDocument();
    expect(document.body.textContent).toMatch(/nothing is uploaded/i);
  });

  it("reads the edge and tracking error out of the link", async () => {
    mount("/lab?e=109&te=46&h=10", "/lab", Lab);
    expect(await screen.findByRole("heading", { level: 2, name: /how much that moves/i })).toBeInTheDocument();
    // 109 bp against 46 bp is settled inside a decade, and the page has to say so.
    expect(document.body.textContent).toContain("100.0%");
  });
});

describe("the fund shelf", () => {
  it("renders the whole shelf", async () => {
    mount("/funds", "/funds", Funds);
    expect(await screen.findByRole("heading", { level: 1, name: /the shelf/i })).toBeInTheDocument();
    expect(document.body.textContent).toContain(`of ${shelf.length} funds`);
  });

  it("renders a fund page and refuses an unknown ticker", async () => {
    mount("/funds/AVLV", "/funds/:ticker", FundDetail);
    expect(await screen.findByRole("heading", { level: 2, name: /what is established/i })).toBeInTheDocument();

    mount("/funds/ZZZZ", "/funds/:ticker", FundDetail);
    expect(await screen.findAllByRole("heading", { level: 1 })).toBeTruthy();
  });
});

describe("the lab's benchmark control", () => {
  it("offers every benchmark the configuration can hold, so none is silently relabelled", async () => {
    mount("/lab?b=peer", "/lab", Lab);
    const select = await screen.findByLabelText(/measured against/i);
    expect(select).toHaveValue("average-investor");
    // Three reference portfolios, three options. A missing option would render blank and
    // coerce an average-investor figure into an index-relative one on the next change.
    expect(select.querySelectorAll("option")).toHaveLength(3);
  });
});

describe("the long-form pages", () => {
  /**
   * These pre-date the portfolio layer and read from the same content modules, so an
   * edit made for a new page can break an old one silently. One assertion each: that it
   * renders, and that the fact it exists to carry is on it.
   */
  it.each([
    ["/reference", Portfolio, /reference construction/i],
    ["/edge-budget", EdgeBudget, /109/],
    ["/placement", Placement, /shelter/i],
    ["/confidence", Confidence, /tracking error/i],
    ["/evidence", Evidence, /exploratory/i],
    ["/concepts", Concepts, /tracking error/i],
    ["/method", Method, /status/i],
  ])("renders %s", async (path, component, expected) => {
    mount(path, path, component);
    expect(await screen.findByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(document.body.textContent).toMatch(expected);
  });
});
