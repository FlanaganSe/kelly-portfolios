import { Link } from "wouter";
import { Icon } from "~/components/Icon";

export default function Home() {
  return (
    <div className="hero-gradient">
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-24 animate-fade-up">
          <div className="mb-8">
            <span className="inline-flex items-center px-4 py-2 bg-blue-50 text-blue-700 text-sm font-medium rounded-full border border-blue-200">
              <Icon name="check" size={4} className="mr-2" aria-label="Checkmark icon" />
              Mathematical Portfolio Optimization
            </span>
          </div>
          <h1 className="text-6xl md:text-8xl font-bold gradient-text mb-8 leading-tight text-balance">
            Portfolio Optimizer
          </h1>
          <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-light text-balance">
            Mathematical portfolio optimization using the Kelly Criterion for optimal risk-adjusted returns.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-20 animate-fade-up-delay">
          <div className="card card-hover p-10">
            <div className="flex items-start mb-8 gap-6">
              <div className="icon-gradient min-w-12 h-12">
                <Icon name="chart" size={8} className="text-white" aria-label="Bar chart icon" />
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
                <Icon name="portfolio" size={8} className="text-white" aria-label="Line chart icon" />
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
                <Icon
                  name="arrow"
                  size={5}
                  className="ml-3 inline group-hover:translate-x-1 transition-transform"
                  aria-label="Arrow icon"
                />
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
              <Icon name="calendar" size={10} className="text-white" aria-label="Calendar icon" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-4">Mathematical Precision</h3>
            <p className="text-lg text-slate-600 leading-relaxed">
              Data-driven portfolio allocation based on proven quantitative finance principles and decades of research
            </p>
          </div>

          <div className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-amber-600 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-amber-900/25 group-hover:scale-105 transition-transform duration-300">
              <Icon name="lock" size={10} className="text-white" aria-label="Lock icon" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-4">Risk Management</h3>
            <p className="text-lg text-slate-600 leading-relaxed">
              Intelligent position sizing that protects capital while maintaining optimal growth potential
            </p>
          </div>

          <div className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-cyan-900/25 group-hover:scale-105 transition-transform duration-300">
              <Icon name="trend" size={10} className="text-white" aria-label="Chart with arrow icon" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-4">Long-term Growth</h3>
            <p className="text-lg text-slate-600 leading-relaxed">
              Strategies optimized for sustained wealth building over extended investment horizons
            </p>
          </div>
        </div>

        <div className="mt-24 card p-12 text-center">
          <h2 className="text-4xl font-bold text-slate-900 mb-6 text-balance">Ready to Optimize Your Portfolio?</h2>
          <p className="text-xl text-slate-600 mb-8 max-w-3xl mx-auto text-balance">
            Start building your mathematically optimized portfolio in minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/calculator">
              <button type="button" className="btn-primary text-lg group">
                Get Started Free
                <Icon
                  name="arrow"
                  size={5}
                  className="ml-3 inline group-hover:translate-x-1 transition-transform"
                  aria-label="Arrow icon"
                />
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
