# Fama–French factor reproduction: the Phase 1 ingestion gate

**Question.** Does this repository's data path — download, raw-byte cache, zip extraction,
multi-table parsing, percent-to-decimal conversion, sample-boundary selection and monthly
statistics — reproduce a precisely identified published table?

**Decision it informs.** Whether any downstream experiment may draw strategy conclusions
from Ken French data. Out of scope: whether any factor is real, investable, or worth
holding.

---

## Conclusion

**The gate is `unresolved` against its predeclared tolerance.** Thirteen of fifteen gating
cells reproduce; the two that do not are **the standard deviations of HML and RMW**.

- All five **monthly means** reproduce, the largest miss being RMW at +0.0142 pp/month
  against a declared tolerance of 0.02.
- All five **t-statistics** reproduce, and all ten cross-factor correlations.
- **HML's standard deviation is 3.0% too low** (2.7926 vs a printed 2.88) and **RMW's is
  5.1% too high** (2.2490 vs 2.14), against a declared tolerance of 0.05 pp/month.

**Exact reproduction is not available at any tolerance**: Ken French publishes no vintage
archive, so the 2013–14 CRSP vintage the paper used cannot be obtained. **The tolerance was
declared before any number was computed and has not been touched.**

**Consequence.** The ingestion path is trustworthy for **first moments** and for
**cross-sectional structure**. It is **not** established to reproduce **second moments of
HML and RMW** to better than about 5%. Any downstream result that divides by an HML or RMW
volatility — a Sharpe ratio, a volatility-scaled sleeve, a risk-parity weight, a covariance
matrix, a Kelly fraction — **inherits a systematic ±3–5% uncertainty that is not sampling
error and will not shrink with more data.** Report those quantities with the band attached,
or state that it was not propagated.

---

## What was targeted, and where the published values came from

The commissioning brief named "Fama and French (2015) Table 1". **Table 1 of that paper is
the average excess returns of the 25 test portfolios, not the factors.** The table holding
the mean, standard deviation and t-statistic of the five monthly factor returns is **Table
4, Panel A, first block (2 × 3 Factors)**, over July 1963 – December 2013, 606 months, in
percent per month. The brief's description matched Table 4 exactly; only the number was
wrong, and Table 4 is what the frozen specification targets.

**The typeset Elsevier PDF was retrieved** (sha256 `5712e97e…`, 2026-08-12) and carries the
running head, submission dates and copyright line, so it is the published article rather
than a preprint. Eight other routes — ScienceDirect, SSRN, Chicago Booth, MIT DSpace,
CiteSeerX and three mirrors — returned 403, 404 or 429.

**Cross-checked, not merely extracted.** The paper's own prose in Section 4 independently
restates nine of the table's values and every one agrees with the extracted table. A
Wayback snapshot of the November 2013 working paper carries the same table over 594 months
and is used only as a second, non-gating reference point.

---

## Results

From the pinned file over 1963-07…2013-12, 606 months, percent per month. Run
`f8972356df0648cf8867b1c742261bda`, specification hash `5bf03adea820…`.

| Factor | Mean pub. | Mean ours | Δ | SD pub. | SD ours | Δ | *t* pub. | *t* ours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mkt-RF | 0.50 | 0.5010 | +0.0010 | 4.49 | 4.4837 | −0.0063 | 2.74 | 2.7506 |
| SMB | 0.29 | 0.2788 | −0.0112 | 3.07 | 3.0451 | −0.0249 | 2.31 | 2.2541 |
| **HML** | 0.37 | 0.3826 | +0.0126 | **2.88** | **2.7926** | **−0.0874 ✗** | 3.20 | 3.3729 |
| **RMW** | 0.25 | 0.2642 | +0.0142 | **2.14** | **2.2490** | **+0.1090 ✗** | 2.92 | 2.8916 |
| CMA | 0.33 | 0.3256 | −0.0044 | 2.01 | 1.9993 | −0.0107 | 4.07 | 4.0092 |

Tolerances declared before anything was computed: mean 0.02, standard deviation 0.05,
t-statistic 0.30.

**Which series are already excess, and which are not.** `Mkt-RF`, `SMB`, `HML`, `RMW` and
`CMA` are **all already excess or long-short returns, and `RF` was not subtracted from any
of them.** Subtracting it a second time is the classic error here and it is **invisible in
the output**, because the result is still a plausible small monthly number. The experiment
measures it rather than asserting its absence: doing so would shift every factor mean by
**−0.4153 pp/month (−4.98 pp/yr)** and **flip every long-short sign.**

Annualisation conventions, stated because they are silent traps: premium `= 12 × monthly
mean` (arithmetic, **not** a compound growth rate); volatility `= sqrt(12) × monthly SD`.
Both assume serially independent monthly returns, which these are not — **the gap between
the iid and HAC standard errors is 7% to 18%, which is the size of that assumption.** The
published t-statistics are the iid ones, so those are what the gate compares.

---

## Diagnosis of the two failing cells

**Verified.**

1. **The failure is confined to second moments of two factors.** Variance ratios (ours ÷
   printed): Mkt-RF 0.997, SMB 0.984, CMA 0.989, **HML 0.940, RMW 1.104**.
2. **The same two cells fail against both printed vintages, by the same amount** — HML
   −0.0851 and RMW +0.1136 against the 594-month draft, versus −0.0874 and +0.1090 against
   the published table. **Two independently typeset vintages a year apart give the same
   discrepancy, so this is not the 2013→2014 revision cycle.**
3. **The correlation structure is unchanged.** All ten correlations reproduce within 0.06
   and nine within 0.033, against the paper's own standard error of 0.04.
4. **HML's and RMW's variance is concentrated where restatement bites hardest.** Of RMW's
   606-month variance, **49.5% comes from the 36 months of 2000–2002**; HML 22.0%, against
   Mkt-RF's 10.3%. RMW's 2000s decade standard deviation is 3.90 against 1.48–1.69 in every
   other decade.
5. **The sample boundary and file integrity are not the cause.** The window holds exactly
   606 strictly increasing, gapless, duplicate-free months with no missing values and no
   sentinel leakage. Shifting it one month forward moves the Mkt-RF mean to 0.4962; one
   month back selects 605 rows and is caught.
6. **Rounding cannot explain it.** Recomputing the published t-statistics from the published
   rounded inputs gives 2.74 / 2.33 / 3.16 / 2.88 / 4.04 against printed 2.74 / 2.31 / 3.20
   / 2.92 / 4.07, confirming the printed rows are independently rounded from unrounded
   inputs. **Printing precision accounts for ±0.005, not 0.087 or 0.109.**

**Inference, not a finding.** CRSP and Compustat restate delistings, share counts, prices
and accounting data retroactively. HML and RMW are built from the extremes of
book-to-market and operating profitability — precisely the cohort of small, unprofitable,
high-growth firms around the dot-com period where twelve years of restatement change the
most. That would perturb the extreme portfolios' monthly returns without much changing
their long-run average, **which is the pattern observed.** Distinguishing it from a subtle
construction difference requires the 2013–14 vintage, which does not exist publicly. **The
Ken French page records no definitional change, but a page that does not mention a change
is not evidence that none occurred.**

---

## What passing this gate does NOT establish

Stated because the failure mode of a green integration test is that it gets quoted as
evidence of something it never tested.

- It does **not** verify portfolio accounting, rebalancing, transaction costs, tax lots,
  corporate actions, insolvency behaviour, missing-data policy, look-ahead protection, or
  optimisation constraints. **None of them is exercised.**
- **The published factor file already contains the authors' own calculated returns.**
  Matching their table shows we read and summarised their numbers correctly; **it does not
  show we could have computed them.**
- **It can match despite compensating errors** — two offsetting mistakes in the unit
  transform and the window would produce the same table.
- Every figure is **gross**, because the source series are. The long-short series are not
  investable.
- **A sha256 proves which file was used, never what was available at an earlier date.**
  Nothing here is point-in-time.

---

## Where the band changes a conclusion: nowhere, and that is structural

The band is carried as a **separate** systematic band and never combined with a sampling
interval. Every downstream primary metric and falsifier clause is a function of the *mean*,
which reproduced for all five factors; the band moves only volatility, Sharpe and the
minimum detectable effect. Checked cell by cell in
[factor persistence](factor-persistence.md), **every reading holds at both ends of the
band** — including the pooled MDE that decides branch (b), where it is roughly ±1.5%
because two of three legs are unaffected.

**Five series carry no measured band at all, which is weaker than a band of zero**: the two
regional five-factor files, and **all three momentum files, never gated against any printed
table in any region.**

---

## Open questions

- **Can any 2013–14 vintage of the file be obtained** — a co-author's archive, a replication
  package, an institutional mirror? That is the single observation that would settle the
  diagnosis, **and it changes no conclusion anywhere.**
- Do the differences persist in the 2 × 2 and 2 × 2 × 2 × 2 blocks, which use different
  portfolio intersections? The library distributes only the 2 × 3 file.
- Is the discrepancy localised to 2000–2002 or spread? Answering it requires the published
  monthly series, which was never distributed.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_phase1_ff_reproduction --view-results
uv run pytest tests/integration/test_phase1_reproduction.py      # offline
uv run pytest -m network tests/integration/test_phase1_reproduction.py
```

The source vintage is `F-F_Research_Data_5_Factors_2x3_CSV.zip`, sha256 `cbc37248…`,
`Last-Modified` 2026-08-03, retrieved 2026-08-12, whose own preamble reads *"This file was
created using the 202606 CRSP database."* **The specification refuses to run against a file
whose sha256 is not the pinned one: when Ken French publishes a new vintage this experiment
aborts rather than reporting numbers, and a new specification must be frozen against the new
hash — which is the point.**
</content>
