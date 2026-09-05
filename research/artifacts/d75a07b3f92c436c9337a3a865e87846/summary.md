### Full portfolio value and momentum substitutions under mapping uncertainty

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `d75a07b3f92c436c9337a3a865e87846`
- **Experiment family:** `exp_029_funded_fund_substitutions`
- **Specification hash:** `a3e48066672d3fa4d283b1f5e157fab355210755d2095d2551beae5e5cf16974`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** Report sign reversals across mapping windows, costs and assumed premia; never promote from this study.

576 full-portfolio scenario rows; fixed funded substitutions, two loading windows and explicit costs/premia. No fund selected or promoted.

No statistics were reported.

**Caveats.**
- Recent fund exposures projected backward; residual risk and return omitted.
- Previously examined data and choices; no untouched holdout.
- Intervals exclude loading and assumed-premium uncertainty.
- No investor taxes, transition gains, or executable internal trading rule.
- Nominal Treasury proxies SCHP; AQR gross trend proxies RSST's trend leg.
- Benchmark gaps are distinct comparisons, never additive.
