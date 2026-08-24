# 0010 — Research stays open; claim gates carry scope and updating evidence

**Status:** current. Consolidates the live governance principle from
[0009](0009-blocks-lifted-and-closures-rescoped.md) and narrows categorical readings of
[0002](0002-no-research-grade-free-price-source.md),
[0004](0004-no-sleeve-promoted.md), and
[0005](0005-factor-premia-closed-on-public-data.md).

## Context

Several defensible precautions became broader than their evidence. Source limitations were
read as bans on acquisition, a zero-leverage recommendation became a restriction on
financing research, fixed numerical reference points became rejection hurdles, and
underpowered nulls became apparent closures. The frozen specifications and results remain
valid records of what was run. Their interpretation must remain no broader than the design.

The opposite absolute—“measurement is never gated”—is also too broad. Law, licensing,
research ethics, security, safety, and destructive acquisition costs can constrain work.
The problem addressed here is narrower: an earlier empirical conclusion should not, by
itself, foreclose a safe and lawful way to learn more.

## Decision

1. **Research is open by default.** Existing findings do not prohibit registering a
   candidate, acquiring an appropriate source, changing an estimand, pricing a construction,
   or running an exploratory comparison. State how the new question differs from the scope
   already tested.
2. **Evidence standards rise with the claim.** Exploration establishes mechanism,
   magnitude, provenance, and next tests. Evaluation freezes decision-relevant choices.
   Promotion or publication adds independent or forward evidence and implementation review
   appropriate to the claim. The tiered protocol is in [`docs/AGENTS.md`](../AGENTS.md).
3. **A durable claim gate names four things:** the claim it limits, the evidence and failure
   mode behind it, its scope, and the evidence or review trigger that would change the
   decision. Constraints already enforced by law, licences, code, or tests need not be
   duplicated as prose policy.
4. **Frozen results and current interpretations are separate.** Do not rewrite a
   specification, falsifier, ledger entry, or artifact after seeing results. If a design
   could not resolve the effect or its rule was defective, preserve the original outcome and
   publish a corrected claim-level interpretation with an audit trail. A correction may not
   manufacture positive evidence.
5. **Thresholds come from the decision and design.** The former 2.0 pp/yr materiality point
   and 0.30 pp/yr sleeve point are useful sensitivities, not universal bars. A new evaluation
   derives or justifies materiality, shows its relationship to MDE and arithmetic ceilings,
   and freezes it before inspecting the result. An exploratory screen may use a rough
   reference point if labelled as such.
6. **Funding is part of the hypothesis.** Pro-rata sale, cash funding, leverage matching,
   and financed overlays answer different questions. The zero-leverage reference portfolio
   remains a current recommendation for an underspecified investor; it is not a restriction
   on researching financed constructions.
7. **Statuses apply to claims, not whole strategy families.** A product can fail a loading
   test without being a bad product; a vendor index can be contradicted without rejecting
   the strategy; a premium can remain unresolved while an implementation is observable.

## Current interpretation of affected work

- Experiment 010's frozen outcomes remain in its artifacts. Where its threshold sat above
  the arithmetic ceiling or below the instrument's resolution, the portfolio claim is
  `unresolved` by that design, not evidence that the sleeve cannot help.
- Experiments 004 and 008 remain about different objects: a vendor trend series and product
  exposure delivery. Neither is a universal verdict on trend.
- The French-file RMW and CMA work establishes the resolution of those panels and windows.
  It does not establish a zero premium or prohibit conditional models, different estimands,
  non-French sources, longer samples, or lower-variance designs.
- The audited free fund-price feeds remain inadequate for confirmatory total-return claims
  that depend on distributions and corporate actions. That finding does not automatically
  reach non-distributing assets, reader-supplied data, source reproduction, cross-checks, or
  sources with different contracts.

No sleeve is promoted by this decision. Promotion status is a current research conclusion,
not a permanent governance rule.

## Consequences

The repository can search cheaply and creatively while keeping stronger claims expensive.
Specifications and artifacts preserve the exact historical result; syntheses carry the
best current interpretation. New work must explain scope and evidentiary tier, but it does
not need a new decision record merely to revisit an empirical question.

This policy should be reviewed when the status vocabulary, artifact model, or publication
contract changes. It is superseded if a later record replaces the tiered evidence model.
