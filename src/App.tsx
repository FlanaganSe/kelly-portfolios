import { useState } from "preact/hooks";
import { Link, Route, Switch } from "wouter";
import { Icon } from "~/components/Icon";
import { ErrorBoundary } from "./components/ErrorBoundary";
import AboutComponent from "./routes/about";
import ArticlesComponent from "./routes/articles";
import CalculatorComponent from "./routes/calculator";
import IndexComponent from "./routes/index";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About" },
  { href: "/calculator", label: "Calculator" },
  { href: "/articles", label: "Articles" },
] as const;

export default function App() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <header className="glass sticky top-0 z-50">
          <div className="container mx-auto px-6 py-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="icon-gradient w-12 h-12">
                  <Icon name="portfolio" size={8} className="text-white" aria-label="Portfolio logo" />
                </div>
                <Link href="/" className="text-2xl font-bold gradient-text hover:scale-105 transition-transform">
                  Portfolio Optimizer
                </Link>
              </div>
              <div className="flex items-center gap-4">
                <nav className="hidden md:flex gap-8">
                  {navItems.map(({ href, label }) => (
                    <Link
                      key={href}
                      href={href}
                      className="text-slate-600 hover:text-slate-900 transition-all font-medium text-lg"
                    >
                      {label}
                    </Link>
                  ))}
                </nav>

                <button
                  type="button"
                  className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-all"
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  aria-label="Toggle mobile menu"
                >
                  <Icon name={isMobileMenuOpen ? "close" : "menu"} size={6} aria-label="Menu" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <>
            <button
              type="button"
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden"
              onClick={closeMobileMenu}
              onKeyDown={(e) => e.key === "Escape" && closeMobileMenu()}
              aria-label="Close mobile menu"
            />
            <div className="fixed top-[85px] left-0 right-0 md:hidden glass border-t border-slate-200/60 z-40">
              <div className="container mx-auto px-6 py-4">
                <nav className="flex flex-col space-y-4">
                  {navItems.map(({ href, label }) => (
                    <Link
                      key={href}
                      href={href}
                      className="text-slate-600 hover:text-slate-900 transition-all font-medium text-lg py-2"
                      onClick={closeMobileMenu}
                    >
                      {label}
                    </Link>
                  ))}
                </nav>
              </div>
            </div>
          </>
        )}

        <main className="flex-1">
          <Switch>
            <Route path="/" component={IndexComponent} />
            <Route path="/about" component={AboutComponent} />
            <Route path="/calculator" component={CalculatorComponent} />
            <Route path="/articles" component={ArticlesComponent} />
          </Switch>
        </main>

        <footer className="glass border-t border-slate-200/60 mt-auto">
          <div className="container mx-auto px-6 py-12">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="flex items-center gap-4">
                <div className="icon-gradient w-10 h-10">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Portfolio logo"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                    />
                  </svg>
                </div>
                <div>
                  <div className="text-slate-900 font-bold text-lg">Portfolio Optimizer</div>
                  <div className="text-slate-600">Mathematical precision for investment success</div>
                </div>
              </div>
              <div className="flex items-center gap-8">
                <a
                  href="https://github.com/FlanaganSe/investing-portfolio"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 text-slate-600 hover:text-slate-900 transition-all font-medium group"
                >
                  <svg
                    className="w-6 h-6 group-hover:scale-110 transition-transform"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="GitHub"
                  >
                    <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                  </svg>
                  View on GitHub
                </a>
                <div className="text-slate-500 font-medium">© 2025 Portfolio Optimizer</div>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}
