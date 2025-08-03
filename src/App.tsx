import { Link, Route, Switch } from "wouter";
import AboutComponent from "./routes/about";
import ArticlesComponent from "./routes/articles";
import CalculatorComponent from "./routes/calculator";
import IndexComponent from "./routes/index";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex flex-col">
      <header className="bg-slate-900/95 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
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
              <Link
                href="/"
                className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent hover:from-blue-300 hover:to-cyan-300 transition-all"
              >
                Portfolio Optimizer
              </Link>
            </div>
            <nav className="flex gap-8">
              <Link href="/" className="text-slate-300 hover:text-white transition-colors font-medium">
                Home
              </Link>
              <Link href="/about" className="text-slate-300 hover:text-white transition-colors font-medium">
                About
              </Link>
              <Link href="/calculator" className="text-slate-300 hover:text-white transition-colors font-medium">
                Calculator
              </Link>
              <Link href="/articles" className="text-slate-300 hover:text-white transition-colors font-medium">
                Articles
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Switch>
          <Route path="/" component={IndexComponent} />
          <Route path="/about" component={AboutComponent} />
          <Route path="/calculator" component={CalculatorComponent} />
          <Route path="/articles" component={ArticlesComponent} />
        </Switch>
      </main>

      <footer className="bg-slate-900/80 backdrop-blur-sm border-t border-slate-700 mt-auto">
        <div className="container mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-white"
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
                <div className="text-white font-semibold">Portfolio Optimizer</div>
                <div className="text-slate-400 text-sm">Mathematical precision for investment success</div>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <a
                href="https://github.com/FlanaganSe/investing-portfolio"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" role="img" aria-label="GitHub">
                  <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                </svg>
                View on GitHub
              </a>
              <div className="text-slate-400 text-sm">© 2025 Portfolio Optimizer</div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
