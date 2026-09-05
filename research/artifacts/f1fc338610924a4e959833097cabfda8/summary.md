### Correct the tilt shelf's funded-return versus residual-appraisal estimand

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `f1fc338610924a4e959833097cabfda8`
- **Experiment family:** `exp_028_tilt_estimand_audit`
- **Specification hash:** `6fb9e55bb82744c082862817127ddf1f55be08fe6cf3b7f92620be8e6922700b`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** Report both diagnostics without allocating or ranking. Zero differences would show that this error has no numerical effect for that case; nonzero differences reopen it.

Correction audit: funded factor-tilt contribution uses the candidate's priced edge over its funding asset. Residual appraisal is a separate diagnostic. Neither measures full funded return or log growth.

No statistics were reported.

**Caveats.**
- Same historical data and study parameters already inspected; no new holdout.
- Market-beta contribution, intercept and taxes are omitted from the priced edge.
- Premium-error ranges omit loading, cost and residual-appraisal uncertainty.
- Held active-position proxy is incomplete; no allocation ranking is established.
