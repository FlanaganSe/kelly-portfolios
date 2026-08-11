# Repository assessment

**Question.** What is this repository, what actually works, and what has to be
settled before it becomes a substantial research project?

**Conclusion.** As of 2026-08-11, Kelly Portfolios is a SolidJS marketing-and-
calculator front end with a serverless AWS design that is described but not
committed. It is a credible starting point for UI and API-contract work. It is not
a research system: no backend in this checkout implements the API it calls, no test
covers the optimization it advertises, and the numbers it shows are either
synthetic or unreachable. The financial claims in the product are ahead of the code
by a wide margin, and closing that gap is the first real piece of work.

## What exists

The tracked client serves home, about, calculator, and articles routes through
`@solidjs/router`. `src/services/api.ts` is a typed client for six endpoints —
asset listing and lookup, volatility, correlation, and Kelly allocation — and the
calculator drives asset search, correlation, and allocation entirely through it.
`src/components/` holds the volatility chart, correlation matrix, asset search, and
an error boundary; charts use Chart.js. Strict TypeScript, Biome 2.3, Vite 7,
pnpm 10, a pre-push hook, and a pull-request workflow give the front end a
reasonable baseline.

`sst.config.ts` intends to deploy a static site alongside imported storage,
database, and API modules, wiring `VITE_API_URL` from the API's URL. Production
deploys are tag-triggered in `.github/workflows/deploy-prod.yaml`.

## What is missing or misleading

1. **The system is not deployable from this checkout.** `sst.config.ts` imports
   `./infra/storage`, `./infra/database`, and `./infra/api`; none of those
   directories are in Git, and neither are the `functions/` handlers the API would
   route to. `pnpm build` succeeds because Vite never evaluates `sst.config.ts`.
2. **The advertised math is not the shipped math.**
   `src/utils/calculateOptimizedPortfolio.ts` is titled "Kelly Criterion Portfolio
   Optimizer" but maximises `μ − ½γσ²`, a mean-variance utility with a
   risk-aversion parameter, using projected gradient descent with a numerical
   gradient at `h = 1e-8`. Its relationship to log-growth Kelly sizing is asserted,
   not derived. It is also unreachable: after the removal of the unrouted
   `src/routes/calculator-old.tsx` in this change, nothing imports it.
   `scripts/mean-variance.py` is a second unwired reference implementation.
3. **Data provenance is absent.** `scripts/seed-database.ts` labels its histories
   as mock and generates them from an unseeded random walk, so its output is
   neither observed nor reproducible between runs.
4. **Product copy overstates the system.** `src/routes/calculator.tsx` promises
   "real-time volatility and historical data"; `src/routes/about.tsx` cites
   "testing by quantitative finance professionals"; the home page and calculator
   describe results as "optimal". Nothing in the repository supports any of these,
   and the calculator degrades to nothing at all without `VITE_API_URL`. The
   "Black Swan Protection" control is passed to an endpoint whose behaviour is
   undefined here.
5. **No tests of any kind.** CI checks formatting, types, and bundling. Nothing
   checks that a constraint holds, that weights sum to one, that annualisation is
   consistent, or that a correlation matrix is positive semi-definite.

## Tooling integrity

The verification loop agents are told to trust was previously broken end to end,
and silently. `pnpm setup` never ran the repository's script, because `setup` is a
built-in pnpm command; the script it shadowed pointed `core.hooksPath` at
`.githooks` while the hook lived in `scripts/githooks/`; and that hook invoked a
`biome:check` script that did not exist. Hook installation now runs from `prepare`
on `pnpm install`, against the real path, executing the same commands as CI.

Static analysis also skipped the code agents are most likely to touch: Biome
inspected only `src/**` and root files, and `tsconfig.json` excluded `scripts/`,
leaving the seed script unlinted and untyped. Both now cover `scripts/`, plus
`infra/` and `functions/` for when those modules return.

Checked 2026-08-11 with pnpm 10.34.5 and Node 26.5.0: `pnpm biome check`,
`pnpm typecheck`, and `pnpm build` pass on a clean tree. CI pins Node 22, so these
gates are verified only on the local toolchain above.

## Documentation history

Three root files — a generated execution prompt and two PRDs, 133 KB combined —
were removed before this assessment. They duplicated requirements, referenced a
different local path, and contradicted both the code and each other, including
Timestream versus DynamoDB storage and simultaneous "no backend" and backend
claims. Reconstructing intent from them is not worthwhile; Git history holds them
if it ever is. The agent and documentation configuration that replaced them is
covered in [agent configuration](2026-08-11-agent-configuration.md).

## Recommended order of work

1. **Fix the claims or fix the code, and decide which.** Separate educational
   output from anything resembling personalised investment advice, and remove
   "real-time", "optimal", and "validated by professionals" wherever the code does
   not earn them. This is cheap and it is currently the largest risk.
2. **Install a test runner and pin the objective.** Write the derivation that
   relates the implemented utility to Kelly log-growth sizing, then cover it with
   constraint tests, numerical edge cases, unit and annualisation checks, and at
   least one fixture computed independently of the implementation.
3. **Recover or rebuild `infra/` and `functions/`,** then generate the API contract
   from shared types instead of maintaining prose on both sides.
4. **Establish data provenance** — source, retrieval date, units, periods, and a
   fixed seed for synthetic data — before any external market data or published
   performance figure enters the project.
5. **Add a calculator user-flow test** once an endpoint exists to exercise.

Items 1 and 2 are independent of the missing backend and can start immediately.
