import { cleanup, fireEvent, render, screen, within } from "@solidjs/testing-library";
import { afterEach, describe, expect, it } from "vitest";
import { HistoryPanel } from "~/components/lab/HistoryPanel";
import { toYearMonth } from "~/lib/backtest/calendar";

// Auto-cleanup is not enabled in this repository, so every render is torn down by hand.
afterEach(cleanup);

const HOLDINGS = [
  { ticker: "AAA", percent: 60 },
  { ticker: "BBB", percent: 40 },
] as const;

const START = 600; // 2020-01
const MONTHS = 36;

/**
 * A paste with arithmetic anyone can check.
 *
 * Both holdings return exactly +2%, 0%, +2%, … so the portfolio's monthly return is
 * +2%, 0% whatever the weights and whatever the rebalancing, and its CAGR is
 * 1.02^6 − 1 = 12.62%. The benchmark alternates +1%, 0%, giving 1.01^6 − 1 = 6.15%,
 * a beta of exactly 2 and a correlation of exactly 1.
 */
function fixture(options: { readonly gapAt?: number; readonly bbbFrom?: number } = {}): string {
  const rows: string[] = ["Month,AAA,BBB,BENCH"];
  for (let index = 0; index < MONTHS; index += 1) {
    const on = index % 2 === 0;
    const aaa = options.gapAt === index ? "" : on ? "0.02" : "0";
    const bbb = index < (options.bbbFrom ?? 0) ? "" : on ? "0.02" : "0";
    rows.push(`${toYearMonth(START + index)},${aaa},${bbb},${on ? "0.01" : "0"}`);
  }
  return rows.join("\n");
}

function paste(screen: ReturnType<typeof render>, text: string): void {
  const box = screen.getByLabelText("Monthly total returns");
  fireEvent.input(box, { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Import" }));
}

describe("HistoryPanel", () => {
  it("shows an empty state, and says that nothing leaves the browser", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);

    expect(screen.getByText(/Nothing imported yet/)).toBeInTheDocument();
    expect(screen.getByText(/no account and no server/)).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: /Your portfolio against/ })).toBeNull();
  });

  it("labels the example as invented rather than as market data", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);

    expect(screen.getByRole("button", { name: "Load example" })).toBeInTheDocument();
    expect(screen.getByText(/The example is invented/)).toBeInTheDocument();
  });

  it("drives the metrics table from an import", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);
    paste(screen, fixture());

    const table = screen.getByRole("table", { name: /Your portfolio against BENCH, 2020-01 to 2022-12/ });
    const cells = (metric: string) =>
      within(table).getByRole("rowheader", { name: metric }).closest("tr")?.textContent?.replace(/\s+/g, " ");

    expect(cells("CAGR")).toContain("12.62%");
    expect(cells("CAGR")).toContain("6.15%");
    expect(cells("Annualised volatility")).toContain("3.51%");
    expect(cells("Beta to benchmark")).toContain("2.00");
    expect(cells("Correlation to benchmark")).toContain("1.00");
    expect(cells("Tracking error")).toContain("1.76%");
    expect(cells("Information ratio")).toContain("3.42");
    expect(cells("Rolling 3-year windows ahead")).toContain("100% of 1");
  });

  it("states the risk-free assumption beside the ratio that needs it", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);
    paste(screen, fixture());

    expect(screen.getByText(/constant risk-free rate of 0.0%/)).toBeInTheDocument();
  });

  it("offers the rebalancing and expenses controls, wired to the engine", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);
    paste(screen, fixture());

    expect(screen.getByLabelText("Rebalancing")).toBeInTheDocument();
    const expenses = screen.getByLabelText("Charge each holding its expense ratio");
    expect(screen.queryByLabelText(/AAA expense ratio/)).toBeNull();

    fireEvent.click(expenses);
    expect(screen.getByLabelText(/AAA expense ratio/)).toBeInTheDocument();
    expect(screen.getByLabelText(/BBB expense ratio/)).toBeInTheDocument();
  });

  it("offers a ratio axis on the growth chart and keeps drawing", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);
    paste(screen, fixture());

    const growth = () => screen.getByRole("img", { name: /Growth of 10,000 invested/ });
    expect(growth()).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Ratio (log) value axis"));
    expect(growth().querySelectorAll("path").length).toBeGreaterThan(0);
    // Growth is strictly positive here, so the ratio axis is honest and is not declined.
    expect(screen.queryByText(/A ratio axis was asked for and declined/)).toBeNull();
  });

  it("reports a gap by ticker and month, and refuses to fill it", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);
    paste(screen, fixture({ gapAt: 1 }));

    expect(screen.getByText(/AAA has no value for 2020-02/)).toBeInTheDocument();
    expect(screen.getByText(/A gap is never filled in/)).toBeInTheDocument();
    // AAA was excluded, so the portfolio cannot be run at all — and says so.
    expect(screen.getByText(/No column was imported for AAA/)).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: /Your portfolio against/ })).toBeNull();
  });

  it("names the holding that truncated the common history", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} benchmarkDefault="BENCH" />);
    paste(screen, fixture({ bbbFrom: 6 }));

    expect(screen.getByText("2020-07 → 2022-12")).toBeInTheDocument();
    const text = screen.container.textContent?.replace(/\s+/g, " ") ?? "";
    expect(text).toContain("because BBB starts there");
    expect(text).toContain("nothing is filled in");

    const table = screen.getByRole("table", { name: /2020-07 to 2022-12/ });
    expect(table).toBeInTheDocument();
  });

  it("lets the reader choose which imported column is the benchmark", () => {
    const screen = render(() => <HistoryPanel holdings={HOLDINGS} />);
    paste(screen, fixture());

    const picker = screen.getByLabelText("Benchmark");
    expect(picker).toBeInTheDocument();
    fireEvent.change(picker, { target: { value: "AAA" } });
    expect(screen.getByRole("table", { name: /Your portfolio against AAA/ })).toBeInTheDocument();
  });
});

describe("the invented example", () => {
  it("marks its own results, and stops marking them once the reader edits the paste", async () => {
    render(() => <HistoryPanel holdings={[{ ticker: "AAA", percent: 100 }]} />);

    fireEvent.click(await screen.findByRole("button", { name: /load example/i }));
    expect(await screen.findByText(/these results are of invented data/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^clear$/i }));
    expect(screen.queryByText(/these results are of invented data/i)).toBeNull();
  });
});

describe("the controls the brief asks for", () => {
  it("scales the growth chart to a starting investment without touching any rate", async () => {
    render(() => <HistoryPanel holdings={[...HOLDINGS]} />);
    fireEvent.click(await screen.findByRole("button", { name: /load example/i }));

    const metrics = screen.getByRole("table", { name: /^Your portfolio against BENCH,/ });
    const cagrBefore = within(metrics).getAllByRole("row")[1]?.textContent;

    fireEvent.input(screen.getByLabelText(/starting investment/i), { target: { value: "250000" } });
    fireEvent.blur(screen.getByLabelText(/starting investment/i));

    expect(await screen.findByRole("img", { name: /Growth of 250,000 invested/ })).toBeInTheDocument();
    // The rate is a property of the returns, not of how much was put in.
    expect(
      within(screen.getByRole("table", { name: /^Your portfolio against BENCH,/ })).getAllByRole("row")[1]?.textContent
    ).toBe(cagrBefore);
  });

  it("restricts the period, and falls back to the whole window when asked for a year that is not there", async () => {
    render(() => <HistoryPanel holdings={[...HOLDINGS]} />);
    fireEvent.click(await screen.findByRole("button", { name: /load example/i }));

    const wholeWindow = screen.getByText("Common history").parentElement?.textContent;

    fireEvent.change(screen.getByLabelText("From"), { target: { value: "2021-01" } });
    expect(screen.getByText("Common history").parentElement?.textContent).not.toBe(wholeWindow);

    fireEvent.click(screen.getByRole("button", { name: /whole history/i }));
    expect(screen.getByText("Common history").parentElement?.textContent).toBe(wholeWindow);
  });

  it("prints a return for every complete calendar year", async () => {
    render(() => <HistoryPanel holdings={[...HOLDINGS]} />);
    fireEvent.click(await screen.findByRole("button", { name: /load example/i }));

    const table = await screen.findByRole("table", { name: /calendar-year total return/i });
    // Five years of example data, one header row plus one row each.
    expect(within(table).getAllByRole("row")).toHaveLength(6);
  });
});
