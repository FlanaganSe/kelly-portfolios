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
    <div className="container mx-auto px-6 py-16">
      <div className="text-center mb-16">
        <h1 className="text-4xl md:text-6xl font-bold gradient-text mb-6">Investment Articles</h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed font-light">
          In-depth analysis and practical guides for evidence-based portfolio optimization and quantitative investing
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
        {articles.map((article) => (
          <article key={article.title} className="card card-hover rounded-2xl p-6 group cursor-pointer">
            <div className="flex items-center mb-4">
              <div
                className={`w-12 h-12 bg-gradient-to-r ${article.gradient} rounded-xl flex items-center justify-center mr-4`}
              >
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Article icon"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
              </div>
              <div>
                <div className="text-sm text-gray-500">{article.category}</div>
                <div className="text-sm text-gray-400">{article.readTime}</div>
              </div>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-3 group-hover:text-blue-600 transition-colors">
              {article.title}
            </h2>
            <p className="text-gray-600 leading-relaxed mb-4">{article.excerpt}</p>
            <div className="flex items-center text-blue-600 group-hover:text-blue-700 transition-colors">
              <span className="text-sm font-medium">Read Article</span>
              <svg
                className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                role="img"
                aria-label="Arrow right"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </article>
        ))}
      </div>

      <div className="card rounded-2xl p-12 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Want to contribute?</h2>
        <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
          Have insights on portfolio optimization, quantitative finance, or risk management? We'd love to feature your
          expertise in our growing library of educational content.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="https://github.com/FlanaganSe/investing-portfolio"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 btn-primary"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" role="img" aria-label="GitHub">
              <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
            </svg>
            Submit via GitHub
          </a>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 px-6 rounded-lg transition-all duration-200"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              role="img"
              aria-label="Email"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            Contact Us
          </button>
        </div>
      </div>
    </div>
  );
}
