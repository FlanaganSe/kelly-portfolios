# Investable factor products

**Question.** Do listed factor funds deliver their advertised exposure at a cost and
stability that makes them useful implementation candidates?

**Current answer.** Some funds deliver material factor loading. The available return panel
does not reliably identify product alpha, and the answer is highly sensitive to the product
census and replication basis. Treat the audit as implementation evidence, not as proof that
the underlying premium exists or that a product belongs in a portfolio.

**Evidence level:** exploratory fund-implementation audit. Public filings and the current
price-source contracts support useful measurement but not a strong point-in-time,
survivorship-free total-return claim.

## What changed the answer

### The frame

The original US audit used a 2019Q4 census and could see 44 products. The corrected frame
uses the union of the 2019Q4 and 2025Q4 censuses and finds 109. Products launched between
those dates are visible in the corrected descriptive shelf but cannot be treated as choices
available in 2019. The union frame reduces one form of omission while remaining unsuitable
for a historical selection backtest.

This is the durable lesson: define the fund universe independently of the return outcome,
include dead and merged products where the question requires point-in-time inference, and
state which date each constituent became observable.

## The US shelf on the corrected frame

Experiment 013 re-ran the frozen US screen on the union census. It established that several
systematic value and small-value products deliver economically meaningful exposure; it also
showed that the number reaching the exploratory screen changed materially when the frame
changed. The full product grid and frozen outcomes are in the run summaries:

- [`2b8cc7f73aef4d8abee68b7abcde9c1c`](../../research/artifacts/2b8cc7f73aef4d8abee68b7abcde9c1c/summary.md)
- [`3dbc9c7a152a45658d03290a3a3f0033`](../../research/artifacts/3dbc9c7a152a45658d03290a3a3f0033/summary.md)

Current tickers, fees, holdings-derived structure, filing dates, and citations live in the
typed shelf under `src/content/`, not in this synthesis.

### The comparator

Experiments 014 and 015 tested multiple replication bases. A cheap comparator must be able
to express the exposure admitted by the screen; otherwise residual return partly measures
model omission. On the US shelf, the chosen basis moved the sign and number of products
clearing the cost clause. Placebo bases made that sensitivity visible.

That does not imply one universal regression model. A future audit should justify why its
basis spans the product's intended exposure, report coverage and collinearity, and show
sensitivity to plausible alternatives. Product alpha on this short, dependent panel should
normally remain `unresolved`.

Full basis results:

- [US replication bases](../../research/artifacts/643d8ba561cb4407a71e2bb8ff923e89/summary.md)
- [Ex-US replication bases](../../research/artifacts/96e3f95961184e75827aa4c30c16eb99/summary.md)

## What is decision-relevant

For a possible implementation, separate five quantities:

1. loading relative to the incumbent fund being replaced;
2. loading stability across relevant windows;
3. explicit fee and trading cost;
4. turnover, distributions, tax, and wrapper effects;
5. tracking error and the time required for any expected advantage to become visible.

A high loading is evidence that the product delivers exposure, not that the exposure will be
rewarded. A low residual is not automatically a defect if the product cheaply delivers the
intended beta. Conversely, a positive fitted alpha is not persuasive when the basis is
incomplete or the fund history is short.

## Ex-US and emerging products

The ex-US shelf is smaller and the premiums, product histories, regional dependence, tax,
and replication bases differ from the US case. Do not transfer a US loading, size premium,
or comparator result. Experiment 009 measured the union-census shelf; Experiment 015 tested
how much its comparator decided. Detailed outputs:

- [ex-US product audit](../../research/artifacts/46d51d99776543cea36af7f24b48ee4d/summary.md)
- [alternate run](../../research/artifacts/e7c4b0d659484efbbc1a487c8e61b700/summary.md)

## Scope and uncertainty

- Current and union censuses do not provide a survivorship-free historical opportunity set.
- Public fund histories are short relative to the effect and tracking error of interest.
- A product's methodology, benchmark, fee waiver, securities lending, or mandate may change.
- Factor returns are long-short academic series gross of retail implementation.
- The underlying premium and product delivery are separate claims.
- A factor loading and long-only capture fraction measure the same exposure; do not multiply
  them in an expected-return line.

## Next informative work

Build a point-in-time fund panel with dead funds, availability dates, holdings, methodology
changes, and net returns; use holdings-based exposure beside returns; choose expressive cheap
replication bases; and focus inference on loading, cost, and tracking difference rather than
an alpha the available panel cannot resolve.

No product is promoted by this audit. It supplies implementation candidates for a later
portfolio comparison under an explicit investor and funding rule.

## What the comparator decided, measured

See [the comparator](#the-comparator).

## What the ex-US comparator decided, measured

See [the comparator](#the-comparator) and [ex-US products](#ex-us-and-emerging-products).

## Do the twelve incumbents hold? Four of them do not

The current interpretation is in [ex-US products](#ex-us-and-emerging-products); exact
product outcomes remain in the linked artifacts and typed shelf.

## What the value funds also buy

See [what is decision-relevant](#what-is-decision-relevant): delivered exposure is a vector,
and incidental size or profitability loading is not automatically a priced benefit.

## The drag that could not be measured

See [scope and uncertainty](#scope-and-uncertainty).
