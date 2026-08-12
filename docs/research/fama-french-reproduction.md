# Fama-French factor reproduction: the Phase 1 ingestion gate

**Question.** Does this repository's data path — download, raw-byte cache, zip
extraction, multi-table parsing, percent-to-decimal conversion, sample-boundary
selection and monthly summary statistics — reproduce a precisely identified
published table?

**Decision it informs.** Whether Phase 1 of [`docs/the-plan.md`](../the-plan.md)
is closed, and therefore whether any downstream experiment may begin drawing
strategy conclusions from Ken French data. Out of scope: whether any factor is
real, investable, or worth holding.

## Conclusion

**The gate is UNRESOLVED against its predeclared tolerance.** Thirteen of the
fifteen gating cells reproduce; the two that do not are the **standard deviations
of HML and RMW**.

- All five **monthly means** reproduce, the largest miss being RMW at
  +0.0142 percentage points per month against a declared tolerance of 0.02.
- All five **t-statistics** reproduce.
- **HML's standard deviation is 3.0% too low** (2.7926 vs a printed 2.88) and
  **RMW's is 5.1% too high** (2.2490 vs a printed 2.14), against a declared
  tolerance of 0.05 percentage points per month.
- The market factor's standard deviation reproduces to 0.14%, and CMA's to 0.53%.

The diagnosis, evidenced below, is that the currently distributed file's HML and
RMW carry a **different second moment** from the series the authors printed,
concentrated in the part of the sample where those two factors' variance actually
lives (2000–2002), while their first moments and the entire correlation structure
are unchanged. Exact reproduction is **not available at any tolerance**: Ken
French publishes no vintage archive, so the 2013–2014 CRSP vintage the paper used
cannot be obtained. The tolerance was declared before any number was computed and
has not been touched.

**Consequence for this repository.** The ingestion path is trustworthy for
**first moments** and for **cross-sectional structure**. It is **not** established
to reproduce **second moments of HML and RMW** to better than about 5%. Any
downstream result that divides by an HML or RMW volatility — a Sharpe ratio, a
volatility-scaled sleeve, a risk-parity weight, a covariance matrix, a Kelly
fraction — inherits a systematic ±3–5% uncertainty in that denominator that is
**not sampling error** and will not shrink with more data. Report those quantities
with that band attached, or state that the band was not propagated.

## What was targeted

The commissioning brief named "Fama and French (2015) Table 1". **Table 1 of that
paper is the average excess returns of the 25 Size-B/M, Size-OP and Size-Inv test
portfolios, not the factors.** The table holding the mean, standard deviation and
t-statistic of the five monthly factor returns is **Table 4**. The brief's
description matched Table 4 exactly; only the number was wrong, and Table 4 is
what the frozen specification targets.

| Field | Value |
| --- | --- |
| Paper | Eugene F. Fama and Kenneth R. French, "A five-factor asset pricing model", *Journal of Financial Economics* **116**(1), 2015, 1–22 |
| Table | Table 4, Panel A ("Averages, standard deviations, and t-statistics for monthly returns"), first block, **2 × 3 Factors** |
| Rows | Mean, Std dev., t-Statistic |
| Columns | RM−RF, SMB, HML, RMW, CMA (RM−RF is `Mkt-RF` in the data file) |
| Caption sample | "July 1963–December 2013, 606 months" |
| Units | percent per month |
| Statistic definitions | arithmetic mean; sample standard deviation; `t = mean / (sd / sqrt(T))` |

### Where the published values came from

**Verified.** The typeset Elsevier PDF was retrieved from
`https://tevgeniou.github.io/EquityRiskFactors/bibliography/FiveFactor.pdf`
(sha256 `5712e97e9d458b808b8a6ab2387a10327bdc0c6b516aaf33e5ac57baf042f779`,
retrieved 2026-08-12). It carries the running head "E.F. Fama, K.R. French /
Journal of Financial Economics 116 (2015) 1–22", the submission and revision
dates, and the Elsevier copyright line, so it is the published article rather
than a preprint.

Tried and refused, in the order the brief specified: ScienceDirect
(`.../science/article/pii/S0304405X14002323` and `.../am/pii/...`, HTTP 403,
Cloudflare challenge); SSRN (`papers.cfm?abstract_id=2287202`, HTTP 403);
`faculty.chicagobooth.edu/-/media/faculty/eugene-fama/research/...` (404);
`faculty.chicagobooth.edu/john.cochrane/teaching/35150_advanced_investments/FF_Five_Factor.pdf`
(404 live, named as the open-access PDF by the Semantic Scholar API);
`dspace.mit.edu/bitstream/handle/1721.1/103199/...` (429);
`bauer.uh.edu/rsusmel/phd/Fama-French_JFE15.pdf` (403); CiteSeerX, Cornell
eCommons, CBS and Ivey mirrors (404 or 429).

**Cross-checked, not merely extracted.** The paper's own prose in Section 4
independently restates nine of the table's values, and every one agrees with the
extracted table: the 2 × 3 HML mean (0.37) against the 2 × 2 mean (0.28); the
2 × 2 × 2 × 2 and 2 × 2 RMW means and t-statistics (0.25, t = 4.09 versus 0.17,
t = 2.79); the CMA standard deviations and means (1.48 → 1.29 and 0.22 with
t = 3.72 → 0.14 with t = 2.71); HML*S* and HML*B* (0.53, t = 4.05 versus 0.21,
t = 1.69); and "Average SMB returns are 0.29% to 0.30% per month". The market
factor's row is identical across all three sort blocks, as it must be.

**Second printed vintage.** A Wayback Machine snapshot of the November 2013
working-paper draft
(sha256 `24c2f8f345b37aa6de4883b8ea890893b8788e18c985128489685bcf0d5c4550`)
carries the same Table 4 over July 1963 – December 2012, 594 months. It is a
*different vintage of the same table*, not an independent copy of the published
one, and it is used only as a second, non-gating reference point.

## Source vintage actually used

**Verified as of 2026-08-12.** Recorded in
[`research/data-manifests/french_us_ff5_monthly.json`](../../research/data-manifests/french_us_ff5_monthly.json).

| Field | Value |
| --- | --- |
| URL | `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip` |
| `sha256_raw` | `cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b` (11 901 bytes) |
| `sha256_normalized` | `e1a9870b29d8302c68bc2e8daa902bf5f01039b6420c8e48eb21d9c781fca752` |
| `Last-Modified` | Mon, 03 Aug 2026 19:17:07 GMT |
| Retrieved | 2026-08-12T06:19:22Z |
| File's own preamble | "This file was created using the **202606** CRSP database." |
| Monthly table | 756 rows, 1963-07 to 2026-06, source units percent, `RF` present but unused |
| Parser | `french/1.0.0` |

The sha256 pins **which file was used**. It does not establish what was publicly
available in 2014. Ken French rebuilds the entire history from the current CRSP
vintage on every rebuild and publishes no vintage archive.

## Results

Computed from the pinned file over 1963-07 to 2013-12, 606 months, in percent per
month. Run `f8972356df0648cf8867b1c742261bda`, specification hash
`5bf03adea82069ee00c7e875321c450983626b0d50beb5374cf54c5d56075976`.

### Against the printed table

| Factor | Mean pub. | Mean ours | Δ | SD pub. | SD ours | Δ | *t* pub. | *t* ours | Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mkt-RF | 0.50 | 0.5010 | **+0.0010** | 4.49 | 4.4837 | −0.0063 | 2.74 | 2.7506 | +0.0106 |
| SMB | 0.29 | 0.2788 | −0.0112 | 3.07 | 3.0451 | −0.0249 | 2.31 | 2.2541 | −0.0559 |
| HML | 0.37 | 0.3826 | +0.0126 | 2.88 | 2.7926 | **−0.0874 ✗** | 3.20 | 3.3729 | +0.1729 |
| RMW | 0.25 | 0.2642 | +0.0142 | 2.14 | 2.2490 | **+0.1090 ✗** | 2.92 | 2.8916 | −0.0284 |
| CMA | 0.33 | **0.3256** | −0.0044 | 2.01 | 1.9993 | −0.0107 | 4.07 | 4.0092 | −0.0608 |

Tolerances, declared in the specification before anything was computed: mean
0.02, standard deviation 0.05, t-statistic 0.30 (derived from the other two, not
independent). **Bold** = rounds to the printed value exactly (within ±0.005).
**✗** = outside the gate.

### Full statistic set

Sharpe ratios use a risk-free rate of **exactly zero**; see "Which series are
already excess" below. HAC is Newey-West with a Bartlett kernel and bandwidth
`L = floor(4·(T/100)^(2/9)) = 5` at T = 606, a function of sample size alone.

| Factor | Mean %/mo | Ann. premium %/yr | SD %/mo | Ann. vol %/yr | Sharpe (ann.) | SE iid | *t* iid | SE HAC | *t* HAC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mkt-RF | 0.5010 | 6.012 | 4.4837 | 15.532 | 0.3871 | 0.1821 | 2.7506 | 0.1943 | 2.5787 |
| SMB | 0.2788 | 3.346 | 3.0451 | 10.549 | 0.3172 | 0.1237 | 2.2541 | 0.1309 | 2.1299 |
| HML | 0.3826 | 4.591 | 2.7926 | 9.674 | 0.4746 | 0.1134 | 3.3729 | 0.1336 | 2.8632 |
| RMW | 0.2642 | 3.170 | 2.2490 | 7.791 | 0.4069 | 0.0914 | 2.8916 | 0.1032 | 2.5598 |
| CMA | 0.3256 | 3.907 | 1.9993 | 6.926 | 0.5642 | 0.0812 | 4.0092 | 0.0920 | 3.5382 |

Annualisation conventions: premium `= 12 × monthly mean` (arithmetic, **not** a
compound growth rate); volatility `= sqrt(12) × monthly SD`; Sharpe
`= sqrt(12) × monthly Sharpe`. All three assume serially independent monthly
returns, which these are not — the gap between `SE iid` and `SE HAC` (7% to 18%)
is the size of that assumption. The published t-statistics are the i.i.d. ones,
so those are what the gate compares.

### Which series are already excess, and which are not

**`Mkt-RF`, `SMB`, `HML`, `RMW` and `CMA` are all already excess or long-short
returns. `RF` was not subtracted from any of them.** `Mkt-RF` is the value-weight
market return already net of the one-month bill; the other four are
zero-net-investment long-short spreads whose financing is netted inside the
spread. Only `RF` itself is a cash rate, and it is not used.

Subtracting `RF` a second time is the classic error here and it is invisible in
the output, because the result is still a plausible small monthly number. The
experiment measures it rather than asserting its absence: doing so would shift
**every** factor mean by **−0.4153 percentage points per month** (−4.98 pp/yr),
turning HML's premium from +0.383 to −0.033 and RMW's from +0.264 to −0.151, and
leaving Mkt-RF at +0.086. Every long-short factor would flip sign.

## Diagnosis of the two failing cells

### Verified facts

1. **The failure is confined to second moments of two factors.** Variance ratios
   (ours ÷ printed): Mkt-RF 0.997, SMB 0.984, CMA 0.989, **HML 0.940, RMW 1.104**.
2. **The same two cells fail against both printed vintages, by the same amount.**
   Against the 594-month November 2013 draft: HML SD −0.0851, RMW SD +0.1136
   (against 606-month 2015: −0.0874 and +0.1090). Two independently typeset
   vintages a year apart give the same discrepancy, so this is not the 2013→2014
   revision cycle.
3. **The correlation structure is unchanged.** All ten of Table 4 Panel C's
   2 × 3 correlations reproduce within 0.06, and nine within 0.033. The paper
   itself puts the standard error of these correlations at 0.04, so every one is
   inside about 1.5 standard errors. HML–CMA reproduces at 0.6983 against a
   printed 0.70; HML–RMW at 0.0730 against 0.08.
4. **HML's and RMW's variance is concentrated where restatement bites hardest.**
   Of RMW's 606-month variance, **49.5% comes from the 36 months of 2000–2002**;
   HML 22.0%, versus Mkt-RF 10.3%. RMW's single largest month is 2000-02 at
   −18.95%; its 2000s decade standard deviation is 3.90 against 1.48–1.69 in every
   other decade.
5. **The sample boundary and file integrity are not the cause.** The window holds
   exactly 606 strictly increasing, gapless, duplicate-free months with no missing
   values and no sentinel leakage. Shifting the window one month forward moves the
   Mkt-RF mean from 0.5010 to 0.4962; one month back selects only 605 rows and is
   caught. Reading the annual table instead of the monthly one gives 6.551%/yr.

### Inference (not verified)

CRSP and Compustat restate delistings, share counts, prices and accounting data
retroactively. HML and RMW are the two factors built from the extremes of
book-to-market and operating profitability, which is precisely the cohort — small,
unprofitable, high-growth firms around the dot-com period — where twelve years of
restatement and delisting reclassification change the most. That would perturb the
extreme portfolios' monthly returns without much changing their long-run average,
which is the pattern observed: first moments and correlations intact, second
moments of exactly those two factors moved by −6% and +10% in variance.

**This is a hypothesis, not a finding.** Distinguishing it from a subtle
construction difference between the paper and the current library file requires
the 2013–2014 vintage, which does not exist publicly. The Ken French data library
page states the current HML and RMW construction in the same terms the paper uses
and records no definitional change, but a page that does not mention a change is
not evidence that none occurred.

### Rounding

Printing precision alone accounts for ±0.005 in each printed cell. Recomputing
the published t-statistics from the published rounded means and standard
deviations gives 2.74 / 2.33 / 3.16 / 2.88 / 4.04 against printed
2.74 / 2.31 / 3.20 / 2.92 / 4.07, confirming that the authors' t-statistics come
from unrounded inputs and that the printed rows are independently rounded.
Rounding cannot explain a 0.087 or 0.109 discrepancy.

## What passing this gate does NOT establish

Stated because the failure mode of a green integration test is that it gets
quoted as evidence of something it never tested.

- It does **not** verify portfolio accounting, rebalancing, transaction costs, tax
  lots, corporate actions, insolvency behaviour, missing-data policy, look-ahead
  protection, or optimisation constraints. **None of them is exercised.**
- The published factor file **already contains the authors' own calculated
  returns**. Matching their table shows we read and summarised their numbers
  correctly; it does not show we could have computed them.
- It **can match despite compensating errors**. Two offsetting mistakes in the
  unit transform and the window would produce the same table.
- Every figure is **gross** of transaction costs, shorting costs, fees and taxes,
  because the source series are. The long-short series are not investable.
- A sha256 proves **which file** was used, never **what was available** at an
  earlier date. Nothing here is point-in-time.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_phase1_ff_reproduction --view-results
uv run pytest tests/integration/test_phase1_reproduction.py      # offline
uv run pytest -m network tests/integration/test_phase1_reproduction.py
```

The frozen specification is
[`research/experiments/phase1_ff_reproduction.yaml`](../../research/experiments/phase1_ff_reproduction.yaml)
and the code is
[`research/src/portfolio_edge/experiments/exp_phase1_ff_reproduction.py`](../../research/src/portfolio_edge/experiments/exp_phase1_ff_reproduction.py).
The run, its git commit, specification hash, dataset-manifest hash, artifact
hashes and the `results_viewed` event are in
[`research/ledger.jsonl`](../../research/ledger.jsonl). Environment: Python 3.12,
NumPy 2.x, deterministic; the specification's seed is recorded but nothing is
resampled.

The specification refuses to run against a file whose sha256 is not the pinned
one. When Ken French publishes a new vintage this experiment will **abort rather
than report numbers**, and a new specification must be frozen against the new
hash — which is the point.

## Open questions

- Can any 2013–2014 vintage of the 5-factor file be obtained (a co-author's
  archive, a replication package, an institutional mirror)? That is the single
  observation that would settle the diagnosis.
- Do the HML and RMW second-moment differences persist in the 2 × 2 and
  2 × 2 × 2 × 2 blocks of Table 4, which use different portfolio intersections?
  The library distributes only the 2 × 3 file, so this needs the six underlying
  Size-B/M and Size-OP portfolios.
- Is the discrepancy localised to 2000–2002, or spread? Answering it requires the
  published monthly series, which was never distributed.
