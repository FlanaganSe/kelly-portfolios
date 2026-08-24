/**
 * The reader's own inputs: one shared store, persisted to this browser and nowhere else.
 *
 * Three properties matter more than the fields.
 *
 * 1. **The empty policy is a valid, complete state.** Every field is optional and
 *    {@link resolvePolicy} fills the gaps with the repository's stated reference
 *    investor — US federal top bracket, thirty-year horizon, contributions continuing,
 *    state tax excluded. A consumer renders fully with nothing entered. It must also
 *    *say* which figures are the reference investor's rather than the reader's, which
 *    is what {@link ResolvedPolicy.defaulted} is for. Entering a policy narrows a page.
 *    It is never a gate, and there is no onboarding flow.
 * 2. **Versioned and defensive.** One key, one version. An unknown version, malformed
 *    JSON, a blocked storage API or a field of the wrong type is discarded and the
 *    policy starts empty. Stale localStorage must never white-screen a page, and a
 *    value outside its valid range must never reach `~/lib/placement`, which throws on
 *    one.
 * 3. **Nothing leaves the browser.** No network, no analytics, no third party. `clear()`
 *    removes the key outright, and every page holding this store makes it reachable.
 *
 * ## Exported API
 *
 * ```ts
 * // The shared instance. Call it from any component; they all see the same state.
 * const policy = useInvestorPolicy();
 *
 * policy.policy                       // InvestorPolicy — reactive, only what was entered
 * policy.resolved()                   // ResolvedPolicy — reactive, gaps filled
 * policy.update({ horizonYears: 20 }) // merge a patch; undefined removes a field
 * policy.clear()                      // back to empty, and drop the stored key
 *
 * // Types
 * InvestorPolicy, ResolvedPolicy, CustomRegimeRates, AccountBalances, RegimeSelection
 *
 * // Values and pure helpers, all safe to call in a test without rendering
 * POLICY_STORAGE_KEY, POLICY_VERSION, REFERENCE_INVESTOR
 * resolvePolicy(policy)               // ResolvedPolicy, no storage and no reactivity
 * regimeFor(policy)                   // the TaxRegime a selection resolves to
 * parseStoredPolicy(raw)              // string | null -> InvestorPolicy, never throws
 * serialisePolicy(policy)             // InvestorPolicy -> the stored JSON string
 * createInvestorPolicyStore()         // a fresh, independent store over localStorage
 * ```
 *
 * `resolved()` recomputes on read inside a tracking scope, so a memo around it is
 * optional rather than required. `update` is a shallow merge: pass a whole `accounts`
 * object to change one balance, or `undefined` to drop a field back to its default.
 */

import { createStore, reconcile } from "solid-js/store";
import { defaultTaxRegime, type TaxRegimeId, taxRegimes } from "~/content/placement";
import type { TaxRegime } from "~/lib/placement";

/** One key, one shape. Bump {@link POLICY_VERSION} rather than reusing this. */
export const POLICY_STORAGE_KEY = "pe-investor-policy";

/** The stored shape's version. An unknown value is discarded, never migrated in place. */
export const POLICY_VERSION = 1;

/** A named regime, or the reader's own three rates. */
export type RegimeSelection = TaxRegimeId | "custom";

/** Rates a reader typed. Decimals, not percentages: 0.24 is 24%. */
export interface CustomRegimeRates {
  readonly ordinaryIncome: number;
  readonly longTermCapitalGain: number;
  readonly netInvestmentIncome: number;
}

/** Balances in dollars. All optional: an unentered account is not a zero balance. */
export interface AccountBalances {
  readonly taxable?: number;
  readonly traditional?: number;
  readonly roth?: number;
  readonly hsa?: number;
}

/** What the reader has actually entered. Every field absent is the valid empty state. */
export interface InvestorPolicy {
  readonly regimeId?: RegimeSelection;
  /** Read only when `regimeId` is `"custom"`. */
  readonly customRegime?: CustomRegimeRates;
  readonly horizonYears?: number;
  readonly contributionsContinue?: boolean;
  readonly withdrawalsBegun?: boolean;
  readonly accounts?: AccountBalances;
  readonly hasHighDeductiblePlan?: boolean;
  /** The share of a foreign credit the §904 limitation actually lets through, 0…1. */
  readonly foreignCreditUtilisation?: number;
}

/** The policy with every gap filled, plus a record of which gaps there were. */
export interface ResolvedPolicy {
  readonly regimeId: RegimeSelection;
  readonly regime: TaxRegime;
  readonly horizonYears: number;
  readonly contributionsContinue: boolean;
  readonly withdrawalsBegun: boolean;
  readonly accounts: AccountBalances;
  readonly hasHighDeductiblePlan: boolean;
  readonly foreignCreditUtilisation: number;
  /** True for each field the reader has not supplied, so a page can label the fallback. */
  readonly defaulted: Readonly<Record<keyof InvestorPolicy, boolean>>;
  /** Nothing at all has been entered. Every figure on the page is the reference investor's. */
  readonly isEmpty: boolean;
}

/**
 * The reference investor, as defaults.
 *
 * The bracket, the horizon and the contribution assumption are the ones the
 * recommendation page states its figures for. State tax is excluded there and excluded
 * here, and it is additive, so a reader in a taxing state is looking at a floor.
 */
export const REFERENCE_INVESTOR = {
  regimeId: defaultTaxRegime.id,
  horizonYears: 30,
  contributionsContinue: true,
  withdrawalsBegun: false,
  hasHighDeductiblePlan: false,
  /** §904 lets the whole credit through until the $300/$600 threshold is crossed. */
  foreignCreditUtilisation: 1,
} as const satisfies Required<Omit<InvestorPolicy, "customRegime" | "accounts">>;

/**
 * A fresh empty policy every time.
 *
 * Never a shared constant: `createStore` takes ownership of the object it is given and
 * mutates it, so handing the same one to two stores makes them the same store.
 */
function emptyPolicy(): InvestorPolicy {
  return {};
}

/** The custom regime carries no source date, because a rate a reader typed has none. */
const CUSTOM_REGIME_LABEL = "Your own rates";

function isRegimeSelection(value: unknown): value is RegimeSelection {
  return value === "custom" || taxRegimes.some((regime) => regime.id === value);
}

function isRate(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value < 1;
}

function isCustomRegimeRates(value: unknown): value is CustomRegimeRates {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return isRate(record.ordinaryIncome) && isRate(record.longTermCapitalGain) && isRate(record.netInvestmentIncome);
}

function sanitiseAccounts(value: unknown): AccountBalances | undefined {
  if (typeof value !== "object" || value === null) return undefined;
  const record = value as Record<string, unknown>;
  const accounts: { -readonly [K in keyof AccountBalances]: number } = {};
  for (const key of ["taxable", "traditional", "roth", "hsa"] as const) {
    const balance = record[key];
    if (typeof balance === "number" && Number.isFinite(balance) && balance >= 0) accounts[key] = balance;
  }
  return Object.keys(accounts).length > 0 ? accounts : undefined;
}

/**
 * Drop anything that is not a usable value of its field.
 *
 * A dropped field is not an error: it falls back to the reference investor like an
 * unentered one. This runs on every read *and* on every write, so a bad value cannot
 * enter the store from stale storage or from a caller.
 */
function sanitisePolicy(value: unknown): InvestorPolicy {
  if (typeof value !== "object" || value === null) return emptyPolicy();
  const record = value as Record<string, unknown>;
  const policy: { -readonly [K in keyof InvestorPolicy]: InvestorPolicy[K] } = {};

  if (isRegimeSelection(record.regimeId)) policy.regimeId = record.regimeId;
  if (isCustomRegimeRates(record.customRegime)) policy.customRegime = record.customRegime;
  if (typeof record.horizonYears === "number" && Number.isFinite(record.horizonYears) && record.horizonYears > 0) {
    policy.horizonYears = record.horizonYears;
  }
  if (typeof record.contributionsContinue === "boolean") policy.contributionsContinue = record.contributionsContinue;
  if (typeof record.withdrawalsBegun === "boolean") policy.withdrawalsBegun = record.withdrawalsBegun;
  const accounts = sanitiseAccounts(record.accounts);
  if (accounts !== undefined) policy.accounts = accounts;
  if (typeof record.hasHighDeductiblePlan === "boolean") policy.hasHighDeductiblePlan = record.hasHighDeductiblePlan;
  // Outside [0, 1] this throws in `~/lib/placement`, so the range is enforced here.
  if (
    typeof record.foreignCreditUtilisation === "number" &&
    Number.isFinite(record.foreignCreditUtilisation) &&
    record.foreignCreditUtilisation >= 0 &&
    record.foreignCreditUtilisation <= 1
  ) {
    policy.foreignCreditUtilisation = record.foreignCreditUtilisation;
  }

  return policy;
}

/**
 * The regime a policy selects.
 *
 * `"custom"` without usable rates — only reachable by hand-editing storage, since the
 * interface seeds the rates when the selection changes — resolves to the reference
 * investor's bracket rather than throwing.
 */
export function regimeFor(policy: InvestorPolicy): TaxRegime {
  if (policy.regimeId === "custom" && policy.customRegime !== undefined) {
    return {
      label: CUSTOM_REGIME_LABEL,
      asOf: "",
      ordinaryIncome: policy.customRegime.ordinaryIncome,
      longTermCapitalGain: policy.customRegime.longTermCapitalGain,
      netInvestmentIncome: policy.customRegime.netInvestmentIncome,
    };
  }
  const named = taxRegimes.find((regime) => regime.id === policy.regimeId);
  return named ?? defaultTaxRegime;
}

/** Fill every gap with the reference investor's value, and record which gaps there were. */
export function resolvePolicy(policy: InvestorPolicy): ResolvedPolicy {
  // A "custom" selection with no usable rates reports as the bracket it actually resolved to.
  const unusableCustom = policy.regimeId === "custom" && policy.customRegime === undefined;
  const regimeId = unusableCustom ? REFERENCE_INVESTOR.regimeId : (policy.regimeId ?? REFERENCE_INVESTOR.regimeId);
  return {
    regimeId,
    regime: regimeFor(policy),
    horizonYears: policy.horizonYears ?? REFERENCE_INVESTOR.horizonYears,
    contributionsContinue: policy.contributionsContinue ?? REFERENCE_INVESTOR.contributionsContinue,
    withdrawalsBegun: policy.withdrawalsBegun ?? REFERENCE_INVESTOR.withdrawalsBegun,
    accounts: policy.accounts ?? {},
    hasHighDeductiblePlan: policy.hasHighDeductiblePlan ?? REFERENCE_INVESTOR.hasHighDeductiblePlan,
    foreignCreditUtilisation: policy.foreignCreditUtilisation ?? REFERENCE_INVESTOR.foreignCreditUtilisation,
    defaulted: {
      regimeId: policy.regimeId === undefined,
      customRegime: policy.customRegime === undefined,
      horizonYears: policy.horizonYears === undefined,
      contributionsContinue: policy.contributionsContinue === undefined,
      withdrawalsBegun: policy.withdrawalsBegun === undefined,
      accounts: policy.accounts === undefined,
      hasHighDeductiblePlan: policy.hasHighDeductiblePlan === undefined,
      foreignCreditUtilisation: policy.foreignCreditUtilisation === undefined,
    },
    isEmpty: Object.keys(policy).length === 0,
  };
}

/** Read a stored payload. Malformed JSON, a foreign shape or an unknown version all give the empty policy. */
export function parseStoredPolicy(raw: string | null): InvestorPolicy {
  if (raw === null || raw === "") return emptyPolicy();
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return emptyPolicy();
  }
  if (typeof parsed !== "object" || parsed === null) return emptyPolicy();
  const { version } = parsed as { version?: unknown };
  if (version !== POLICY_VERSION) return emptyPolicy();
  return sanitisePolicy(parsed);
}

/** What gets written: the version, then the fields. */
export function serialisePolicy(policy: InvestorPolicy): string {
  return JSON.stringify({ version: POLICY_VERSION, ...policy });
}

function readStoredPolicy(): InvestorPolicy {
  try {
    return parseStoredPolicy(localStorage.getItem(POLICY_STORAGE_KEY));
  } catch {
    // A blocked or absent storage API costs persistence, not the page.
    return emptyPolicy();
  }
}

function writeStoredPolicy(policy: InvestorPolicy): void {
  try {
    if (Object.keys(policy).length === 0) localStorage.removeItem(POLICY_STORAGE_KEY);
    else localStorage.setItem(POLICY_STORAGE_KEY, serialisePolicy(policy));
  } catch {
    // Same trade: the session still works, it just will not survive a reload.
  }
}

export interface InvestorPolicyStore {
  /** Reactive. Only what the reader entered; read {@link InvestorPolicyStore.resolved} to render. */
  readonly policy: InvestorPolicy;
  /** Reactive. The policy with the reference investor's values filling the gaps. */
  readonly resolved: () => ResolvedPolicy;
  /** Shallow merge. `undefined` for a field removes it and restores its default. */
  readonly update: (patch: Partial<InvestorPolicy>) => void;
  /** Back to the empty policy, and the stored key is removed. */
  readonly clear: () => void;
}

/**
 * A store of its own, hydrated from localStorage at the moment it is called.
 *
 * {@link useInvestorPolicy} is what pages want. This exists so a test can hold an
 * independent instance, and so hydration happens on first use rather than at import.
 */
export function createInvestorPolicyStore(): InvestorPolicyStore {
  const [policy, setPolicy] = createStore<InvestorPolicy>(readStoredPolicy());

  const commit = (next: InvestorPolicy): void => {
    const clean = sanitisePolicy(next);
    writeStoredPolicy(clean);
    setPolicy(reconcile(clean));
  };

  return {
    policy,
    resolved: () => resolvePolicy(policy),
    update: (patch) => {
      const merged: Record<string, unknown> = { ...policy, ...patch };
      for (const key of Object.keys(merged)) {
        if (merged[key] === undefined) delete merged[key];
      }
      commit(merged as InvestorPolicy);
    },
    clear: () => commit(emptyPolicy()),
  };
}

let shared: InvestorPolicyStore | undefined;

/** The one store every page shares. Created on first call, not at import. */
export function useInvestorPolicy(): InvestorPolicyStore {
  shared ??= createInvestorPolicyStore();
  return shared;
}
