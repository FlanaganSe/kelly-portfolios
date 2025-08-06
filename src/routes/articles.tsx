import { Icon } from "~/components/Icon";

export default function Articles() {
  const articles = [
    {
      title: "Understanding the Kelly Criterion",
      excerpt:
        "Deep dive into the mathematical foundation of optimal position sizing and how it applies to portfolio management.",
      readTime: "8 min read",
      category: "Theory",
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      title: "Modern Portfolio Theory in Practice",
      excerpt:
        "How Markowitz's Nobel Prize-winning framework helps construct efficient portfolios that maximize return for given risk.",
      readTime: "12 min read",
      category: "Strategy",
      gradient: "from-emerald-500 to-green-500",
    },
    {
      title: "Risk Parity vs Traditional Allocation",
      excerpt:
        "Comparing equal-weight, market-cap, and risk-adjusted allocation strategies for long-term wealth building.",
      readTime: "10 min read",
      category: "Analysis",
      gradient: "from-purple-500 to-pink-500",
    },
    {
      title: "Behavioral Finance and Systematic Investing",
      excerpt: "Why mathematical approaches help overcome cognitive biases that lead to poor investment decisions.",
      readTime: "15 min read",
      category: "Psychology",
      gradient: "from-amber-500 to-orange-500",
    },
    {
      title: "Rebalancing Strategies and Tax Efficiency",
      excerpt: "Optimal rebalancing frequencies and tax-aware portfolio management for after-tax return maximization.",
      readTime: "9 min read",
      category: "Implementation",
      gradient: "from-cyan-500 to-blue-500",
    },
    {
      title: "Monte Carlo Simulation for Portfolio Planning",
      excerpt: "Using probabilistic modeling to stress-test portfolio performance across different market scenarios.",
      readTime: "11 min read",
      category: "Modeling",
      gradient: "from-indigo-500 to-purple-500",
    },
  ];

  return (
    <div className="hero-gradient min-h-screen">
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-20">
          <h1 className="text-5xl md:text-7xl font-bold gradient-text mb-8 text-balance">Investment Articles</h1>
          <p className="text-xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-light text-balance">
            In-depth analysis and practical guides for evidence-based portfolio optimization and quantitative investing
            strategies
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          {articles.map((article) => (
            <article key={article.title} className="card card-hover p-8 group cursor-pointer">
              <div className="flex items-center mb-6">
                <div
                  className={`w-16 h-16 bg-gradient-to-br ${article.gradient} rounded-xl flex items-center justify-center mr-4 shadow-lg`}
                >
                  <Icon name="book" size={8} className="text-white" aria-label="Article icon" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-500">{article.category}</div>
                  <div className="text-sm text-slate-400">{article.readTime}</div>
                </div>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4 group-hover:text-blue-600 transition-colors text-balance">
                {article.title}
              </h2>
              <p className="text-lg text-slate-600 leading-relaxed mb-6">{article.excerpt}</p>
              <div className="flex items-center text-blue-600 group-hover:text-blue-700 transition-all">
                <span className="font-semibold">Read Article</span>
                <Icon
                  name="arrow-right"
                  size={5}
                  className="ml-2 transform group-hover:translate-x-1 transition-transform"
                  aria-label="Arrow right"
                />
              </div>
            </article>
          ))}
        </div>

        <div className="card p-16 text-center">
          <h2 className="text-4xl font-bold text-slate-900 mb-6 text-balance">Want to contribute?</h2>
          <p className="text-xl text-slate-600 mb-12 max-w-3xl mx-auto text-balance">
            Have insights on portfolio optimization, quantitative finance, or risk management? We'd love to feature your
            expertise in our growing library of educational content.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="https://github.com/FlanaganSe/investing-portfolio"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-lg group"
            >
              <Icon name="github" size={6} className="mr-3" aria-label="GitHub" />
              Submit via GitHub
            </a>
            <button type="button" className="btn-secondary text-lg">
              <Icon name="email" size={6} className="mr-3" aria-label="Email" />
              Contact Us
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
