# Loading comparability, and the wrapper exposure this repository said it could not measure

**Question.** Two questions that turn out to have the same answer. First: can a stacked
fund's *delivered* trend exposure be measured at all, when no research-grade price feed is
licensed? Second: are the factor loadings published on the fund shelf comparable with one
another?

**Decision it informs.** Whether the 30% stacked-wrapper line in the candidate portfolio
rests on a filed notional or on a measured exposure, and whether any ranking of value
products by loading — the ranking that picks which value fund to hold — means anything as
published.

**Out of scope.** Whether a trend sleeve is worth holding, which is
[decision 0004](../decisions/0004-no-sleeve-promoted.md) and is untouched here; and what
the trend premium is, which no window on this page could resolve. A loading is *exposure
delivered*, not *return earned*. Nothing here signs a premium.

`as of 2026-08-23`. `exploratory`. No specification was frozen before these numbers were
seen and no experiment is registered for them. Reproduce with
`cd research && uv run python -m portfolio_edge.studies.loading_windows`; the arithmetic is
in [`loading_windows.py`](../../research/src/portfolio_edge/studies/loading_windows.py) and
the filing reads in
[`_loading_windows_tables.py`](../../research/src/portfolio_edge/studies/_loading_windows_tables.py).

---

## Conclusion

1. **A wrapper's delivered trend exposure is measurable, and RSST's is +0.681.** Over its 31
   clean filed months (2023-10 … 2026-04), regressing RSST's own filed monthly total return
   in excess of cash on the US market and on AQR's TSMOM index gives a trend loading of
   **+0.681, 95% [+0.406, +0.955]**, *t* = 4.86, beside an equity beta of **+0.979
   [+0.763, +1.195]**. Four research pages, two study modules and the application's own
   content all asserted that this could not be done. It could; every one of those claims has
   been corrected in place.
2. **The negative control behaved, which is what makes the number readable.** RSSB — same
   sponsor, same wrapper structure, Treasury futures instead of a trend book — returns a
   trend loading of **−0.101 [−0.358, +0.155]** on 29 months, with the same equity beta near
   one (+0.947). The design discriminates: it finds trend where there is a trend book and
   not where there is not.
3. **Against a fund an investor could actually hold, RSST reads +0.857.** Regressed on DBMF's
   own filed excess return rather than on a vendor index, over the 30 months both file:
   **+0.857 [+0.719, +0.995]**, R² 0.878. About 86 cents of DBMF per dollar of RSST.
4. **The published shelf loadings are not comparable with one another.** Each was fitted on
   the months that fund had filed, so the nine US value products carry windows from 36 to 72
   months. Refitted on the 36 months all nine share, the ordering changes: **AVLV falls from
   mid-table to last** and VTV — a 3 bp cap-weighted index fund — passes four systematic
   funds. On the managed-futures shelf, **FMF rises from +0.303 to +0.476 and overtakes CTA**.
5. **The matched ranking is a snapshot, not a stable ordering.** VTV's own HML loading over
   rolling 36-month windows runs from **+0.143 to +0.520** — a range wider than the entire
   spread between the nine funds on the matched window. Thirty-six months is roughly one
   market regime. Treat any ordering here as a fact about 2023–2025.
6. **What is fixed, and what is not.** `src/content/shelf.ts` no longer stores a month
   count; every loading carries its window, and `rankLoadings` in `src/lib/loadings.ts`
   throws rather than sorting a mixed-window set. Nothing here re-estimates the published
   numbers: they stand on their own windows, as fitted.

---

## 1. Why this was thought impossible, and why it is not

[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) records that no
free *price* feed reachable from this project documents a total-return contract, a
corporate-action policy or a revision history. That finding stands.

It does not reach this measurement, because **Form N-PORT is not a price feed**. Item B.5 of
the form asks a fund to report *its own* monthly total return for each of the three months
in the reporting period, per share class — net of the fund's own ongoing fees and with
distributions reinvested, on a signed filing the SEC archives permanently. It is the fund's
number, not a quotient of two scraped closing prices.
[Decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) says exactly this:
0002's finding "does not automatically reach non-distributing assets, reader-supplied data,
source reproduction, cross-checks, or sources with different contracts."

`portfolio_edge.data.nport` has read Item B.5 since Experiment 008, and Experiments 008, 009,
012 and 013 all built their fund returns from it. **Nothing new was needed to measure a
wrapper. Nobody had pointed the existing reader at one.**

The places that said otherwise are corrected in place:
[stacking](stacking-and-effective-breadth.md) (twice), [the notional
budget](leverage-and-the-notional-budget.md), [timing
rules](timing-rules-on-the-equity-sleeve.md), the two study modules that build those pages'
tables, and the shelf, family, portfolio and confidence content the application renders.

**What it still does not give.** Public N-PORT filings begin in 2019 and RSST began trading
in 2023-09, so the window is 31 months whatever the source. The figures are fund-reported
and unaudited. This is `exploratory` work and cannot promote a sleeve.

---

## 2. The wrapper's trend loading

**Design.** Monthly. The fund's filed Item B.5 return, less the one-month Treasury bill from
the same Ken French file that supplies the market factor, regressed on the US market excess
return and on AQR's TSMOM index. Newey-West standard errors at six lags — the lag count
Experiments 008, 009 and 013 all fix — and 95% normal intervals. The AQR workbook is pinned
to the hash Experiment 008 froze, and the study aborts on a mismatch rather than reporting a
loading against an unrecognised vintage.

**Why the market term is there.** A standalone trend fund has no equity leg, so Experiment
008 regressed those funds on TSMOM alone. A *stacked* wrapper is one dollar of equity plus
one dollar of trend, and omitting the market would push the equity return into whatever the
trend index happened to do in the same months. The market term is the difference between
measuring a wrapper and measuring a fund.

**The launch stub.** RSST commenced operations on 2023-09-05 and filed a return for
September 2023 covering about three quarters of a month. Regressed against a whole month of
factor returns that observation is not small, it is differently scaled, and its beta is
attenuated by the fraction of the month the fund did not exist. It is dropped, which is
[Experiment 013](../../research/experiments/exp_013_us_products_union_frame.yaml)'s own
launch-cut rule. That is the difference between 32 filed months and 31 clean ones.

| | Loading | 95% interval | *t* | Months | Window | Smallest detectable |
| --- | ---: | :---: | ---: | ---: | --- | ---: |
| **RSST on TSMOM** | **+0.681** | [+0.406, +0.955] | 4.86 | 31 | 2023-10…2026-04 | 0.392 |
| RSST equity beta | +0.979 | [+0.763, +1.195] | 8.87 | 31 | 2023-10…2026-04 | 0.309 |
| RSST on TSMOM, first half | +0.618 | [+0.171, +1.066] | 2.71 | 15 | 2023-10…2024-12 | 0.640 |
| RSST on TSMOM, second half | +0.686 | [+0.381, +0.992] | 4.40 | 16 | 2025-01…2026-04 | 0.437 |
| **RSSB on TSMOM** (control) | **−0.101** | [−0.358, +0.155] | −0.77 | 29 | 2023-12…2026-04 | 0.366 |
| RSSB equity beta | +0.947 | [+0.759, +1.135] | 9.86 | 29 | 2023-12…2026-04 | 0.269 |
| **RSST on DBMF** | **+0.857** | [+0.719, +0.995] | 12.16 | 30 | 2023-10…2026-03 | 0.197 |
| RSST equity beta, same fit | +0.972 | [+0.895, +1.050] | 24.69 | 30 | 2023-10…2026-03 | 0.110 |
| DBMF on TSMOM, same months | +0.722 | [+0.522, +0.922] | 7.09 | 30 | 2023-10…2026-03 | 0.285 |

"Smallest detectable" is the minimum detectable loading at 80% power and 5% significance —
2.802 standard errors. Read it as the resolution of the instrument. RSST's is 0.392, so this
window could not have distinguished a true loading of 0.3 from zero, and the fact that it
found 0.681 anyway is the point.

**What the number means in plain terms.** RSST's own filing says it holds one dollar of
US-equity notional and one dollar of trend notional per dollar of capital. The regression
says the equity dollar arrived essentially intact (+0.979) and the trend dollar arrived at
roughly seven tenths (+0.681). That gap is what a 99 bp fee, a volatility target set
independently of the index, and a different trend book than AQR's look like from the
outside. **The interval does not exclude a full dollar**: +0.955 is inside it. Thirty-one
months cannot tell 0.7 from 1.0.

**Stability.** The two halves read +0.618 and +0.686. That is reassuring and worth almost
nothing on its own: with 15 and 16 months, each half's smallest detectable loading is 0.64
and 0.44, so the halves could not have disagreed detectably even if the fund had changed.

### The negative control

This is the part that makes the rest credible. RSSB is the same sponsor, the same wrapper
mechanics, the same Cayman-subsidiary-free 1940-Act structure, and a Treasury-futures
overlay in place of a trend book. If the +0.681 were an artefact — of stacked wrappers, of
2023–2026 returns, of the regression — RSSB would show it too.

It does not. **−0.101 [−0.358, +0.155]**, a *t* of −0.77, on a window whose resolution is
0.366. The design finds trend where a trend book exists and nothing where none does.

The one caveat: RSSB began trading in 2023-02 but EDGAR lists no NPORT-P filing for its
series before the one covering 2023-11, so the control has 29 months against RSST's 31 and
starts two months later. Both windows are inside the same regime, and the control's own
resolution is stated above.

### Against a held fund instead of a vendor index

AQR's TSMOM index states no fee, no transaction cost, no slippage and no financing basis, a
flag [trend](trend-marginal-value.md) raises before any number. Regressing RSST on DBMF's
own filed excess return replaces the vendor construction with a fund an investor could
buy: **+0.857 [+0.719, +0.995]**, R² 0.878. About 86 cents of DBMF per dollar of RSST, with
the tightest interval on this page — because both sides are net of real costs, so the
mismatch that widens the vendor regression is gone.

Consistency check: DBMF's own loading on TSMOM over those same 30 months is **+0.722**,
against the **+0.671** the shelf publishes on DBMF's own 54-month window. Same fund, same
index, different months, 0.05 apart. That is the comparability problem in one line, and §4
is about it.

### The other wrappers: counted, not estimated

| Fund | Filed months | Range | Verdict |
| --- | ---: | --- | --- |
| MATE | 6 | 2025-12…2026-05 | Declined |
| CTAP | 3 | 2026-01…2026-03 | Declined |
| JPFP | 0 | — | No Form N-PORT exists |

A three-parameter regression needs 36 months under Experiments 009's and 013's own floor. At
six months the smallest detectable loading would exceed 1.0 — the instrument could not tell
a full dollar of trend from none — so an estimate would be a statement about the window
dressed as a statement about the fund. **The count is the finding.** CTAP's 2025-12 stub is
dropped on the same launch rule as RSST's. JPFP commenced 2026-05-27 and its first filing is
due 2026-08-29 or 2026-09-29; the shelf already carries that review trigger.

---

## 3. The method, proved before it was used

Every loading below was first refitted on its **own published window** and checked against
the published number. This is the check that separates "a different answer" from "a
different method".

Twenty published loadings across three experiments and two panels, every one reproduced to
within 0.0005:

| Panel | Funds | Loadings checked | Largest gap |
| --- | --- | ---: | ---: |
| US FF5+UMD (Experiment 013) | VTV, AVLV, DFLV, DFUV, AVUV, DFSV, DFAT, RPV, VBR | 9 | 0.0005 |
| AQR TSMOM (Experiment 008) | DBMF, CTA, KMLM, FMF, WTMF | 5 | 0.0004 |
| Developed ex-US FF5+UMD (Experiment 009) | AVDV, DISV, IVLU | 6 | 0.0004 |

The ex-US funds are there for a second reason. The shelf publishes a month count for each
loading, and the window is recovered from it by taking the trailing *n* months ending
2025-12, the last month of the frozen common period in all three experiments. That rule is a
**derivation**, so it is checked rather than assumed — and it holds on all three panels.

---

## 4. The US value shelf, refitted on its common window

The nine US value products were fitted on 36 to 72 months each. They share 36 months,
2023-01 … 2025-12, which is DFLV's own window and therefore the most any refit can use
without inventing history.

| Fund | Published | Its window | Matched (2023-01…2025-12) | 95% interval | Smallest detectable |
| --- | ---: | --- | ---: | :---: | ---: |
| RPV | +0.710 | 2020-01…2025-12 (72m) | **+0.836** | [+0.666, +1.006] | 0.243 |
| DFLV | +0.637 | 2023-01…2025-12 (36m) | **+0.637** | [+0.476, +0.798] | 0.230 |
| DFUV | +0.515 | 2022-06…2025-12 (43m) | **+0.582** | [+0.426, +0.739] | 0.224 |
| VTV | +0.337 | 2020-01…2025-12 (72m) | **+0.520** | [+0.288, +0.752] | 0.331 |
| DFSV | +0.442 | 2022-03…2025-12 (46m) | **+0.494** | [+0.293, +0.696] | 0.288 |
| AVUV | +0.537 | 2020-01…2025-12 (72m) | **+0.467** | [+0.250, +0.685] | 0.311 |
| DFAT | +0.433 | 2021-07…2025-12 (54m) | **+0.466** | [+0.323, +0.608] | 0.204 |
| VBR | +0.410 | 2020-01…2025-12 (72m) | **+0.451** | [+0.347, +0.554] | 0.148 |
| AVLV | +0.322 | 2021-10…2025-12 (51m) | **+0.413** | [+0.271, +0.554] | 0.202 |

DFLV's two columns are identical because the matched window *is* DFLV's window. That is a
useful internal check, not a coincidence.

**What moved.** Every fund's loading rises on the matched window — 2023–2025 was a period in
which measured value exposure ran higher across the board — but not by the same amount, and
that is what reorders things. On the published numbers AVLV (+0.322) sits above only VTV; on
the matched window it is **last of nine**. VTV, a 3 bp cap-weighted index fund that is not a
tilt at all, moves from eighth to fourth and passes AVUV, DFAT and VBR.

**What did not move.** RPV is the deepest value exposure on either reading and DFLV is second
on both. The extremes are robust; the middle of the table is not.

### How much of this is signal

Very little, and the page must say so.

- **The intervals overlap almost completely.** Six of the nine matched loadings lie inside
  [+0.413, +0.582]. Their intervals are 0.15 to 0.33 wide at 80% power. **No pair inside
  that band is distinguishable from another on 36 months.** The reordering is real as
  arithmetic and mostly noise as inference.
- **VTV's own loading is not stable across windows.** Rolling 36-month windows over its 81
  filed months give 46 estimates ranging from **+0.143** (2021-12…2024-11) to **+0.520**
  (2023-01…2025-12). The whole spread between the nine funds on the matched window is 0.42;
  a single fund's own estimate moves 0.38 depending on which 36 months you pick.
- **The matched window is the most recent 36 months.** It is not a random draw from history;
  it is the period every young fund happens to have existed for, which is also the period the
  value spread was widest.

**So the honest statement is:** the published ordering is not an ordering, and the matched
ordering is one regime's ordering. Use the matched column to see that AVLV's advertised
exposure is at the bottom of its peer group on common months, not to conclude that RPV
delivers twice AVLV's value exposure as a durable matter.

---

## 5. The managed-futures shelf, on two matched windows

Same treatment. The five products were fitted on 46 to 78 months each.

| Fund | Published | Its window | Matched, 46m (2022-03…2025-12) | Wrapper-comparable, 30m (2023-10…2026-03) |
| --- | ---: | --- | ---: | ---: |
| DBMF | +0.671 | 2021-07…2025-12 (54m) | **+0.788** | +0.722 |
| RSST | — | — | — | **+0.698** |
| CTA | +0.475 | 2022-03…2025-12 (46m) | +0.475 | **+0.584** |
| FMF | +0.303 | 2019-07…2025-12 (78m) | **+0.476** | **+0.515** |
| WTMF | +0.099 | 2019-09…2025-12 (76m) | +0.066 | +0.203 |
| KMLM | +0.245 | 2021-01…2025-12 (60m) | +0.260 | +0.137 |

Two windows are reported because two different questions are being asked. The 46-month
window is the one all five standalone funds share and is the right basis for ranking them
against each other. The 30-month window is the one RSST also occupies, and is the only basis
on which a wrapper's trend delivery can be compared with a fund's.

**What moved.** FMF's published +0.303 was the tightest of the four rejections against the
frozen 0.50 bar — "clearly under the bar", the shelf says. On the 46 months it shares with
the others it reads **+0.476 [+0.373, +0.578]**, and on the 30 months it shares with RSST
**+0.515 [+0.407, +0.623]**, which is *above* the bar. CTA moves from +0.475 to +0.584 on
the wrapper window. FMF and CTA swap places between the two matched windows.

**This does not overturn Experiment 008's verdicts, and must not be read as doing so.** Those
verdicts were frozen against a specification, on stated windows, with a bar chosen in
advance; a refit on a different window is a different measurement and cannot retroactively
pass a falsifier. What it establishes is narrower and still important: **FMF's rejection was
substantially a statement about 2019–2021**, months in which the other funds did not exist,
and a reader comparing the published +0.303 against DBMF's +0.671 is comparing 78 months
with 54.

**Where RSST lands.** On the 30 months all six share, RSST's +0.698 sits between DBMF's
+0.722 and CTA's +0.584 — a stacked wrapper delivering trend exposure comparable to a
standalone trend fund, per dollar of *notional*, on top of a full dollar of equity. Its
interval is the widest in the column (0.457 detectable) because it is the youngest fund.

---

## 6. What changed in the code

- **`src/content/shelf.ts` no longer has a `months` field.** Every loading carries
  `window: { from, to }`, and the length is derived from it, so a month count and a window
  can no longer disagree. Where no experiment recorded a window the field is an explicit
  `null`, never an inferred range.
- **`src/lib/loadings.ts` refuses incomparable comparisons.** `rankLoadings` throws
  `IncomparableWindowsError` on a set of loadings with different windows, different factors
  or different panels, and names the windows it found. This follows
  `studies/outperformance_horizon.aggregate()`, which raises rather than adding results
  measured against different benchmarks.
- **The fund page prints the window beside every loading**, so the comparability problem is
  visible to a reader and not only to a test.
- **`src/content/shelf.test.ts` pins the invariant**: the nine US value loadings must not be
  rankable, they must share exactly 36 months, and every loading must carry a window or an
  explicit null.
- **RSST and RSSB now carry a TSMOM loading on the shelf**, with their own windows. Their
  alphas stay `null`: over 29 to 31 months an alpha is a statement about the window.

---

## Verified, assumed, open

**Verified here.** Twenty published loadings reproduced on their own windows to within
0.0005, across three experiments and two panels. RSST's and RSSB's trend loadings and equity
betas from their own Form N-PORT filings. The matched-window refits and their intervals.
VTV's rolling-window range. The filed-month counts for MATE, CTAP and JPFP.

**Assumed.** That a published month count identifies the trailing window ending 2025-12 —
derived from the three specifications and checked on all three panels, but a derivation.
That Item B.5 returns are what the filer says they are; they are unaudited. That six
Newey-West lags remain the right truncation on a 30-month window; it is the frozen choice
elsewhere in this repository, and the shorter samples here would justify fewer. At three
lags RSST's trend loading is unchanged at +0.681 with a wider interval, [+0.393, +0.968].

**Open.**

- **Whether +0.681 is 0.7 or 1.0.** The interval spans both. Two more years of filings would
  roughly halve the standard error. The review date is when RSST's filed history reaches 48
  months, in 2027-09.
- **Whether the shortfall is fee, volatility target, or a different book.** A loading cannot
  separate them. RSST's prospectus targets 100% of a managed-futures strategy; the filing
  shows a gross notional of about 294% of net assets on the trend leg to deliver it. Whether
  ~0.7 of AQR's index is the intended delivery or a shortfall is an issuer question, not a
  regression question.
- **MATE, CTAP and JPFP.** Re-run when each reaches 36 filed months: MATE around 2028-11,
  CTAP around 2028-12, JPFP not before 2029-05.
- **Whether any matched ordering survives a second regime.** It cannot be known from 36
  months. The only cure is time.
- **The other panels.** The ex-US and emerging shelves have the same comparability defect
  and have not been refitted here. Their windows are now visible in `shelf.ts`, which is the
  precondition for doing it.
