# 0012 — Valuation enters through the drawdown assumption, not through a forecast

**Status:** current. Adds a constraint on how a market valuation reading may change the
published construction. Amends none of [0004](0004-no-sleeve-promoted.md),
[0006](0006-reference-portfolio-without-promotion.md) or
[0009](0009-blocks-lifted-and-closures-rescoped.md); applies
[0010](0010-bars-carry-a-reopening-condition.md) clause 3 to one empirical rejection.

## Context

On 2026-08-31 the US CAPE stood at 41.7, the ten-year TIPS real yield at 2.44% and the
thirty-year at 2.99%, and the TIPS-based excess CAPE yield printed below zero for the first
time in its 23-year record. Six managers' published 2026 assumptions for US large cap span
fourteen points. The investor asked that valuations be taken into account. The repository's
own evidence ([valuation and the allocation](../research/valuation-and-the-allocation.md),
[current regime and pricing](../research/current-regime-and-pricing.md)) is that a rule on
the CAPE level loses gross and net, that the CAPE model's out-of-sample record since 1990 is
negative at every horizon, that the one valuation rule with a positive gross record is
`exploratory` and net-negative in a taxable account, and that the claim which survives is a
risk claim: entries above CAPE 30 ran a median −51.8% real fifteen-year drawdown with 59.7%
of months under water, on 0.32 independent observations.

The question a valuation reading can therefore change is not "what will equities return"
but "what drawdown is the position sized against, and what does protection cost today". At
the same time, Experiment 018
([run `311048fb…`](../../research/artifacts/311048fbc6b44072a3715ff24d1507a4/summary.md),
`exploratory`) tested a financed Treasury stack, a gold stack, cash and long-Treasury
substitutions and a bonds-plus-trend wrapper inside the leveraged construction for the
first time, on 1929–2025 and three shorter panels, and an adversarial review reproduced it.

## Decision

1. **A valuation reading enters the construction through three routes only.**
   (a) A widened drawdown assumption — the high-valuation-conditional −52% real drawdown and
   ~60% of months under water in place of the unconditional −37% and ~5% — routed through the
   notional budget, which sizes the wrapper against the investor's stated tolerance.
   (b) A conditional TIPS substitution rule gated on that stated tolerance: at −50% or
   tighter, ten points of long TIPS held unlevered in the traditional account, funded from VTI
   and VXUS pro rata, with the wrapper shrunk to 19.1%; at −60% or looser, none. Amended
   2026-09-02: the ten points are Experiment 018's frozen substitution arm and the 19.1% is
   the ladder's trend column at −50%; the rule is not a derivation from the ladder's equity
   column, which would call for about 36 points of TIPS, and it is labelled as such in
   [part A](../research/portfolio-for-one-investor.md) §7.
   The default for a contributing, leverage-accepting investor is none.
   (c) The US/international split adjusted by contributions only, from 65/35 toward 60/40,
   never by a sale in a taxable account.
   No route is a market return forecast, a CAPE-level timing rule, or a rule run in a taxable
   account. The excess-CAPE-yield rule was frozen and run on 2026-09-02 (Experiment 022):
   it clears its floor against a risk-matched control on a century, is unresolved since
   1990, and is admissible in the traditional third as a 25% wrapper plus a 5-point
   ten-year Treasury or TIPS line. It stays `exploratory` and is offered as the investor's
   valuation-conditioned choice rather than adopted into the published vector.
2. **The financed bond stack is not adopted, on a scoped rejection.** Tested as 20 and 40
   points of an RSSB-like Treasury leg on the 70% equity core plus 30% trend wrapper, it reads
   +0.34 [−0.01, +0.69] and +0.68 pp/yr against the reference on 1157 months, `unresolved`; its
   whole contribution sits in 1981-10…2020-07, it is −0.25 [−0.69, +0.16] on the 691 months
   outside that era, and at a term premium of about 0.8 pp its expected contribution net of
   an 11 bp certain cost is about +0.04 pp/yr against 1.71% of tracking error. The scope is
   that design: a modelled ~20-year bond leg, assumed wrapper exposures, no fund returns. The
   rejection reopens on any of: a term-premium estimate above 1.5 pp/yr; a year of negative
   trailing 36-month bond–equity correlation, with a registered correlation-conditioned test
   that clears its floor on the complement of the bull market; a measured bond-leg excess
   outside 1981–2020 that is positive on any window the repository holds; or filed evidence
   that the wrapper the investor holds covered the 2022 bond loss. Substitution arms are
   `rejected` on mean (−0.55 to −0.77 pp/yr) and are the only route that cut 1929- and
   2008-scale drawdown; route (b) above is that trade, taken only when the constraint binds
   and priced at today's real yield.
3. **External capital-market assumptions are inputs, never edges.** A manager's expected
   return, premium or valuation-reversion term may be displayed beside the repository's own
   readings, labelled as that firm's model output with its as-of date and basis. It may not
   enter a sizing calculation, an edge decomposition, a notional budget or a figure record as
   a measured quantity. The spread between managers is itself the reading.
4. **The review triggers are levels, checkable from the same series**, and they travel with
   the position: CAPE below 30 reverts the drawdown assumption; the Shiller excess CAPE yield's
   expanding percentile at 0.50, or the TIPS-based measure back at its 2.97 pp median, returns
   the ECY rule to its anchor; a thirty-year TIPS real yield below about 2.0% ends the
   "cheapest in the record" note; Baa−Aaa at 0.90 pp reopens credit; the US value spread
   below 4.95× re-examines tilt size.

## Consequences

The capital-weight vector is unchanged by the September 2026 review, and the site shows the
ladder beside the published weight, stating that 30% is its loosest row, rather than
choosing a number for the investor (this record claimed a prompt for the tolerance before
one existed; the ladder was published on 2026-09-02). A valuation page may say what a reading is and what the repository's rules would
prescribe; it may not book a forecast. The stacked-bond question stays open as research
under [0010](0010-bars-carry-a-reopening-condition.md); what is closed is adopting it into
the published construction on the evidence held.

This record should be revisited when the investor supplies a tolerance, when any trigger in
clause 4 fires, or when the excess-CAPE-yield rule's post-1990 window clears its floor. It is
superseded if a later record admits a return forecast into the construction.
