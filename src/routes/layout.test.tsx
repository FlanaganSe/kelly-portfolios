import { readFileSync } from "node:fs";
import { glob } from "node:fs/promises";
import path from "node:path";
import { MetaProvider } from "@solidjs/meta";
import { createMemoryHistory, MemoryRouter, Route } from "@solidjs/router";
import { cleanup, render, screen } from "@solidjs/testing-library";
import type { JSX } from "solid-js";
import { afterEach, describe, expect, it } from "vitest";
import FundDetail from "~/routes/fund-detail";
import Funds from "~/routes/funds";
import Lab from "~/routes/lab";
import PortfolioDetail from "~/routes/portfolio-detail";
import Portfolios from "~/routes/portfolios";
import Research from "~/routes/research";
import ResearchDetail from "~/routes/research-detail";
import StartHere from "~/routes/start-here";

afterEach(cleanup);

/**
 * The two claims a screenshot would normally have to make, made as checks instead.
 *
 * There is no browser automation in this repository, so "it works on mobile" and
 * "keyboard access is solid" cannot be demonstrated by looking. What can be demonstrated
 * is the property underneath each: that no layout is committed to a width a 360px screen
 * does not have, and that every control a reader can reach has a name a screen reader can
 * announce.
 */

function mount(pathname: string, pattern: string, component: () => JSX.Element) {
  const history = createMemoryHistory();
  history.set({ value: pathname });
  return render(() => (
    <MetaProvider>
      <MemoryRouter history={history}>
        <Route path={pattern} component={component} />
      </MemoryRouter>
    </MetaProvider>
  ));
}

const ROUTES: readonly [string, string, () => JSX.Element][] = [
  ["/", "/", StartHere],
  ["/portfolios", "/portfolios", Portfolios],
  ["/portfolios/candidate", "/portfolios/:id", PortfolioDetail],
  ["/research", "/research", Research],
  ["/research/value", "/research/:slug", ResearchDetail],
  ["/funds", "/funds", Funds],
  ["/funds/RSST", "/funds/:ticker", FundDetail],
  ["/lab?from=candidate", "/lab", Lab],
];

describe("every control has a name", () => {
  it.each(ROUTES)("on %s", async (pathname, pattern, component) => {
    mount(pathname, pattern, component);
    await screen.findByRole("heading", { level: 1 });

    const controls = document.querySelectorAll("button, a[href], input, select, textarea, summary, [tabindex]");
    const unnamed: string[] = [];
    for (const element of controls) {
      const labelled =
        element.getAttribute("aria-label") ??
        (element.getAttribute("aria-labelledby") === null
          ? null
          : (document.getElementById(element.getAttribute("aria-labelledby") ?? "")?.textContent ?? null)) ??
        (element.id === "" ? null : (document.querySelector(`label[for="${element.id}"]`)?.textContent ?? null)) ??
        element.closest("label")?.textContent ??
        element.textContent;
      if ((labelled ?? "").trim() === "") {
        unnamed.push(element.outerHTML.slice(0, 120));
      }
    }
    expect(unnamed, `unnamed controls on ${pathname}`).toEqual([]);
  });
});

describe("heading order", () => {
  it.each(ROUTES)("never skips a level on %s", async (pathname, pattern, component) => {
    mount(pathname, pattern, component);
    await screen.findByRole("heading", { level: 1 });

    const levels = [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")].map((one) => Number(one.tagName.slice(1)));
    expect(
      levels.filter((level) => level === 1),
      `one h1 on ${pathname}`
    ).toHaveLength(1);

    let previous = 1;
    const skips: string[] = [];
    for (const level of levels) {
      if (level > previous + 1) {
        skips.push(`h${previous} → h${level}`);
      }
      previous = level;
    }
    expect(skips, `heading skips on ${pathname}`).toEqual([]);
  });
});

/**
 * A source scan rather than a render: the layout classes that break a 360px screen are
 * visible in the markup, and a rendered jsdom tree has no widths at all.
 */
describe("nothing is committed to a width a small phone does not have", () => {
  it("declares no multi-column grid or wide element without a breakpoint", async () => {
    const offenders: string[] = [];
    let scanned = 0;
    for await (const file of glob("src/**/*.tsx", { cwd: process.cwd() })) {
      if (file.endsWith(".test.tsx")) {
        continue;
      }
      const source = readFileSync(path.join(process.cwd(), file), "utf8");
      scanned += 1;
      for (const [index, line] of source.split("\n").entries()) {
        // A column count with no `sm:`/`md:`/`lg:` in front of it applies at every width.
        for (const match of line.matchAll(/(^|[\s"'`])grid-cols-([2-9]|1[0-2])\b/g)) {
          offenders.push(`${file}:${index + 1} unconditional ${match[0].trim()}`);
        }
        // A pixel width or minimum wider than the narrowest phone content box.
        for (const match of line.matchAll(/\b(?:min-)?w-\[(\d+)px\]/g)) {
          if (Number(match[1]) > 320) {
            offenders.push(`${file}:${index + 1} ${match[0]}`);
          }
        }
      }
    }
    expect(offenders).toEqual([]);
    // A scan that reads nothing passes silently, which is the one way this check lies.
    expect(scanned).toBeGreaterThan(20);
  });
});
