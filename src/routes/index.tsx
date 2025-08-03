import { Link } from "wouter";

export default function Home() {
  return (
    <div className="container mx-auto px-6 py-12">
      <div className="text-center mb-16">
        <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent mb-6">
          Portfolio Optimizer
        </h1>
        <p className="text-xl md:text-2xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
          Harness the power of the Kelly Criterion to optimize your investment portfolio with mathematical precision
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-12 mb-16">
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8 hover:bg-slate-800/60 transition-all duration-300">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mr-4">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                role="img"
                aria-label="Chart icon"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white">Kelly Criterion</h2>
          </div>
          <p className="text-slate-300 leading-relaxed mb-4">
            The Kelly Criterion is a mathematical formula that determines the optimal allocation of capital to maximize
            long-term growth while minimizing risk of ruin.
          </p>
          <div className="bg-slate-900/50 rounded-lg p-4 font-mono text-sm text-cyan-300">f* = (bp - q) / b</div>
          <p className="text-slate-400 text-sm mt-2">
            Where f* is the fraction to bet, b is odds, p is probability of win, q is probability of loss
          </p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8 hover:bg-slate-800/60 transition-all duration-300">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-green-500 rounded-xl flex items-center justify-center mr-4">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                role="img"
                aria-label="Growth chart icon"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white">Optimal Growth</h2>
          </div>
          <p className="text-slate-300 leading-relaxed">
            By applying Kelly sizing to your portfolio, you can achieve maximum geometric growth while maintaining
            prudent risk management. This approach balances aggressive growth with capital preservation.
          </p>
          <ul className="mt-4 space-y-2 text-slate-300">
            <li className="flex items-center">
              <div className="w-2 h-2 bg-emerald-400 rounded-full mr-3"></div>
              Maximizes long-term wealth
            </li>
            <li className="flex items-center">
              <div className="w-2 h-2 bg-emerald-400 rounded-full mr-3"></div>
              Prevents over-leveraging
            </li>
            <li className="flex items-center">
              <div className="w-2 h-2 bg-emerald-400 rounded-full mr-3"></div>
              Adapts to market conditions
            </li>
          </ul>
        </div>
      </div>

      <div className="text-center">
        <Link href="/calculator">
          <button
            type="button"
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-bold py-4 px-8 rounded-xl text-lg transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-blue-500/25"
          >
            Start Optimizing Your Portfolio
            <svg
              className="w-5 h-5 ml-2 inline"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              role="img"
              aria-label="Arrow right"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </Link>
      </div>

      <div className="mt-20 grid md:grid-cols-3 gap-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              role="img"
              aria-label="Calculator icon"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Mathematical Precision</h3>
          <p className="text-slate-400">
            Data-driven approach to portfolio allocation based on proven mathematical principles
          </p>
        </div>

        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-amber-500 to-orange-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              role="img"
              aria-label="Security shield icon"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Risk Management</h3>
          <p className="text-slate-400">Intelligent position sizing that protects capital while maximizing returns</p>
        </div>

        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              role="img"
              aria-label="Growth trend icon"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Long-term Growth</h3>
          <p className="text-slate-400">Optimized for sustained wealth building over extended time horizons</p>
        </div>
      </div>
    </div>
  );
}
