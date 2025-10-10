import { A } from "@solidjs/router";
import type { Component } from "solid-js";
import { Icon } from "~/components/Icon";

const About: Component = () => {
  return (
    <div class="hero-gradient min-h-screen">
      <div class="container mx-auto px-6 py-20">
        <div class="max-w-5xl mx-auto">
          <div class="text-center mb-20">
            <h1 class="text-5xl md:text-7xl font-bold gradient-text mb-8 text-balance">About Portfolio Optimizer</h1>
            <p class="text-xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-light text-balance">
              Empowering investors with mathematical precision and evidence-based portfolio optimization strategies
              rooted in decades of quantitative finance research
            </p>
          </div>

          <div class="grid lg:grid-cols-2 gap-10 mb-20">
            <div class="card p-12">
              <div class="flex items-start mb-8 gap-6">
                <div class="icon-gradient w-12 h-12 min-w-12">
                  <Icon name="lightbulb" size={8} class="text-white" aria-label="Mission icon" />
                </div>
                <div>
                  <h2 class="text-3xl font-bold text-slate-900 mb-4">Our Mission</h2>
                  <p class="text-lg text-slate-600 leading-relaxed">
                    To democratize advanced portfolio optimization techniques by making mathematical finance accessible
                    to individual investors. We believe sophisticated risk management and return optimization should not
                    be exclusive to institutional investors.
                  </p>
                </div>
              </div>
            </div>

            <div class="card p-12">
              <div class="flex items-start mb-8 gap-6">
                <div class="bg-gradient-to-br from-emerald-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/25 min-w-12 h-12">
                  <Icon name="chart" size={8} class="text-white" aria-label="Approach icon" />
                </div>
                <div>
                  <h2 class="text-3xl font-bold text-slate-900 mb-4">Our Approach</h2>
                  <p class="text-lg text-slate-600 leading-relaxed">
                    We leverage proven mathematical frameworks including the Kelly Criterion, Modern Portfolio Theory,
                    and risk parity strategies. Our tools are built on decades of academic research and real-world
                    testing by quantitative finance professionals.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div class="card p-16 mb-20">
            <h2 class="text-4xl font-bold text-slate-900 text-center mb-12 text-balance">
              The Kelly Criterion Advantage
            </h2>
            <div class="grid md:grid-cols-3 gap-12">
              <div class="text-center group">
                <div class="w-20 h-20 bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-purple-900/25 group-hover:scale-105 transition-transform duration-300">
                  <Icon name="calendar" size={10} class="text-white" aria-label="Mathematical precision" />
                </div>
                <h3 class="text-2xl font-bold text-slate-900 mb-4">Optimal Sizing</h3>
                <p class="text-lg text-slate-600 leading-relaxed">
                  Mathematically determines the ideal position size for each investment to maximize long-term growth and
                  wealth accumulation
                </p>
              </div>

              <div class="text-center group">
                <div class="w-20 h-20 bg-gradient-to-br from-amber-600 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-amber-900/25 group-hover:scale-105 transition-transform duration-300">
                  <Icon name="lock" size={10} class="text-white" aria-label="Risk management" />
                </div>
                <h3 class="text-2xl font-bold text-slate-900 mb-4">Risk Control</h3>
                <p class="text-lg text-slate-600 leading-relaxed">
                  Prevents dangerous over-leveraging and ruin risk while maintaining aggressive growth potential for
                  optimal returns
                </p>
              </div>

              <div class="text-center group">
                <div class="w-20 h-20 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-cyan-900/25 group-hover:scale-105 transition-transform duration-300">
                  <Icon name="optimize" size={10} class="text-white" aria-label="Adaptive strategy" />
                </div>
                <h3 class="text-2xl font-bold text-slate-900 mb-4">Dynamic Adaptation</h3>
                <p class="text-lg text-slate-600 leading-relaxed">
                  Automatically adjusts allocations as market conditions and asset characteristics change over time
                </p>
              </div>
            </div>
          </div>

          <div class="text-center">
            <h2 class="text-4xl font-bold text-slate-900 mb-6 text-balance">Ready to optimize your portfolio?</h2>
            <p class="text-xl text-slate-600 mb-12 max-w-3xl mx-auto text-balance">
              Start building a mathematically optimized portfolio that balances aggressive growth with prudent risk
              management.
            </p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <A href="/calculator" class="btn-primary text-lg group">
                Try the Calculator
                <Icon
                  name="arrow"
                  size={5}
                  class="ml-3 inline group-hover:translate-x-1 transition-transform"
                  aria-label="Arrow right"
                />
              </A>
              <A href="/articles" class="btn-secondary text-lg">
                Read Articles
              </A>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;
