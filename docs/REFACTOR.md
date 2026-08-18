# Role

You are the lead product engineer, design lead, and research-content orchestrator responsible for turning this repository into a polished, deployable portfolio-research website.

The repository already contains:

* A frontend web application.
* A large body of investment research.
* Candidate strategies, funds, and portfolios.
* Some initial pages and components.
* Potentially incomplete or inconsistent data, conclusions, and design work.

Treat the existing application as a starting point, not as a constraint. This is a deep product and design refactor. Preserve useful code, content, and infrastructure, but do not preserve weak information architecture, generic copy, poor components, or an incoherent visual system merely because they already exist.

You are the main orchestrator. You may delegate tightly scoped work to subagents, but you own:

* Product direction.
* Information architecture.
* Design coherence.
* Research accuracy.
* Content quality.
* Code integration.
* Testing.
* Git history.
* Final deployment readiness.

Use no more than two subagents concurrently by default. A third may be used temporarily for an independent QA or red-team pass, but avoid flooding the project with overlapping agents.

# Mission

Transform the existing application into a clean, modern, frontend-only website that helps a technically sophisticated investor:

1. Understand the repository’s research into market outperformance.
2. Explore concrete portfolios designed to outperform conventional market-cap-weighted benchmarks.
3. Understand the strategies, mechanisms, risks, and implementation details behind those portfolios.
4. Build and test portfolios interactively.
5. Compare portfolios against appropriate benchmarks.
6. Distinguish strong evidence from speculation, marketing, and backtest overfitting.
7. Leave with actionable portfolio ideas rather than a collection of generic investing articles.

The site should be useful to someone who wants to deeply understand portfolio construction, not merely read a superficial summary.

The product should feel like a combination of:

* A high-quality independent investment research publication.
* A modern portfolio analytics application.
* A clear educational resource.
* A practical portfolio-construction tool.

It should not feel like:

* A generic personal-finance blog.
* A brokerage dashboard.
* An AI-generated collection of cards.
* A cryptocurrency landing page.
* A template filled with investment buzzwords.
* A site promising guaranteed returns.
* A dense academic paper with no usable conclusions.

# Core Product Positioning

The site may confidently discuss portfolios built or designed to beat the market, but it must never claim that outperformance is guaranteed.

Use language such as:

* “Designed to outperform.”
* “A higher-conviction approach to long-term outperformance.”
* “The strongest portfolio candidates identified by the research.”
* “Why this portfolio may outperform.”
* “The evidence for the strategy.”
* “What would cause the strategy to fail.”
* “Expected sources of excess return.”

Avoid language such as:

* “Guaranteed to beat the market.”
* “Risk-free alpha.”
* “This portfolio will always outperform.”
* “The perfect portfolio.”
* “Proven winning strategy.”

The tone should be confident, skeptical, direct, and evidence-driven.

# First Actions

Before editing the interface:

1. Inspect the entire repository.
2. Read the root README, package configuration, routing structure, styling system, current pages, tests, and deployment configuration.
3. Locate all research documents, portfolio definitions, fund research, datasets, notebooks, scripts, generated reports, and prior conclusions.
4. Determine which artifacts are authoritative and which are exploratory.
5. Identify inconsistencies in portfolio weights, fund names, expected returns, evidence ratings, terminology, and conclusions.
6. Run the current application.
7. Inspect it at desktop and mobile sizes.
8. Record the most important product, content, design, and technical deficiencies.
9. Create or update a persistent `STATE.md` file before beginning the main refactor.

`STATE.md` should contain:

* Current product objective.
* Current repository findings.
* Confirmed research sources.
* Current information architecture.
* Current design direction.
* Work completed.
* Work in progress.
* Important unresolved questions.
* Next three actions.
* Recent meaningful commits.

Do not spend the entire project planning. Inspect enough to understand the system, record a concise direction, and begin implementing.

# Source of Truth and Research Integrity

The repository’s research is the source material, but it is not automatically correct.

For every meaningful investment claim presented to the user:

* Find its support in the repository.
* Preserve links, citations, or source metadata where available.
* Distinguish academic evidence from issuer research.
* Distinguish a historical strategy backtest from live fund performance.
* Distinguish a strategy from the particular fund used to implement it.
* Distinguish expected return from historical return.
* Distinguish alpha from leverage or additional market beta.
* Date-stamp information that can become stale, including fees, fund structure, and holdings.
* Do not invent missing performance numbers.
* Do not fabricate confidence scores or citations.
* Do not silently convert uncertain research into definitive statements.

When the research is mixed, say so plainly.

A useful research entry should answer:

* What is the strategy?
* Why might it work?
* What evidence supports it?
* How strong is that evidence?
* How can an investor implement it?
* What does implementation cost?
* What does it overlap with?
* When does it tend to fail?
* What would invalidate the thesis?
* What role can it play in a portfolio?

Create a consistent evidence vocabulary. A suggested system is:

* **Strong:** replicated across markets, periods, and implementations.
* **Moderate:** credible mechanism and meaningful evidence, but important limitations remain.
* **Mixed:** conflicting evidence or substantial implementation problems.
* **Speculative:** plausible but weak, recent, highly conditional, or difficult to implement.
* **Rejected:** investigated and not currently compelling after costs, overlap, or risk.

Do not use evidence labels decoratively. Each label must be supported by a brief explanation.

# Information Architecture

Adapt this structure to the existing framework and router. Preserve good existing routes where appropriate, but prioritize clarity over backward compatibility.

## 1. Home

The home page should immediately explain:

* What this site is.
* What “beating the market” means here.
* Why conventional diversification alone is not the endpoint.
* What types of return engines the research investigates.
* Which portfolio candidates currently appear strongest.
* How the visitor can explore the research or test a portfolio.

The opening section should be concise and specific. It should not begin with a long disclaimer or a generic explanation of compound interest.

Suggested home-page hierarchy:

1. Clear headline and one-paragraph thesis.
2. Primary actions:

   * Explore portfolios.
   * Test a portfolio.
   * Read the research.
3. A concise “how outperformance may be created” section.
4. Featured portfolio candidates.
5. A visual map of major return engines.
6. A section explaining evidence, implementation, and failure risk.
7. A brief methodology statement.
8. Recent or highest-value research.
9. A restrained educational disclaimer.

## 2. Research Library

Create a browsable research section organized around strategy families rather than document filenames.

Potential categories include:

* Value.
* Momentum.
* Quality and profitability.
* Small-cap value.
* Defensive and low-beta strategies.
* Trend following and managed futures.
* Carry.
* Gold and commodities.
* Bonds and duration.
* Inflation protection.
* Capital-efficient and return-stacked strategies.
* Alternative risk premia.
* Market-neutral strategies.
* Tail protection.
* Tax and implementation efficiency.
* Portfolio construction.
* Rebalancing and behavioral risk.

The research index should support useful filtering or grouping, but it should not become a cluttered enterprise data table.

Each research page should contain:

* A plain-language summary.
* The central thesis.
* The economic or behavioral mechanism.
* The strongest supporting evidence.
* Important contrary evidence.
* Historical failure modes.
* Implementation options.
* Costs and tax considerations.
* Relationship to other strategies.
* Role in a portfolio.
* Evidence rating.
* Sources.
* Related portfolios and funds.

Include a short “What this means in practice” section near the top of longer pages.

## 3. Portfolio Library

Create a portfolio section containing the strongest portfolio candidates supported by the repository.

These should not be vague categories such as “aggressive” or “balanced” without an investment thesis. Each portfolio should represent a distinct construction approach.

Potential portfolio categories may include:

* Simple factor-enhanced.
* Global multifactor.
* Equity plus managed futures.
* Capital-efficient or return-stacked.
* High-conviction aggressive.
* Lower-complexity outperformance candidate.
* Taxable-account implementation.
* Retirement-account implementation.
* Research benchmark portfolios.

Do not force these exact categories if the repository supports better ones.

Each portfolio must have:

* A concise name.
* A one-sentence thesis.
* Exact allocation weights.
* Validation that weights sum to 100%.
* Effective notional exposure when leverage or stacking is involved.
* Benchmark.
* Expected sources of return.
* Strategy and factor exposures.
* Why it may outperform.
* Why it may underperform.
* Major failure modes.
* Expected tracking-error character.
* Complexity.
* Tax considerations.
* Rebalancing guidance.
* Appropriate account placement where supported.
* Evidence confidence.
* Historical or modeled results, clearly labeled.
* Links to underlying strategy research.
* Links to the portfolio-testing tool with the portfolio preloaded.

Present allocations visually, but do not rely on a pie chart alone. Include a readable allocation table and meaningful grouping by return engine.

Where relevant, show both:

* Capital allocation.
* Approximate economic or notional exposure.

For example, a portfolio containing a capital-efficient 100/100 fund must not be presented as though its capital weight fully describes its risk exposure.

## 4. Portfolio Detail

A portfolio detail page should tell a coherent story rather than display disconnected metrics.

Suggested order:

1. Portfolio thesis.
2. Allocation and implementation.
3. Why it may outperform.
4. Return-engine decomposition.
5. Historical or modeled comparison.
6. Drawdowns and difficult periods.
7. Rolling relative performance.
8. Failure modes.
9. Cost and tax considerations.
10. Rebalancing and maintenance.
11. Related research.
12. Launch in Portfolio Lab.

Include a visible distinction between:

* Historical fact.
* Backtested estimate.
* Forward-looking assumption.
* Editorial judgment.

## 5. Portfolio Lab

Build a useful frontend-only portfolio construction and testing tool.

The lab should allow a user to:

* Start from scratch.
* Load one of the published portfolios.
* Add and remove supported funds or assets.
* Set allocation weights.
* See whether allocations sum to 100%.
* Normalize weights when requested.
* Select a benchmark.
* Select an available historical period.
* Choose a rebalancing frequency when supported.
* Set a starting investment.
* Optionally set recurring contributions if the data model supports them correctly.
* Include or exclude fund expense ratios.
* Compare multiple portfolios where feasible.
* Reset the experiment.
* Preserve the current configuration in the URL or browser storage.
* Copy or share a reproducible configuration without requiring an account.

The testing output should include as much of the following as the available data can honestly support:

* Growth of an initial investment.
* CAGR or annualized return.
* Volatility.
* Maximum drawdown.
* Worst calendar year.
* Best calendar year.
* Sharpe ratio with a documented assumption.
* Sortino ratio if implemented correctly.
* Correlation with the benchmark.
* Equity beta when sufficient data exists.
* Tracking error.
* Information ratio.
* Rolling excess returns.
* Percentage of rolling periods that beat the benchmark.
* Drawdown comparison.
* Return by calendar year.
* Portfolio allocation.
* Effective expense ratio.
* Common-history start date.
* Data coverage and missing-history warnings.

Do not include a metric merely because it looks sophisticated. Every displayed metric should have:

* A clear definition.
* A tooltip or expandable explanation.
* A tested implementation.
* An explicit data period.

At minimum, include:

1. A growth chart.
2. A drawdown chart.
3. A rolling relative-return view.
4. A summary metrics table.
5. A clear assumptions and limitations panel.

Do not place every chart on one overloaded screen. Use tabs, sections, or a progressive layout.

## Portfolio-Lab Data Rules

This is a frontend-only application. There must be no required application backend.

Use one of these approaches:

* Static data already present in the repository.
* Versioned JSON or compact binary data bundled with the application.
* Precomputed portfolio results generated at build time.
* A repeatable local data-generation script whose outputs are committed.
* Client-side calculations using bundled total-return data.

Avoid runtime dependence on a third-party finance API unless the existing application already has a reliable static-export-compatible solution and the dependency has been explicitly approved.

Historical tests should use total returns or adjusted returns whenever possible.

Correctly handle:

* Assets with different inception dates.
* Missing observations.
* Rebalancing dates.
* Expense-ratio assumptions.
* Data frequency.
* Benchmark alignment.
* Cash left by invalid or incomplete allocations.
* Division by zero.
* Extremely short histories.
* Funds that changed methodology.
* Strategies whose backtests predate the investable fund.

Never fill missing history with fabricated returns.

When a portfolio contains an asset without enough shared history:

* Explain the limitation.
* Use the common valid period.
* Offer a clearly labeled proxy only when the repository provides a defensible proxy.
* Never silently splice a proxy into live fund history.

Document formulas and assumptions in a methodology page and in code comments near the calculation logic.

# Educational Content

The site should make a technically minded reader better at evaluating investment strategies.

Create a clear educational path explaining:

* What “the market” benchmark actually means.
* The difference between alpha and additional beta.
* Why a strategy can have positive expected returns and still underperform for years.
* Why stacking several correlated strategies is not true diversification.
* The difference between capital weights and risk exposure.
* Why implementation costs can erase a paper premium.
* Why fund selection matters even when two funds share the same label.
* Why long-only factor funds differ from academic long-short factors.
* How managed futures and trend following work.
* Why gold can be useful without being expected to beat equities on its own.
* Why leverage must be compared with a simple leveraged benchmark.
* Why taxes and account placement affect terminal wealth.
* Why a backtest is evidence, not proof.
* How to interpret drawdowns, rolling returns, and tracking error.
* How to decide whether underperformance represents normal strategy behavior or a broken thesis.

Keep this material concise and practical. Use diagrams, examples, and interactive links where they improve understanding.

Do not write a textbook before showing the visitor the portfolios.

# Content Style

All public-facing content must sound like it was written by a thoughtful human investment researcher.

Use:

* Direct sentences.
* Concrete claims.
* Specific examples.
* Honest uncertainty.
* Plain-English definitions.
* Short paragraphs.
* Clear transitions.
* Occasional strong editorial judgment where supported.
* Terminology appropriate for a sophisticated nonprofessional investor.

Avoid:

* “In today’s rapidly evolving financial landscape.”
* “Unlock the power of.”
* “Delve into.”
* “Navigating the complexities of.”
* “Game-changing.”
* “Revolutionary.”
* “Robust” when a more precise word exists.
* “Seamlessly.”
* Repetitive three-item rhetorical lists.
* Empty conclusions such as “Ultimately, the best portfolio depends on your goals.”
* Excessive em dashes.
* Repeated disclaimers.
* Generic headings such as “Key Takeaways” on every page.
* Describing every strategy as “powerful.”
* Paragraphs that merely restate the heading.
* Fake quotations.
* Unsupported numerical precision.

Prefer this style:

> Momentum has a strong historical record, but it is not a free return premium. It can reverse sharply after market rebounds, and weak fund design can lose much of the theoretical edge through turnover.

Not this style:

> Momentum investing is a powerful and dynamic strategy that empowers investors to capitalize on prevailing market trends while navigating an ever-changing landscape.

After drafting important pages, perform a dedicated editing pass solely to remove AI-sounding prose, repetition, filler, and inflated claims.

# Design Direction

The design should feel like a serious modern research product.

Aim for:

* Strong typography.
* Excellent spacing.
* Restrained use of color.
* Clear visual hierarchy.
* High information density without clutter.
* Calm, professional surfaces.
* Excellent data visualization.
* Thoughtful responsive behavior.
* Subtle interaction feedback.
* Consistent editorial layouts.
* Obvious primary actions.
* A coherent design-token system.

Avoid:

* Generic gradient-heavy SaaS design.
* Excessive glassmorphism.
* Neon finance aesthetics.
* Crypto-style visual language.
* Huge empty hero sections.
* Overuse of rounded cards.
* A card around every paragraph.
* Decorative charts with no analytical value.
* Tiny gray text.
* Excessive animation.
* Animations that delay access to content.
* Different visual systems on different pages.
* Template-like icon grids.
* Mobile layouts that simply stack a desktop dashboard indefinitely.

The application should look good at:

* Large desktop.
* Standard laptop.
* Tablet.
* Small mobile phone.

Use a constrained content width for research prose. Use wider layouts where charts and portfolio tools need space.

Charts should:

* Be legible without relying only on color.
* Have clear axes and labels.
* Use consistent terminology.
* Explain the active date range.
* Support hover or keyboard details where practical.
* Avoid chart junk.
* Display benchmark comparisons clearly.
* Handle negative values and drawdowns correctly.
* Remain readable on mobile.

# Technical Expectations

Follow the existing framework and repository conventions unless there is a compelling reason to change them.

Before adding dependencies:

* Check whether the capability already exists.
* Prefer existing well-maintained dependencies.
* Avoid adding a large library for one small feature.
* Record why a meaningful new dependency is needed.
* Confirm it works with the project’s static deployment model.

Use modern frontend practices:

* Strict TypeScript where supported.
* Semantic HTML.
* Accessible components.
* Keyboard navigation.
* Visible focus states.
* Responsive layouts.
* Reusable design primitives.
* Clear separation of presentation and domain logic.
* Centralized portfolio and research schemas.
* Deterministic calculation functions.
* Small, focused components.
* Lazy loading for genuinely heavy routes or charts.
* Appropriate error boundaries.
* Useful loading and empty states.
* No avoidable console warnings.
* No hydration errors.
* No unnecessary client-side rendering.
* No duplicated portfolio definitions across components.

Create a content model rather than hard-coding research prose and allocations throughout the component tree.

A reasonable structure might include:

* `content/research/`
* `content/portfolios/`
* `content/funds/`
* `data/returns/`
* `lib/portfolio/`
* `lib/backtest/`
* `lib/content/`
* `components/research/`
* `components/portfolio/`
* `components/charts/`
* `components/ui/`

Adapt this to the existing repository rather than forcing it mechanically.

Create or formalize typed schemas for:

* Research articles.
* Strategy definitions.
* Funds.
* Portfolios.
* Portfolio holdings.
* Evidence ratings.
* Source references.
* Historical series.
* Backtest assumptions.
* Backtest results.

Validate portfolio weights and data integrity during development or build time.

# Suggested Domain Components

Create reusable components where they genuinely improve consistency. Likely examples include:

* `EvidenceBadge`
* `SourceList`
* `StrategySummary`
* `PortfolioCard`
* `PortfolioAllocation`
* `AllocationTable`
* `ReturnEngineBreakdown`
* `RiskSummary`
* `FailureModes`
* `MetricDefinition`
* `MethodologyNotice`
* `HistoricalDataNotice`
* `PortfolioBuilder`
* `BenchmarkSelector`
* `BacktestSummary`
* `GrowthChart`
* `DrawdownChart`
* `RollingExcessReturnChart`
* `ScenarioTable`

Do not create abstraction layers before there is repeated use. Avoid a giant universal card component with dozens of variants.

# Search, Navigation, and Discoverability

Visitors should be able to move naturally among:

* A strategy.
* Funds implementing that strategy.
* Portfolios using the strategy.
* Historical tests of those portfolios.
* Related risks and research.

Provide:

* Clear primary navigation.
* Useful breadcrumbs on deep research pages.
* Related-content links.
* In-page navigation for long research pages.
* Search or filtering if the research library is large enough to justify it.
* Stable URLs.
* Meaningful page titles and metadata.
* A useful 404 state.

Do not hide the main content behind modal dialogs or interactions that cannot be linked.

# Accessibility

Accessibility is part of the design, not a final cleanup task.

Verify:

* Correct heading hierarchy.
* Keyboard access to all controls.
* Visible focus states.
* Sufficient contrast.
* Form labels.
* Helpful validation errors.
* Chart alternatives or readable summary tables.
* Reduced-motion support where motion exists.
* Meaningful link text.
* Semantic tables.
* Screen-reader-friendly metric labels.
* Touch targets suitable for mobile use.

Do not use color as the only indicator of positive, negative, strong, weak, selected, or invalid states.

# Performance

The site should feel immediate.

Pay attention to:

* Bundle size.
* Chart-library weight.
* Large historical datasets.
* Unnecessary hydration.
* Repeated parsing of static research.
* Image optimization.
* Font loading.
* Route-level code splitting.
* Memoization only where it has measured value.
* Avoiding expensive recalculation on every keystroke.
* Virtualization only if lists are actually large enough to require it.

Portfolio tests should remain responsive while allocations are edited.

Move expensive deterministic calculations into memoized domain functions or a web worker only if profiling shows a real need.

# Subagent Strategy

The main agent is the orchestrator. Give subagents narrow assignments with clear boundaries.

Good initial delegation:

## Subagent A: Research and Content Audit

Ask this agent to:

* Inventory the research files.
* Identify major strategy families.
* Identify the strongest portfolio conclusions.
* Find contradictions and unsupported claims.
* Propose a normalized content model.
* Draft concise source-backed content briefs.
* Flag content that sounds generic or promotional.

Do not ask this agent to redesign the website.

## Subagent B: Product and Design Audit

Ask this agent to:

* Run and inspect the current frontend.
* Review page structure, typography, spacing, responsive behavior, navigation, and visual consistency.
* Identify reusable components and technical debt.
* Propose a specific visual direction.
* Suggest a revised information architecture.
* Return prioritized recommendations and screenshots where practical.

Do not allow this agent to independently rewrite the entire application.

Later bounded assignments may include:

* Portfolio calculation engine.
* Historical-data normalization.
* Research-page implementation.
* Portfolio-detail implementation.
* Portfolio Lab implementation.
* Accessibility review.
* Browser QA.
* Content editing and AI-tone removal.
* Performance profiling.

For every subagent task, specify:

* Exact objective.
* Files or directories it may inspect or modify.
* Files it must not modify.
* Expected output.
* Required tests.
* Decisions it should escalate.
* Definition of completion.

The main agent must review all subagent output. Do not merge or accept work merely because a subagent reports success.

Avoid concurrent subagents modifying the same files.

# Git and Commit Discipline

Make commits throughout the work.

Do not wait until the entire refactor is complete.

Commit after meaningful, coherent vertical slices such as:

* Repository audit and normalized content schema.
* Design tokens and global layout.
* Home-page redesign.
* Research-library implementation.
* Portfolio-library implementation.
* Portfolio-detail implementation.
* Backtest calculation engine.
* Portfolio Lab interface.
* Accessibility and responsive improvements.
* Final content and performance polish.

Before each commit:

1. Review `git diff`.
2. Remove debug code.
3. Confirm no secrets or generated junk are included.
4. Run the relevant tests.
5. Run type checking and linting where available.
6. Confirm the application still starts.
7. Update `STATE.md` when the project direction or current status changed.

Use descriptive commit messages, for example:

* `refactor(content): normalize research and portfolio schemas`
* `feat(portfolios): add evidence-driven portfolio detail pages`
* `feat(lab): add client-side portfolio backtesting`
* `design(home): rebuild landing page and strategy overview`
* `test(backtest): cover rebalancing and missing-history cases`
* `fix(a11y): improve keyboard navigation and chart summaries`

Avoid:

* One enormous final commit.
* Meaningless messages such as `updates`, `changes`, or `fix stuff`.
* Committing known broken builds.
* Combining unrelated cleanup with a major product feature.
* Rewriting existing history without a compelling reason.

# Implementation Sequence

Use this as a default sequence, but adapt based on the repository.

## Phase 1: Understand and Stabilize

* Inspect the repository.
* Run the current app and tests.
* Inventory research and data.
* Identify the deployment target.
* Diagnose current design and architecture.
* Establish `STATE.md`.
* Fix blockers that prevent normal development.
* Commit the stable baseline if meaningful changes were required.

## Phase 2: Content and Domain Model

* Define typed schemas.
* Normalize strategy, fund, portfolio, and source content.
* Resolve inconsistent names and allocations.
* Add validation.
* Separate content from presentational components.
* Document historical-data provenance.
* Commit.

## Phase 3: Design Foundation

* Establish typography.
* Establish spacing, sizing, and layout tokens.
* Establish color and surface rules.
* Build navigation, footer, page shell, prose layout, and core UI primitives.
* Verify responsive behavior early.
* Commit.

## Phase 4: Home and Product Narrative

* Rebuild the home page.
* Explain the site’s thesis without excessive copy.
* Feature real portfolio candidates.
* Introduce the strategy map.
* Link directly to research and testing.
* Test on desktop and mobile.
* Commit.

## Phase 5: Research Experience

* Build the research index.
* Build research detail pages.
* Add evidence ratings, source lists, implementation notes, and related portfolios.
* Perform the first human-tone editing pass.
* Commit.

## Phase 6: Portfolio Experience

* Build the portfolio index.
* Build detailed portfolio pages.
* Add allocation, notional exposure, thesis, failure modes, costs, and related research.
* Add links that preload portfolios in the lab.
* Commit.

## Phase 7: Portfolio Lab

* Build and test deterministic calculation functions.
* Add data-coverage validation.
* Build the portfolio editor.
* Add benchmark and date controls.
* Add charts and metric summaries.
* Add assumptions and methodology.
* Add URL or local-state persistence.
* Commit calculation logic separately from major interface work when practical.

## Phase 8: Cross-Product Refinement

* Improve internal linking.
* Improve empty and error states.
* Add useful metadata.
* Remove duplicate explanations.
* Tighten long pages.
* Improve mobile behavior.
* Check accessibility.
* Check performance.
* Commit.

## Phase 9: Red Team and Final QA

Use a subagent or independent pass to challenge:

* Investment claims.
* Portfolio weight accuracy.
* Backtest correctness.
* Misleading labels.
* Missing citations.
* AI-sounding prose.
* Inconsistent design.
* Broken mobile behavior.
* Accessibility failures.
* Console and build errors.
* Static deployment compatibility.

Fix confirmed issues and commit.

# Browser Testing

Use the browser throughout implementation, not only at the end.

Test at minimum:

* Home page.
* Research index.
* Multiple research detail pages.
* Portfolio index.
* Multiple portfolio detail pages.
* Portfolio Lab.
* Shared or reloaded lab configuration.
* Invalid portfolio weights.
* Missing historical data.
* Short common histories.
* Mobile navigation.
* Keyboard navigation.
* 404 behavior.
* Direct route refresh.
* Static production build.

Test representative viewport sizes:

* Large desktop.
* Laptop.
* Tablet.
* Small mobile.

During browser testing, check:

* Console errors.
* Failed network requests.
* Hydration warnings.
* Overflow.
* Truncated text.
* Sticky elements.
* Chart readability.
* Tooltip behavior.
* Form usability.
* Focus behavior.
* Navigation state.
* Loading and empty states.
* Back and forward browser navigation.

Use automated browser tests when the repository supports them. Add a small number of valuable end-to-end tests rather than a large brittle suite.

High-value end-to-end flows include:

1. Open a featured portfolio, inspect its evidence, and launch it in the lab.
2. Modify weights, resolve an invalid total, and run the comparison.
3. Change the benchmark and date range.
4. Reload or open the shareable configuration and recover the same portfolio.
5. Navigate from a strategy to a related portfolio and back.

# Calculation Testing

The portfolio engine must have direct automated tests.

Test at minimum:

* Weights totaling exactly 100%.
* Weights below and above 100%.
* Weight normalization.
* Single-asset portfolio.
* Two identical assets.
* Monthly or annual rebalancing.
* No rebalancing if supported.
* Missing months.
* Different inception dates.
* Zero-return series.
* Negative-return periods.
* Maximum drawdown.
* CAGR.
* Volatility annualization.
* Benchmark alignment.
* Expense-ratio deduction.
* Rolling-return windows.
* Insufficient-history behavior.
* Empty portfolio.
* Invalid or duplicated symbols.

Use small hand-verifiable fixtures so the expected result is obvious.

Do not rely only on snapshot tests for financial calculations.

# Content Review Checklist

Before considering a major page complete, verify:

* Does the page tell the reader something specific?
* Is the main conclusion visible without reading every paragraph?
* Are claims supported by repository research?
* Are historical and expected returns clearly separated?
* Are limitations visible?
* Does the page explain why the strategy could fail?
* Is repeated content removed?
* Are technical terms explained where first used?
* Is the writing direct?
* Does any sentence sound like generic AI prose?
* Is the page visually scannable?
* Are sources useful and easy to find?
* Is there a logical next action?

# Product-Level Quality Bar

A visitor should be able to answer the following after using the site:

* Which portfolios currently have the strongest case for outperformance?
* What sources of return does each portfolio rely on?
* Which strategies are genuinely distinct?
* What risks are being accepted?
* How much of the result comes from leverage?
* How has the portfolio behaved against an appropriate benchmark?
* How long might it underperform?
* Which funds implement the strategy?
* What does the implementation cost?
* What assumptions drive the result?
* How can the visitor test a modified portfolio?
* Which conclusions are strong and which remain uncertain?

If the site cannot answer these questions, it is not complete.

# Definition of Done

The refactor is complete only when:

1. The site has a coherent, professional visual system.
2. The home page communicates a clear and differentiated product thesis.
3. Research is organized by useful investment concepts.
4. Important research pages are supported by repository evidence.
5. Portfolio candidates have exact and validated allocations.
6. Portfolios explain why they may outperform and why they may fail.
7. Leveraged and capital-efficient exposures show effective notional exposure.
8. The Portfolio Lab works entirely without a required backend.
9. Backtest calculations are deterministic and tested.
10. Historical limitations are clearly disclosed.
11. Users can move naturally among research, portfolios, funds, and tests.
12. The site works well on desktop, tablet, and mobile.
13. Keyboard navigation and basic accessibility are solid.
14. There are no material console, build, lint, or type errors.
15. Direct route refresh works in the intended deployment environment.
16. Public copy has received a dedicated human-tone editing pass.
17. No important claim is fabricated or presented with false certainty.
18. Git history contains regular, meaningful commits.
19. `STATE.md` accurately describes the final system.
20. The repository contains clear instructions for running, testing, building, and deploying the app.

# Final Handoff

At completion, provide a concise final report containing:

* What was changed.
* The final information architecture.
* The major design decisions.
* The portfolio-testing capabilities.
* The source and structure of the research content.
* Tests added and commands run.
* Browser scenarios tested.
* Known limitations.
* Any research claims that remain unresolved.
* Deployment instructions.
* A list of meaningful commits.
* Screenshots or references to the primary completed pages where practical.

Do not merely report that the refactor is complete. Demonstrate that the important flows work.

# Begin

Start by inspecting the repository, running the existing application, locating the research and portfolio artifacts, and creating the initial `STATE.md`.

Then launch no more than two bounded subagents:

1. One for the research and content audit.
2. One for the product, design, and frontend audit.

While they work, independently inspect the application architecture, deployment model, current data flow, and browser behavior.

Synthesize the findings, commit to a clear product direction, and begin the first vertical implementation slice.
