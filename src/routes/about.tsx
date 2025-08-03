export default function About() {
  return (
    <div className="hero-gradient min-h-screen">
      <div className="container mx-auto px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-20">
            <h1 className="text-5xl md:text-7xl font-bold gradient-text mb-8 text-balance">
              About Portfolio Optimizer
            </h1>
            <p className="text-xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-light text-balance">
              Empowering investors with mathematical precision and evidence-based portfolio optimization strategies
              rooted in decades of quantitative finance research
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-10 mb-20">
            <div className="card p-12">
              <div className="flex items-start mb-8 gap-6">
                <div className="icon-gradient w-12 h-12 min-w-12">
                  <svg
                    className="w-8 h-8 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Mission icon"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-slate-900 mb-4">Our Mission</h2>
                  <p className="text-lg text-slate-600 leading-relaxed">
                    To democratize advanced portfolio optimization techniques by making mathematical finance accessible
                    to individual investors. We believe sophisticated risk management and return optimization should not
                    be exclusive to institutional investors.
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-12">
              <div className="flex items-start mb-8 gap-6">
                <div className="bg-gradient-to-br from-emerald-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/25 min-w-12 h-12">
                  <svg
                    className="w-8 h-8 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Approach icon"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-slate-900 mb-4">Our Approach</h2>
                  <p className="text-lg text-slate-600 leading-relaxed">
                    We leverage proven mathematical frameworks including the Kelly Criterion, Modern Portfolio Theory,
                    and risk parity strategies. Our tools are built on decades of academic research and real-world
                    testing by quantitative finance professionals.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="card p-16 mb-20">
            <h2 className="text-4xl font-bold text-slate-900 text-center mb-12 text-balance">
              The Kelly Criterion Advantage
            </h2>
            <div className="grid md:grid-cols-3 gap-12">
              <div className="text-center group">
                <div className="w-20 h-20 bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-purple-900/25 group-hover:scale-105 transition-transform duration-300">
                  <svg
                    className="w-10 h-10 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Mathematical precision"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Optimal Sizing</h3>
                <p className="text-lg text-slate-600 leading-relaxed">
                  Mathematically determines the ideal position size for each investment to maximize long-term growth and
                  wealth accumulation
                </p>
              </div>

              <div className="text-center group">
                <div className="w-20 h-20 bg-gradient-to-br from-amber-600 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-amber-900/25 group-hover:scale-105 transition-transform duration-300">
                  <svg
                    className="w-10 h-10 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Risk management"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Risk Control</h3>
                <p className="text-lg text-slate-600 leading-relaxed">
                  Prevents dangerous over-leveraging and ruin risk while maintaining aggressive growth potential for
                  optimal returns
                </p>
              </div>

              <div className="text-center group">
                <div className="w-20 h-20 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-cyan-900/25 group-hover:scale-105 transition-transform duration-300">
                  <svg
                    className="w-10 h-10 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Adaptive strategy"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Dynamic Adaptation</h3>
                <p className="text-lg text-slate-600 leading-relaxed">
                  Automatically adjusts allocations as market conditions and asset characteristics change over time
                </p>
              </div>
            </div>
          </div>

          <div className="text-center">
            <h2 className="text-4xl font-bold text-slate-900 mb-6 text-balance">Ready to optimize your portfolio?</h2>
            <p className="text-xl text-slate-600 mb-12 max-w-3xl mx-auto text-balance">
              Start building a mathematically optimized portfolio that balances aggressive growth with prudent risk
              management.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <a href="/calculator" className="btn-primary text-lg group">
                Try the Calculator
                <svg
                  className="w-5 h-5 ml-3 inline group-hover:translate-x-1 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Arrow right"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </a>
              <a href="/articles" className="btn-secondary text-lg">
                Read Articles
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
