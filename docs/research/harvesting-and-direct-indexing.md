# Tax-loss harvesting and direct indexing: what it is worth, and to whom

**Question.** The edge budget books **30 bp/yr** for tax-loss harvesting and dismisses
direct indexing in a sentence — it "needs direct security ownership that funds do not
give". This investor holds roughly a third of the portfolio in a taxable account,
contributes 5–15%/yr and has a long horizon with no withdrawal need, which is close to the
profile the harvesting literature is written for. Is harvesting worth more than 30 bp here,
and if so should the taxable third be direct-indexed?

**Decision it informs.** Whether to replace the taxable US core with a direct-indexed
separately managed account, whether to harvest between two similar funds instead, and what
either does to the placement plan in
[structural and tax edges §8](structural-and-tax-edges.md#8-the-investors-plan-eight-funds-three-accounts-and-a-ranking-that-does-not-move).

**Scope.** US federal individual investor, `as of 2026-08-23`. State income tax is excluded
and additive. **Not personalised advice.** Every figure is a function of stated inputs a
different investor must restate — and two of those inputs, the taxable account's dollar
size and the investor's own stream of realised capital gains, **have not been given**, so
they are reported across a range.

Everything numerical regenerates from
[`studies/tax_loss_harvesting.py`](../../research/src/portfolio_edge/studies/tax_loss_harvesting.py)
and [`studies/_tax_loss_harvesting_tables.py`](../../research/src/portfolio_edge/studies/_tax_loss_harvesting_tables.py),
pinned in `research/tests/unit/test_studies_tax_loss_harvesting.py`:

```sh
cd research && uv run python -m portfolio_edge.studies.tax_loss_harvesting
```

No experiment is registered. This is `exploratory` implementation work under
[the tiered protocol](../AGENTS.md#research-pages): a sizing exercise for a decision, not a
hypothesis test about a market.

---

## Conclusion

1. **Harvesting is not worth 30 bp/yr to this investor. On the stated plan it is worth
   about zero, and direct indexing is worth about −9 bp/yr.** The reason is not the
   harvest yield, which is large. It is that **26 U.S.C. §1211(b) caps the deduction of net
   capital loss against ordinary income at $3,000 a year**, and the plan's whole content is
   that the taxable account never sells. With no realised gains to shelter, **0.2% of every
   dollar of loss harvested over thirty years ever produces a tax saving**; the other 99.8%
   stands as a §1212(b) carryforward. At a **zero fee** the whole exercise is worth
   **−0.2 bp/yr**. The 9 bp fee is what makes it −9.
2. **The number that decides everything is not the harvest yield but the investor's own
   realised gains.** Direct indexing at 9 bp breaks even at **1.2% of the account per year
   of exogenous long-term gain if the account is held to a §1014 step-up, and 3.0% if it is
   ever liquidated** (top bracket; 1.5%/3.8% at 18.8%, 1.9%/5.9% at 15%). Gains from
   restricted-stock vesting, a concentrated position being unwound, a business sale or a
   home sale all count. **Gains the direct-index account creates for itself do not**, because
   the fund holder never had them.
3. **The step-up-versus-liquidation gap is the whole decision, and it is worth about
   14 bp/yr.** At 3% of offsetting gains and the top bracket, the same strategy is
   **+13.9 bp/yr held to death and 0.0 bp/yr if liquidated at thirty years**. Harvesting
   lowers basis; §1014 forgives the reduction and a sale reverses it at the capital-gain
   rate. What survives a sale is only the rate difference on the losses actually used, plus
   the time value.
4. **A capital-loss carryforward dies with the taxpayer.** IRS Publication 559: a decedent's
   capital losses *"(including capital loss carryovers) can be deducted only on the
   decedent's final income tax return"*, and *"you can't deduct any unused NOL or capital
   loss on the estate's income tax return"*. So the step-up that makes harvesting permanent
   also destroys the unused stock of it. **Harvesting into a carryforward you never use is
   worth exactly nothing, twice over.**
5. **The decay curve is real and steep, and contributions are what stop it.** Modelled
   gross harvest yield, as a percentage of the account: **18.8% in year one, 8.8% in year
   two, 4.8% in year ten and 4.0% in year thirty** with 10%/yr of contributions —
   against **18.6%, 7.6%, 1.7%, 0.9%** with none. The thirty-year averages are **5.1%**
   and **2.2%**, so a headline quoted from year one overstates a contributing investor by
   **3.7 times** and a static one by **8.3 times**, before the usage constraint bites at
   all.
6. **The simpler route wins at every plausible input for this investor.** Harvesting at the
   *fund* level — sell the total-market fund at a loss, buy a different sponsor's
   total-market fund — captures market-wide losses only, but it costs **no fee, adds only
   the difference between two total-market indices, and can be stopped at any time**. It beats direct indexing at every
   offsetting-gain rate below **2.5%** (top bracket, step-up) and **at every rate tested
   below the top bracket if the account is ever liquidated**.
7. **Direct indexing is a one-way door and it doubles the lock-in it was bought to
   exploit.** After thirty years the modelled harvested account carries a median embedded
   gain of **55.7% of its value against 26.7% for the same account never selling**.
   Abandoning it with ten years left costs **142 bp/yr** at the top rate — ten times the
   best case for running it.
8. **The one operational trap this investor is specifically exposed to is a cross-account
   wash sale, and the employer plan is where it lives.** Revenue Ruling 2008-5 disallows a
   loss whose replacement is bought inside the taxpayer's IRA **and denies the IRA the
   §1091(d) basis increase**, so the deduction is destroyed rather than deferred. At the
   `f = 0` corner of [§8.5](structural-and-tax-edges.md#85-the-plan-and-the-employer-plans-menu)
   the employer plan holds **18.3% of the portfolio in VTI**, bought automatically every
   pay period. Any fund-level harvest of VTI in the taxable account must be checked against
   that schedule.

**One caution.** Item 1's "about zero" is a statement about *this stated plan*, in which
the taxable account never sells and no other realised gain is disclosed. It is not a
statement that harvesting is worthless. Change one input — a stream of realised gains from
outside the portfolio — and item 2's break-evens decide it, in direct indexing's favour.
**Ask for that input before executing anything on this page.**

---

## 1. What the repository's own data says about dispersion

The whole case for direct indexing is that a fund cannot pass through a loss on one
security while the index it tracks is up. So the size of the prize is the dispersion
*within* the index. Two things were measured from the committed Ken French 49-industry
file (`sha256 a0b2345…`, retrieved 2026-08-17) and the FF3 file.

### 1.1 Single-stock idiosyncratic volatility, backed out of firm counts

An equal-weighted basket of `n` stocks carries `sigma_idio² / n` of idiosyncratic
variance. Each industry portfolio's residual variance after a market regression is
therefore `common variance + sigma_idio² × mean(1/n)`, and a cross-sectional regression of
one on the other identifies both.

| Window | Industries | Common sd | **Stock idiosyncratic sd** | Slope *t* | R² |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1946–1965 | 42 | 8.7% | 24.0% | 4.91 | 0.38 |
| 1966–1985 | 49 | 14.6% | 43.6% | 2.62 | 0.13 |
| 1986–2005 | 49 | 15.7% | 56.4% | 4.59 | 0.31 |
| 2006–2026 | 49 | 15.2% | 64.6% | 3.76 | 0.23 |
| **1996–2026** | 49 | 15.4% | **69.7%** | 4.90 | 0.34 |
| 1996–2026, smaller half by average firm size | 24 | 12.7% | **87.2%** | 4.44 | 0.47 |
| **1996–2026, larger half by average firm size** | 24 | 16.8% | **45.9%** | 2.59 | 0.23 |

**Read the resolution before the level.** The identifying assumption is that idiosyncratic
variance is uncorrelated with firm count across industries, and the size split shows it is
not: the estimate nearly doubles between the large and small halves. R² is 0.23 on the
large half and the slope carries *t* = 2.59, which is a signal rather than a measurement.
And these are equal-weighted averages over every CRSP firm in an industry, while a
cap-weighted total-market index puts most of its money in the largest names. **So 45.9% is
an upper estimate for the position-weighted figure a direct index would actually see**, and
the model below is centred at **35%** and swept from 0 to 45%.

The one thing the table says clearly is that dispersion **rose** — 24% in the post-war
sample, 55–70% now — which is the direction that favours harvesting, and it is a fact about
the composition of the listed universe rather than a forecast.

### 1.2 How often a lot is actually below cost

No model at all: the share of positions more than 5% below a lot bought `h` months
earlier, over every start month 1996-01 to 2026-06.

| Horizon | Position more than 5% below cost | Market more than 5% below cost | Mean depth of the below-cost positions |
| ---: | ---: | ---: | ---: |
| 3m | 25.2% | 14.3% | 11.7% |
| 6m | 27.2% | 15.6% | 14.3% |
| **12m** | **28.6%** | **17.2%** | 18.4% |
| 24m | 25.1% | 14.9% | 23.8% |
| 60m | 14.4% | 8.2% | 32.6% |
| 120m | 7.6% | 3.7% | 41.2% |

**A 49-industry portfolio is a diversified basket, not a stock**, so every position figure
here is a **floor**. Even at that floor, position-level opportunities are about **1.7 to
2.1 times as frequent** as market-level ones at every horizon — which is the whole
mechanism, measured, with no vendor involved. The horizons overlap heavily, so these are a
description of the sample and not independent observations; no test is run on them and none
should be.

---

## 2. The decay curve, and why the headline is always year one

Modelled, not measured: a lognormal one-factor model with 7% pre-tax total log drift (the
figure [`tax_structure`](../../research/src/portfolio_edge/studies/tax_structure.py) uses
throughout, so the two pages compare), **15.8% market volatility** — the annualised monthly
standard deviation of the French US market total return over 1996–2026 — a 1.5% dividend
yield, 35% idiosyncratic volatility and a 5% harvest threshold. Gross harvested loss as a
percentage of the account:

| Route | y1 | y2 | y3 | y5 | y10 | y20 | y30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct index, no contributions | 18.6% | 7.6% | 4.7% | 2.6% | 1.7% | 1.0% | **0.9%** |
| **Direct index, 10%/yr contributions** | **18.8%** | 8.8% | 6.4% | 5.1% | 4.8% | 4.3% | **4.0%** |
| Fund level, 10%/yr contributions | 5.4% | 0.5% | 0.6% | 0.6% | 0.6% | 0.6% | **0.5%** |

Thirty-year averages: **5.1%** with contributions, **2.2%** without.

Three readings.

- **Ossification is real and it is self-inflicted.** Loss lots are systematically sold and
  gain lots systematically retained, so a static account's basis converges on its market
  value and stops producing losses: **a twentyfold fall by year thirty**.
- **Contributions defeat it, and this investor has them.** 5–15%/yr of new money plus
  reinvested dividends holds the steady state at roughly **4%/yr** rather than 0.9%. That
  is the single input that most favours direct indexing here.
- **A fund harvests roughly an eighth of what the securities inside it harvest**, in steady
  state. That ratio, not the absolute level, is what direct indexing is buying.

**None of this is a benefit yet.** A harvested loss is a deduction only if it can be
deducted.

---

## 3. Usage: the constraint every vendor figure assumes away

Write `H` for the losses harvested over a lifetime, `U` for the part actually used, and
`C = H − U` for the carryforward standing at the end. Harvesting reduces the account's
basis by exactly `H` — an identity the code checks to floating point on every path.

**On liquidation**, the extra gain realised is `H`, the carryforward absorbs `C`, and the
residue taxed is exactly `U`. Harvesting therefore *costs* `capital-gain rate × U` at the
end and *saved* `rate-at-use × U` along the way. **Every dollar of `H` that is never used
is worth zero, and the permanent benefit is only the rate difference on `U` plus the time
value.**

**On a §1014 step-up or an outright §170 gift of the shares**, the terminal gain is never
taxed, the reversal never happens, and the early saving is permanent. But `C` is destroyed
— IRS Publication 559, quoted in the conclusion. **Both paths turn on `U`, never on `H`.**

`U` has exactly two sources.

1. **The investor's own realised capital gains**, from any source. A loss shelters them
   dollar for dollar.
2. **§1211(b): $3,000 a year against ordinary income**, unchanged since the 1976–77
   amendments and never indexed. The excess carries forward under §1212(b) with its
   character.

The second is a nominal amount, so its basis-point value falls with the account and it is a
**ceiling, not an estimate** — reached only while the account is still producing $3,000 of
losses:

| Taxable account | 23.8% / 37% | 18.8% / 32% | 15% / 24% |
| --- | ---: | ---: | ---: |
| $100,000 | 111.0 bp | 96.0 bp | 72.0 bp |
| $250,000 | 44.4 bp | 38.4 bp | 28.8 bp |
| **$1,000,000** | **11.1 bp** | 9.6 bp | 7.2 bp |
| $3,000,000 | 3.7 bp | 3.2 bp | 2.4 bp |

**The rate here is the bracket rate on wages, not the all-in investment rate.** The §1411
surtax reaches net investment income, not salary, so applying 40.8% to a deduction against
a paycheque overstates it. Where the loss also reduces net investment income the deduction
is worth up to 3.8 points more; that is reported and not booked.

---

## 4. What direct indexing is worth, as a distribution

Median and 10th/90th percentiles across 400 simulated market paths, thirty years, a $1m
taxable account, 10%/yr contributions, a **9 bp** fee against **VTI's 1.16 bp net cost**
(a 3 bp fee less 1.84 bp of median securities lending, from
[§6.1](structural-and-tax-edges.md#61-net-cost-and-why-it-is-not-the-fee-ranking)), and a
4 bp round-trip trading cost. In bp/yr of after-tax log terminal wealth against **the same
account holding VTI and never selling** — the investor's own counterfactual, not a cheap
index.

| Bracket | Exit | 0% gains | 1% gains | 3% gains | 5% gains |
| --- | --- | ---: | ---: | ---: | ---: |
| **23.8% / 37%** | liquidate | **−9.3** | −6.2 | 0.0 | +4.7 |
| | **step-up** | **−9.2** | −1.4 | **+13.9** | **+24.2** |
| **18.8% / 32%** | liquidate | −9.3 | −6.8 | −1.9 | +1.8 |
| | step-up | −9.3 | −3.0 | +9.3 | +17.6 |
| **15% / 24%** | liquidate | −9.4 | −7.4 | −3.5 | −0.6 |
| | step-up | −9.4 | −4.3 | +5.6 | +12.4 |

The 10th–90th spread at the top bracket, step-up, 3% gains is **+6.3 to +29.2 bp**; at 0%
gains it is **−9.4 to −8.9 bp and negative on 100% of paths**. The dispersion is not noise:
**the correlation between the benefit and log terminal wealth is −0.72**. Harvesting is a
hedge on the tax bill and it pays most in the paths where the market did worst, which is
why a mean is a poor summary of it and why it is reported as a distribution.

**Break-even exogenous long-term gain, as a fraction of the account per year:**

| Bracket | Liquidate at 30 years | Held to a step-up |
| --- | ---: | ---: |
| 23.8% / 37% | **2.99%** | **1.18%** |
| 18.8% / 32% | 3.82% | 1.48% |
| 15% / 24% | 5.86% | 1.86% |

**Fee sensitivity, top bracket, step-up, $1m:**

| Fee | 0% gains | 3% gains |
| ---: | ---: | ---: |
| 0 bp | **−0.2** | +22.9 |
| **9 bp** (Frec, verified) | −9.2 | +13.9 |
| 12 bp | −12.2 | +10.9 |
| 20 bp | −20.2 | +2.9 |
| 40 bp | −40.2 | **−17.1** |

**The 0 bp / 0% gains cell is the most important number on this page.** Strip the fee out
entirely and harvesting still earns this investor **nothing**, because there is nothing to
deduct against. That is not a fee problem and no cheaper provider fixes it.

---

## 5. The cost side, stated fully

**Fee.** **Frec charges 0.09% a year with a $20,000 minimum**, verified at
`frec.com/direct-indexing` on **2026-08-23**, and it lists **Morningstar US Total Market**
among its indices — which since **2026-07-29** is VTI's own target index
([§6.2](structural-and-tax-edges.md#62-tracking-difference--filed-and-mostly-unusable-across-funds)),
so the sleeve substitution would be exact rather than approximate. **No other provider's
schedule was re-verified**: Wealthfront's pricing page renders its figures in script and
returned nothing to a plain fetch. The wider list in
[§5 of the tax-edge page](structural-and-tax-edges.md#5-direct-indexing-against-the-30-bp-already-booked)
— Wealthfront 9, Altruist 12, Vanguard 20, Schwab 40, Fidelity 40 — is dated mid-2026 and
is carried forward unchanged, not confirmed.

**The fee is not deductible, and that is now permanent.** 26 U.S.C. §67(h) —
redesignated from §67(g) by Pub. L. 119-21 §70110(b)(2) — reads *"no miscellaneous itemized
deduction shall be allowed for any taxable year beginning after December 31, 2017."* The
same act **struck the words "and before January 1, 2026"** from the text, so the suspension
no longer sunsets. An advisory fee on a direct-indexed account is paid in after-tax
dollars, forever.

**The hurdle is the fund's net cost, not its fee.** A direct index replaces the fund, so it
also forfeits the fund's securities-lending income. VTI costs **1.16 bp** to own, not 3.
The right comparison is 9 against 1.16, a **7.84 bp** gap.

**Tracking error, bounded rather than measured.** Running the same harvest rule on the real
49-industry panel and differencing against the identical account that never sold gives
**1.44%/yr** of tracking error, 1996-01 to 2026-06. **Treat that as a ceiling**: 49
positions with proceeds redistributed across the other 48 is a far cruder replacement than
a 500-name index buying one close substitute. A stated-assumption bound runs the other way —
10% of the account in substitutes across 50 names with idiosyncratic correlation 0.7 gives
**0.38%/yr**, and 30% across 150 names at 0.5 gives **0.86%/yr**. Nothing here holds a
direct-index account's holdings file, so **this is the input the page is least able to
resolve**, and it matters: the whole edge-versus-tracking-error arithmetic at the end of
[the tax-edge page](structural-and-tax-edges.md#the-ledger) assumes about 46 bp of combined
tracking error. Adding even a quarter of the measured ceiling would dominate it and push
"90% confidence" from three and a half months to years.

**The wash-sale rules, and the trap that is permanent rather than timing.** §1091(a)
disallows a loss where substantially identical stock is bought within 30 days either side of
the sale. Ordinarily §1091(d) repairs it by adding the disallowed loss to the replacement's
basis, so a wash sale is a deferral. **Revenue Ruling 2008-5 removes the repair when the
replacement is bought inside the taxpayer's IRA**: the loss is disallowed and the IRA's
basis is *not* increased. The taxable account still bought its replacement out of the
proceeds, so **the basis reduction happens and the deduction does not** — the taxpayer
keeps the harm and loses the good. The model prices it as a disallowance fraction and it
reduces the benefit strictly.

**Scanning must be household-wide and schedule-aware.** The exposure specific to this
investor is not a manual trade. It is the **automatic payroll purchase inside the employer
plan**: at the `f = 0` corner of
[§8.5](structural-and-tax-edges.md#85-the-plan-and-the-employer-plans-menu) the plan holds
**18.3% of the portfolio in VTI**, bought every pay period. A spouse's account and a Roth
raise the same question on the same reasoning. Whether a 401(k) purchase is reached by
Rev. Rul. 2008-5's logic is **not settled by any ruling found**; the prudent reading is
that it is.

**Lock-in, which is the cost that is easiest to underestimate.** After thirty years the
harvested account's median embedded gain is **55.7% of its value, against 26.7% for the
same account never selling**. Harvesting more than doubles the lock-in it exists to
exploit. Abandoning that account with ten years left costs:

| Bracket | Annualised cost of exiting |
| --- | ---: |
| 23.8% / 37% | **142 bp/yr** |
| 18.8% / 32% | 111 bp/yr |
| 15% / 24% | 87 bp/yr |

**Ten times the best case for running the strategy.** A separately managed account of
several hundred low-basis lots cannot be transferred to another manager's model without
realising gains, and cannot be converted into a fund at all. This is a one-way door, and
this repository's own record is that a construction gets revised: the placement plan, the
trend weight and the edge budget have each moved materially within one session.

---

## 6. Does it fit this portfolio?

At `f = 1` the taxable third holds **VTI 20% and AVLV 13.3–15%** of the portfolio; at
`f = 0` the menu constraint forces **AVLV 15, DFIV 10, AVES 5, IDMO 1.7, VTI 1.7**
([§8.5](structural-and-tax-edges.md#85-the-plan-and-the-employer-plans-menu)).

- **The sleeve it would replace is VTI, and only VTI.** It is a broad cap-weighted index
  with a matching direct-index product, and [§8.4](structural-and-tax-edges.md#84-the-ranking-at-three-brackets)
  ranks it **last in the shelter queue at every rate**, so it is the one holding that is
  reliably in the taxable account. Nothing about direct indexing changes that ranking:
  the fee is not a distribution and does not move VTI's 1.07% fully qualified yield.
- **Direct-indexing the value tilt is a different and worse trade.** AVLV is a systematic
  process with a measured loading, and it contributes **+0.128 pp/yr** to the construction
  tournament's result ([adversarial review](adversarial-review.md)). A provider's
  "US large-cap value" index is a different, unmeasured process. Substituting it forfeits
  about **13 bp of measured contribution** to buy at most a few basis points of harvesting,
  and [factor products](factor-products.md) is the record of how often a product's label
  and its delivered exposure differ.
- **At `f = 0` the plan gets worse, not better.** That is the corner where the employer
  plan holds VTI and the taxable account holds the two highest-yielding international
  funds. Direct-indexing US equity there would leave only 1.7% of the portfolio to
  direct-index — under Frec's $20,000 minimum on any portfolio below about $1.2m — while
  maximising the wash-sale exposure. **The rollover share `f` is a prerequisite for this
  decision as well as for the placement one.**
- **It breaks the headroom rule.** [The recommendation](portfolio-recommendation.md#operating-the-portfolio)
  establishes that the portfolio is restorable without a taxable sale *iff every fund's
  taxable holding is at or below its target weight*. A direct-indexed VTI position with a
  56% embedded gain is the least trimmable line in the portfolio, so it must never be the
  overweight one — and it is the line most likely to be, because US equity is 65% of the
  book.

---

## 7. The alternatives, ranked

Benefit is the modelled median in bp/yr at the top bracket, held to a step-up, on a $1m
taxable account. Fund-level harvesting is priced with a **1 bp** swap cost, which is
conservative: [§6.6](structural-and-tax-edges.md#66-spread-and-premiumdiscount-weighted-as-the-one-time-costs-they-are)
measures VTI's 30-day median bid-ask spread at **0.55 bp** and ITOT's at **1 bp**, so
selling one and buying the other costs about 0.8 bp of half-spreads. Direct indexing is
priced at 4 bp on single stocks.

| Route | Fee | Decisions/yr | Reversible? | 0% gains | 1% gains | 3% gains | 5% gains |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| **Hold and never sell** | 0 | 0 | free | 0 | 0 | 0 | 0 |
| Contributions to whatever is furthest below target | 0 | 4 | free | 0 | 0 | 0 | 0 |
| Gift appreciated lots (§170) | 0 | 1 | free | — | — | — | — |
| **Fund-level harvesting, two similar funds** | **0** | ~2 | cheap | **+0.1** | **+6.9** | **+10.4** | +11.4 |
| **Direct indexing the taxable US core** | 9 bp | 0 | **one-way** | **−9.2** | **−1.4** | **+13.9** | **+24.2** |

**Direct indexing overtakes fund-level harvesting only above these offsetting-gain rates:**

| Bracket | Held to a step-up | Liquidated at 30 years |
| --- | ---: | --- |
| 23.8% / 37% | **2.48%** | 5.00% |
| 18.8% / 32% | 2.82% | **never below 40% — fund-level wins throughout** |
| 15% / 24% | 3.26% | **never below 40% — fund-level wins throughout** |

Four things this table says that the individual numbers do not.

- **Fund-level harvesting saturates and direct indexing scales.** Fund level goes 6.9 →
  10.4 → 11.4 as gains rise from 1% to 5%, because it runs out of losses at 0.5%/yr of the
  account. Direct indexing goes −1.4 → 13.9 → 24.2, because at 4%/yr it does not. **An
  investor with a large recurring gain stream should direct-index; one without should not**,
  and the crossover is around 2.5–3.3% of the account a year.
- **The two free routes are worth zero as tax lines and are still the right answer.**
  Contribution-directed rebalancing is what lets the taxable account never sell, and never
  selling is what preserves the **84 bp/yr** deferral that
  [§4 of the tax-edge page](structural-and-tax-edges.md#4-deferred-unrealised-gain--the-largest-number-here)
  prices. That is an order of magnitude larger than anything in this table and it is
  obtained by doing nothing.
- **Gifting is a way of giving, not a return.** §170 gives a fair-market-value deduction
  for long-term publicly traded stock and the gain is never recognised, subject to the
  §170(b)(1)(C) 30%-of-contribution-base limit for capital gain property to a public
  charity, 20% under §170(b)(1)(D) for others, with a five-year carryover under §170(d).
  It is worth doing to the extent the investor was giving anyway. Its incidental effect —
  removing the most-appreciated, most ossified lots — would slow the decay in §2, and it is
  **deliberately not credited to harvesting**, because the same gift is available to the
  fund holder and does the same job there.
- **"Substantially identical" is undefined for two ETFs tracking two different indices, and
  no authority resolves it.** VTI tracks Morningstar US Total Market and ITOT tracks S&P
  Total Market; different sponsors, different index providers, high but imperfect overlap.
  The §6.1 audit puts them at **ITOT 1.04 bp and VTI 1.16 bp** of net cost, so the swap is
  nearly free on cost as well. The IRS has issued no ruling on the pair; the position is
  defensible and it is not certain, and this page does not pretend otherwise.

---

## 8. Verdict

**Do not direct-index the taxable third. Harvest at fund level under a written rule, keep
never-selling as the default, and gift appreciated lots if giving anyway.**

**The number, with its uncertainty.** For this investor as stated — no disclosed stream of
realised capital gains, a taxable account that never sells, 5–15%/yr of contributions:

| | Median bp/yr | 10th–90th | Certainty class |
| --- | ---: | --- | --- |
| **Fund-level harvesting** | **+0.1 to +7** | wide; zero at 0% gains, +6.9 at 1% | **modelled**, sensitive to the offsetting-gain input |
| **Direct indexing at 9 bp** | **−9** | −9.4 to −8.9, negative on every path | **modelled**; the fee is contractual and the benefit is not |
| Never selling, for comparison | +84 (a hurdle not paid, not a saving) | — | arithmetic |

**Booked: nothing.** Fund-level harvesting's positive cells all require an offsetting-gain
rate that has not been stated, and
[§8.6 rule 3](structural-and-tax-edges.md#86-what-the-plan-is-worth-under-four-rules-that-bound-it)
is explicit that a hurdle avoided is not a saving. **The existing 30 bp harvesting line in
the edge budget should be read as what it is: a figure for a different investor, one with
gains to shelter, and it does not apply to this plan.** It is already netted to 25.6 bp
there and it should be **0 for this investor** until the gain stream is known.

**What would change it, in order of how much it moves the answer.**

1. **A stream of realised capital gains of more than about 2.5% of the taxable account a
   year** — restricted-stock vesting, unwinding a concentrated position, a business or
   property sale, or capital-gain distributions from funds held elsewhere. Above that, at
   the top bracket and held to a step-up, direct indexing overtakes fund-level harvesting;
   above 5% it is worth +24 bp/yr and is the right answer.
2. **A decision to liquidate rather than hold to a step-up.** It removes about 14 bp and
   makes fund-level harvesting the better route at every bracket below the top.
3. **A materially smaller taxable account.** At $100,000 the §1211(b) ceiling alone is
   111 bp/yr, and the arithmetic inverts — though at that size the fee minimums and the
   operational burden bite instead.
4. **A change to §1211(b).** The $3,000 cap is the binding constraint on the whole page and
   it is a nominal figure from the 1970s. Indexing it, or raising it, would move this
   conclusion more than any market fact.
5. **A verified fee below 9 bp, or a provider that lends the securities.** At a zero fee
   direct indexing is still −0.2 bp at 0% gains, so this changes the margin and not the
   sign.

---

## Assumptions, open questions, provenance

**Assumptions, separated from measurement.**

- **7% pre-tax total log drift**, constant, carried from `tax_structure` for comparability.
  It is a forecast. Lower drift raises the harvest yield and raises the benefit.
- **35% idiosyncratic volatility** as the central case, against a measured 45.9% on the
  larger half of industries and 69.7% across all of them. Cap weighting pulls it down and
  the amount is not resolved here.
- **A lot is a position.** Each lot draws an independent idiosyncratic shock, which assumes
  the account is broad enough that two lots are rarely the same security. It understates
  co-movement between two vintages of one holding and so slightly overstates how smooth the
  harvest yield is within a path; it does not bias the mean, and the market factor — the
  dominant source of covariance — is exact.
- **Tax savings are reinvested** at the drift less the tax on the dividend, not at the
  pre-tax drift.
- **Rates constant for thirty years**, which no thirty-year period in US history has
  satisfied.
- **State tax excluded**, and additive. A state that taxes capital gain as ordinary income
  raises both the saving and the clawback and mostly cancels.
- **Round-trip trading cost** 4 bp on single stocks and 1 bp on a fund swap; assumptions,
  not measurements, and a small-cap direct index would pay several times the first.

**Open questions.**

1. **The investor's own realised capital gains.** The single input that decides this page,
   and it has not been given. **Ask before executing.**
2. **The taxable account's dollar size**, which sets the §1211(b) ceiling. Reported across
   $100,000 to $3m.
3. **A real direct-index account's tracking error.** No holdings file was obtained. The
   1.44%/yr measured on the 49-industry proxy is a ceiling and the 0.38–0.86% stated bound
   rests on three assumed inputs.
4. **Whether a 401(k) purchase triggers Rev. Rul. 2008-5's permanent disallowance.** The
   ruling addresses an IRA. No authority extending it to a qualified plan was found, and
   none excluding it either.
5. **Every published direct-indexing fee except Frec's.** Only `frec.com/direct-indexing`
   was verified on 2026-08-23. Wealthfront's pricing page renders in script and returned no
   figure to a plain fetch; it was not worked around.
6. **The position-weighted idiosyncratic volatility of a cap-weighted total-market index.**
   The estimate here is an equal-weighted-firm average and the size gradient is steep.
7. **Non-US investors.** A jurisdiction without a step-up removes the largest cell in §4's
   table; one that ring-fences capital losses removes the $3,000 line entirely; one taxing
   on accrual removes the deferral that makes never-selling the baseline.

**Reproducibility.** Rates, thresholds and market parameters are arguments rather than
constants. The market data are the two committed Ken French files, read from the raw cache
and never from the network: `49_Industry_Portfolios_CSV.zip`
(`sha256 a0b23457eac619c8a3cce362de563b6f57acc3514779ceccdb99886edfa0a804`, retrieved
2026-08-17) and `F-F_Research_Data_Factors_CSV.zip`
(`sha256 cd6d8e0d175b6f423862a6ad15a3073a6e4264b52b2ac9262396c79f707c6bcb`). Simulation
seed 20260823. Statutory citations: [§1091](https://www.law.cornell.edu/uscode/text/26/1091),
[§1211](https://www.law.cornell.edu/uscode/text/26/1211),
[§1212](https://www.law.cornell.edu/uscode/text/26/1212),
[§1014](https://www.law.cornell.edu/uscode/text/26/1014),
[§170](https://www.law.cornell.edu/uscode/text/26/170),
[§67](https://www.law.cornell.edu/uscode/text/26/67), Revenue Ruling 2008-5, and
[IRS Publication 559](https://www.irs.gov/publications/p559), all read on 2026-08-23.

---

## Consequence for this repository

1. **The 30 bp harvesting line is not this investor's number.** It belongs to an investor
   with realised gains to shelter. For the stated plan it is **0**, and the honest range for
   any US investor is **0 to about +25 bp/yr**, decided by their own gain stream and their
   exit path rather than by the strategy.
2. **A harvesting claim must state `U`, not `H`.** Any future figure quotes the losses
   *used*, the source of the gains they offset, and the disposal path. A gross harvest
   yield is not a benefit and must never be quoted as one.
3. **The disposal path is now a required input to any taxable-account claim**, alongside
   the bracket. §1014, §170 and a liquidation give three different answers to the same
   arithmetic, and the spread between them here is larger than the whole edge.
4. **Irreversibility is a cost and belongs in the comparison.** A strategy worth single
   digits of basis points that raises the cost of changing your mind to hundreds is a bad
   trade under any of this repository's own review policies. Add it to the promotion
   protocol alongside the deferral hurdle.
5. **Wash-sale scanning is a household-and-schedule problem, not an account problem**, and
   the employer plan's automatic purchases are the specific exposure. Any harvesting rule
   this repository writes states the funds it must not buy and the accounts it must not buy
   them in.
