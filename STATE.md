# STATE

`as of 2026-08-17` · branch `further-research`

## Objective

Turn this repository's client into a portfolio-research website that presents a
concrete candidate portfolio designed to outperform a cap-weighted benchmark, the
evidence behind each of its return engines, and a frontend-only lab for testing
alternatives. Confident and evidence-driven; never a guarantee.

## Direction (committed)

- Keep the existing design system in `src/styles.css`. It is already a serious
  editorial system: tokens, dark mode, tabular numerals, one accent. Extend, do not
  replace.
- Keep the existing typed content layer discipline (`src/content/`): no number in a
  component, every figure carries status, `as of` and source.
- The candidate portfolio is a **first-class object** with its own schema, validated
  weights, and both capital and notional exposure.
- The lab computes forward expected edge (the repository's own tested arithmetic) and,
  where honest data exists, a clearly labelled factor-model reconstruction. It never
  presents a fund NAV backtest the repository cannot source.

## Work in progress

Phase 1: repository inspection and audits.

## Next three actions

1. Land the audits and fix the content model.
2. Build the fund and portfolio registries with validation tests.
3. Rebuild the home page around the candidate portfolio.
