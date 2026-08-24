import { Meta, MetaProvider, Title } from "@solidjs/meta";
import { A, Navigate, Route, Router, useLocation } from "@solidjs/router";
import { createEffect, createSignal, For, lazy, type ParentComponent } from "solid-js";
import { ErrorBoundary } from "~/components/ErrorBoundary";
import { ThemeToggle } from "~/components/ThemeToggle";
import { CORPUS_AS_OF, NAV_ITEMS, REPO_URL } from "~/lib/nav";

const StartHere = lazy(() => import("~/routes/start-here"));
const Portfolios = lazy(() => import("~/routes/portfolios"));
const PortfolioDetail = lazy(() => import("~/routes/portfolio-detail"));
const Research = lazy(() => import("~/routes/research"));
const Funds = lazy(() => import("~/routes/funds"));
const Lab = lazy(() => import("~/routes/lab"));
const FundDetail = lazy(() => import("~/routes/fund-detail"));
const ResearchDetail = lazy(() => import("~/routes/research-detail"));
const Portfolio = lazy(() => import("~/routes/portfolio"));
const EdgeBudget = lazy(() => import("~/routes/edge-budget"));
const Placement = lazy(() => import("~/routes/placement"));
const Confidence = lazy(() => import("~/routes/confidence"));
const Evidence = lazy(() => import("~/routes/evidence"));
const Concepts = lazy(() => import("~/routes/concepts"));
const Method = lazy(() => import("~/routes/method"));
const NotFound = lazy(() => import("~/routes/not-found"));

const linkBase = "inline-block py-2 text-sm transition-colors border-b-2 -mb-px";
const linkActive = `${linkBase} border-accent font-medium text-ink`;
const linkInactive = `${linkBase} border-transparent text-ink-muted hover:text-ink hover:border-rule-strong`;

const Layout: ParentComponent = (props) => {
  const [menuOpen, setMenuOpen] = createSignal(false);
  const location = useLocation();

  // A route change closes the collapsed menu. No overlay, nothing to dismiss.
  createEffect(() => {
    void location.pathname;
    setMenuOpen(false);
  });

  return (
    <div class="flex min-h-screen flex-col bg-paper text-ink">
      <a
        href="#main"
        class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-[3px] focus:bg-raised focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to content
      </a>

      <header class="border-b border-rule">
        <div class="mx-auto w-full max-w-page px-5 sm:px-8">
          {/* Masthead. */}
          <div class="flex items-center justify-between gap-4 py-4">
            <A href="/" class="font-serif text-xl tracking-[-0.01em] text-ink transition-colors hover:text-accent">
              Portfolio Edge
            </A>

            <div class="flex items-center gap-2">
              <span data-numeric class="hidden text-xs text-ink-faint sm:inline">
                as of {CORPUS_AS_OF}
              </span>
              <ThemeToggle />
              <button
                type="button"
                class="inline-flex h-8 items-center gap-1.5 rounded-[3px] border border-rule px-2.5 text-sm text-ink-muted transition-colors hover:border-rule-strong hover:text-ink lg:hidden"
                aria-expanded={menuOpen()}
                aria-controls="sections"
                onClick={() => setMenuOpen(!menuOpen())}
              >
                Sections
                <svg
                  viewBox="0 0 12 12"
                  width="10"
                  height="10"
                  aria-hidden="true"
                  class="transition-transform"
                  style={{ transform: menuOpen() ? "rotate(180deg)" : "none" }}
                >
                  <path
                    d="M2.5 4.5 6 8l3.5-3.5"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Sections. A row on wide screens, a list under the masthead on narrow ones. */}
          <nav
            id="sections"
            aria-label="Sections"
            class={`border-t border-rule lg:block lg:border-t-0 ${menuOpen() ? "block" : "hidden"}`}
          >
            <ul class="flex flex-col gap-x-6 pb-2 lg:flex-row lg:flex-wrap lg:pb-0">
              <For each={NAV_ITEMS}>
                {(item) => (
                  <li>
                    <A href={item.href} end={item.href === "/"} activeClass={linkActive} inactiveClass={linkInactive}>
                      {item.label}
                    </A>
                  </li>
                )}
              </For>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main" class="mx-auto w-full max-w-page flex-1 px-5 py-12 sm:px-8 sm:py-16">
        {props.children}
      </main>

      <footer class="mt-16 border-t border-rule">
        <div class="mx-auto flex w-full max-w-page flex-col gap-3 px-5 py-8 text-sm text-ink-muted sm:flex-row sm:items-baseline sm:justify-between sm:px-8">
          <p class="max-w-measure">Nothing here is advice, and no sleeve in the underlying research is promoted.</p>
          <p class="flex items-baseline gap-4 whitespace-nowrap">
            <a href={REPO_URL} target="_blank" rel="noopener noreferrer" class="link">
              GitHub
            </a>
            <span data-numeric class="text-ink-faint">
              Research as of {CORPUS_AS_OF}
            </span>
          </p>
        </div>
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <ErrorBoundary>
      {/* The defaults. A route's own <Title> or <Meta> cascades over these and
          is restored when that route unmounts. */}
      <MetaProvider>
        <Title>Portfolio Edge</Title>
        <Meta
          name="description"
          content="A reading of the portfolio research in this repository: what was tested, what survived, and what it is worth."
        />
        <Router root={Layout}>
          <Route path="/" component={StartHere} />
          <Route path="/portfolios" component={Portfolios} />
          <Route path="/portfolios/:id" component={PortfolioDetail} />
          <Route path="/research" component={Research} />
          <Route path="/research/:slug" component={ResearchDetail} />
          <Route path="/funds" component={Funds} />
          <Route path="/funds/:ticker" component={FundDetail} />
          <Route path="/lab" component={Lab} />
          <Route path="/reference" component={Portfolio} />
          {/* `/portfolio` was this page's address before the portfolio library existed.
              One character apart from `/portfolios` is a trap, so it redirects. */}
          <Route path="/portfolio" component={() => <Navigate href="/reference" />} />
          <Route path="/edge-budget" component={EdgeBudget} />
          <Route path="/placement" component={Placement} />
          <Route path="/confidence" component={Confidence} />
          <Route path="/evidence" component={Evidence} />
          <Route path="/concepts" component={Concepts} />
          <Route path="/method" component={Method} />
          <Route path="*" component={NotFound} />
        </Router>
      </MetaProvider>
    </ErrorBoundary>
  );
}
