import { Link } from "wouter";

export default function Home() {
  return (
    <div className="hero-gradient">
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-24 animate-fade-up">
          <div className="mb-8">
            <span className="inline-flex items-center px-4 py-2 bg-blue-50 text-blue-700 text-sm font-medium rounded-full border border-blue-200">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <title>Checkmark icon</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Mathematical Portfolio Optimization
            </span>
          </div>
          <h1 className="text-6xl md:text-8xl font-bold gradient-text mb-8 leading-tight text-balance">
            Portfolio Optimizer
          </h1>
          <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-light text-balance">
            Transform your investment strategy with the Kelly Criterion and modern portfolio theory. Achieve optimal
            risk-adjusted returns through mathematical precision.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-20 animate-fade-up-delay">
          <div className="card card-hover p-10">
            <div className="flex items-start mb-8 gap-6">
              <div className="icon-gradient min-w-12 h-12">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <title>Bar chart icon</title>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <div>
                <h2 className="text-3xl font-bold text-slate-900 mb-4">Kelly Criterion</h2>
                <p className="text-lg text-slate-600 leading-relaxed mb-6">
                  Mathematical formula for optimal capital allocation that maximizes long-term growth while minimizing
                  risk of ruin.
                </p>
              </div>
            </div>
            <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-xl p-6 mb-4">
              <div className="font-mono text-2xl text-blue-900 font-bold text-center mb-2">f* = (bp - q) / b</div>
              <p className="text-slate-600 text-sm text-center">
                f* = fraction to allocate, b = odds, p = win probability, q = loss probability
              </p>
            </div>
          </div>

          <div className="card card-hover p-10">
            <div className="flex items-start mb-8 gap-6">
              <div className="bg-gradient-to-br from-emerald-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/25 min-w-12 h-12">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <title>Line chart icon</title>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                  />
                </svg>
              </div>
              <div>
                <h2 className="text-3xl font-bold text-slate-900 mb-4">Optimal Growth</h2>
                <p className="text-lg text-slate-600 leading-relaxed">
                  Achieve maximum geometric growth with intelligent risk management that adapts to market conditions.
                </p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center text-slate-700">
                <div className="w-3 h-3 bg-emerald-500 rounded-full mr-4"></div>
                <span className="font-medium">Maximizes long-term wealth accumulation</span>
              </div>
              <div className="flex items-center text-slate-700">
                <div className="w-3 h-3 bg-emerald-500 rounded-full mr-4"></div>
                <span className="font-medium">Prevents dangerous over-leveraging</span>
              </div>
              <div className="flex items-center text-slate-700">
                <div className="w-3 h-3 bg-emerald-500 rounded-full mr-4"></div>
                <span className="font-medium">Dynamic adaptation to market changes</span>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center mb-32">
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/calculator">
              <button type="button" className="btn-primary text-lg group">
                Start Optimizing Your Portfolio
                <svg
                  className="w-5 h-5 ml-3 inline group-hover:translate-x-1 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <title>Arrow icon</title>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </Link>
            <Link href="/about">
              <button type="button" className="btn-secondary text-lg">
                Learn More
              </button>
            </Link>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-purple-900/25 group-hover:scale-105 transition-transform duration-300">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <title>Calendar icon</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-4">Mathematical Precision</h3>
            <p className="text-lg text-slate-600 leading-relaxed">
              Data-driven portfolio allocation based on proven quantitative finance principles and decades of research
            </p>
          </div>

          <div className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-amber-600 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-amber-900/25 group-hover:scale-105 transition-transform duration-300">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <title>Lock icon</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-4">Risk Management</h3>
            <p className="text-lg text-slate-600 leading-relaxed">
              Intelligent position sizing that protects capital while maintaining optimal growth potential
            </p>
          </div>

          <div className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-cyan-900/25 group-hover:scale-105 transition-transform duration-300">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <title>Chart with arrow icon</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-4">Long-term Growth</h3>
            <p className="text-lg text-slate-600 leading-relaxed">
              Strategies optimized for sustained wealth building over extended investment horizons
            </p>
          </div>
        </div>

        <div className="mt-24 card p-12 text-center">
          <h2 className="text-4xl font-bold text-slate-900 mb-6 text-balance">Ready to Transform Your Portfolio?</h2>
          <p className="text-xl text-slate-600 mb-8 max-w-3xl mx-auto text-balance">
            Join thousands of investors using mathematical optimization to achieve superior risk-adjusted returns. Start
            building your optimized portfolio in minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/calculator">
              <button type="button" className="btn-primary text-lg group">
                Get Started Free
                <svg
                  className="w-5 h-5 ml-3 inline group-hover:translate-x-1 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <title>Arrow icon</title>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </Link>
            <Link href="/articles">
              <button type="button" className="btn-secondary text-lg">
                Read Articles
              </button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
