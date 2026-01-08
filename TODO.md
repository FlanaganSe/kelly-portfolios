# Portfolio Optimizer V2 - Future Development Roadmap

This document outlines the prioritized development tasks for the Portfolio Optimizer V2 application after the initial MVP implementation.

## Completed in MVP

- [x] Mean-Variance Optimization engine with custom QP solver
- [x] Client-side computation via Web Workers
- [x] CAPM-based expected returns with configurable market return
- [x] Covariance matrix calculation from price history
- [x] 10 asset universe with realistic mock data (104 weeks)
- [x] Stress test scenarios (2008, 2020, COVID, Dot-Com, Black Monday)
- [x] Efficient frontier visualization
- [x] Mobile-responsive layout with slide-out sidebar
- [x] localStorage persistence for configuration
- [x] Quick preset portfolios (Balanced, Aggressive, Conservative)
- [x] User-overridable expected returns per asset
- [x] Configurable leverage with margin cost modeling
- [x] Glassmorphism UI with dark theme

---

## Priority 1: Production Readiness

These are blocking issues that must be addressed before production deployment.

### Real Data Integration
- [ ] Implement real API data service (AlphaVantage, Yahoo Finance, or FMP)
- [ ] Add API key management via environment variables
- [ ] Implement rate limiting and caching for API calls
- [ ] Add fallback to mock data when API unavailable
- [ ] Handle partial data (some tickers unavailable)

### Error Handling & Robustness
- [ ] Add error boundaries around Chart.js components
- [ ] Add retry logic for failed API requests
- [ ] Add validation for user inputs (negative rates, etc.)
- [ ] Handle edge cases in optimizer (singular covariance matrix)
- [ ] Add network offline detection and graceful degradation

### Testing
- [ ] Unit tests for core math functions (statistics.ts)
- [ ] Unit tests for QP solver (optimizer.ts)
- [ ] Integration tests for optimization pipeline
- [ ] E2E tests for critical user flows
- [ ] Test coverage for edge cases (2 assets, 10 assets, high leverage)

### Performance
- [ ] Profile and optimize covariance matrix calculation
- [ ] Add debouncing to slider inputs
- [ ] Optimize efficient frontier generation (parallel computation)
- [ ] Add lazy loading for Chart.js

---

## Priority 2: User Experience Enhancements

### Portfolio Management
- [ ] Export portfolio to CSV/JSON
- [ ] Share portfolio via URL parameters
- [ ] Import portfolio from CSV/JSON
- [ ] Portfolio naming and multiple saved portfolios
- [ ] Undo/redo for configuration changes

### Visualization
- [ ] Historical backtest chart (how would this portfolio have performed)
- [ ] Correlation matrix heatmap visualization
- [ ] Asset contribution to portfolio risk
- [ ] Drawdown analysis chart
- [ ] Interactive efficient frontier (click to set risk level)

### Onboarding
- [ ] First-time user tutorial/walkthrough
- [ ] Tooltips explaining financial terms
- [ ] Help modal with documentation
- [ ] Example portfolios with explanations

### Accessibility
- [ ] Full keyboard navigation support
- [ ] Screen reader optimization
- [ ] High contrast mode
- [ ] Reduced motion preference support

---

## Priority 3: Feature Expansion

### Asset Universe
- [ ] Add more ETFs (sector, international, factor)
- [ ] Add individual stocks support
- [ ] Custom asset addition (ticker search)
- [ ] Asset categories filtering in search
- [ ] Asset comparison view

### Advanced Optimization
- [ ] Short-selling support (negative weights)
- [ ] Minimum/maximum weight constraints per asset
- [ ] Sector exposure constraints
- [ ] Target volatility optimization mode
- [ ] Maximum Sharpe ratio optimization mode
- [ ] Black-Litterman model integration

### Risk Analysis
- [ ] Value at Risk (VaR) calculation
- [ ] Conditional VaR (CVaR)
- [ ] Custom stress scenario builder
- [ ] Monte Carlo simulation for returns distribution
- [ ] Rolling window backtest

### Costs & Taxes
- [ ] Transaction cost modeling
- [ ] Tax-loss harvesting suggestions
- [ ] Dividend yield display
- [ ] Expense ratio impact calculation

---

## Priority 4: Infrastructure & DevOps

### Deployment
- [ ] Complete SST configuration for AWS deployment
- [ ] Add CloudFront CDN distribution
- [ ] Configure custom domain
- [ ] Add staging environment
- [ ] Implement blue/green deployments

### Monitoring
- [ ] Add error tracking (Sentry)
- [ ] Add analytics (privacy-respecting)
- [ ] Performance monitoring (Web Vitals)
- [ ] Uptime monitoring

### Security
- [ ] Content Security Policy headers
- [ ] Regular dependency updates
- [ ] Security audit of client-side data handling

---

## Priority 5: Future Vision (Post v1.0)

These are longer-term features that would significantly enhance the product.

### User Accounts
- [ ] User authentication (OAuth/magic link)
- [ ] Cloud-synced portfolios
- [ ] Portfolio sharing between users
- [ ] Collaboration features

### Real-Time Features
- [ ] WebSocket price updates
- [ ] Push notifications for rebalancing triggers
- [ ] Price alerts

### Advanced Analytics
- [ ] Factor analysis (Fama-French 3/5 factor)
- [ ] Regime-switching covariance matrices
- [ ] Machine learning return predictions
- [ ] Sentiment analysis integration

### Mobile
- [ ] PWA with offline support
- [ ] Native mobile app (React Native or Capacitor)
- [ ] Widget for quick portfolio check

---

## Technical Debt

Items to address for code quality:

- [ ] Replace non-null assertions with proper null checks
- [ ] Add comprehensive JSDoc comments to math functions
- [ ] Create shared types for Chart.js configuration
- [ ] Extract magic numbers to named constants
- [ ] Add biome configuration to CI pipeline

---

## Notes

- **Data Source Decision**: The mock data is designed to be replaced by a real API. The `DataService` interface in `src/data/api.ts` allows for swapping implementations without changing consumer code.

- **Solver Choice**: The current custom projected gradient descent solver works well for <20 assets. For larger portfolios, consider integrating OSQP.js (WASM-based QP solver).

- **Privacy First**: All computation remains client-side. Any future features should maintain this principle unless users explicitly opt into cloud features.
