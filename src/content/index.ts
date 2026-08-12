/**
 * The typed content layer. Every fact the app is allowed to display lives here,
 * with its evidence status, its `as of` date, and a link back to the page that owns
 * it.
 *
 * Three rules for anything importing from this directory:
 *
 * 1. **Do not hardcode a number in a component.** If a figure is missing, add it
 *    here with its source, or say the repository does not have it.
 * 2. **Carry the caveat with the claim.** Every optimistic figure in this record has
 *    a paired caveat, and they travel together or neither travels.
 * 3. **Do not upgrade a status.** `unresolved` is not a promotion, `exploratory`
 *    permits use as an implementation proxy in a later experiment and nothing else,
 *    and nothing here reached `production-eligible`.
 *
 * Nothing in this layer is advice, and nothing in it forecasts a market.
 */

export * from "~/content/confidence";
export * from "~/content/edgeBudget";
export * from "~/content/experiments";
export * from "~/content/glossary";
export * from "~/content/openQuestions";
export * from "~/content/placement";
export * from "~/content/portfolio";
export * from "~/content/sleeves";
export * from "~/content/types";
