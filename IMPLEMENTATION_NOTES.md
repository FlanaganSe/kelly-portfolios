# Portfolio Optimizer V2 - Implementation Notes

## Overview

This document captures implementation decisions, deviations from the PRD, and areas for future improvement.

## Mathematical Implementation

### QP Solver Choice

The PRD specified using `javascript-lp-solver` for Quadratic Programming. However, `javascript-lp-solver` is primarily a **Linear Programming** solver and does not natively support true quadratic objectives.

**Solution implemented:** Instead of `javascript-lp-solver`, we implemented a custom **Projected Gradient Descent** optimizer with momentum. This approach:

1. Directly optimizes the Mean-Variance utility function: `U = w^T * mu_net - (gamma/2) * w^T * Sigma * w`
2. Handles all constraints (non-negativity, min investment, max leverage) via projection
3. Converges reliably for portfolios with <20 assets as specified

**Alternative for future:** Consider using `osqp.js` (WASM-based) for a true QP solver if more robustness is needed.

### Leverage Cost Formulation

The leverage cost is modeled as specified in the PRD:
- Returns are adjusted: `q_i = E[R_i] - R_borrow`
- Any portfolio weight sum above 1.0 incurs the borrow rate

### CAPM Expected Returns

Expected returns are calculated using the Capital Asset Pricing Model:
```
E[R_i] = R_riskfree + beta_i * (R_market - R_riskfree)
```

With default market return assumption of 10% (historical average).

## Data Layer

### Mock Data Generation

The mock data generator (`mockHistory.ts`) creates:
- 104 weeks (2 years) of price data
- Correlated returns using Cholesky decomposition
- Realistic asset characteristics based on historical patterns

**Note:** The correlation matrix and volatility estimates are approximations. For production, these should be derived from real market data.

### Assets Included

10 assets as specified:
- SPY, QQQ (Equity)
- TLT, HYG, LQD (Bonds)
- GLD (Commodity)
- VNQ (REIT)
- BTC, ETH (Crypto)
- CASH (Money Market)

## UI/UX Decisions

### Glassmorphism Styling

Implemented using custom CSS rather than Tailwind utilities due to Tailwind v4's changed syntax for `@layer` directives and component application.

### Charts

Using Chart.js with:
- Doughnut chart for allocation visualization
- Line/scatter chart for efficient frontier

## Areas for Future Improvement

### High Priority

1. **True QP Solver:** Replace gradient descent with `osqp.js` for guaranteed optimality
2. **Real Data Integration:** Add interface for AlphaVantage, Yahoo Finance, or FMP APIs
3. **LocalStorage Persistence:** Save portfolio configurations between sessions

### Medium Priority

4. **Stress Covariance Matrices:** During crisis scenarios, correlations often converge to 1. Consider implementing regime-switching covariance models
5. **Tax-Loss Harvesting:** Post-MVP feature for tax optimization
6. **More Asset Classes:** Add support for options, futures, and international equities

### Nice to Have

7. **Mobile Responsive Sidebar:** Currently optimized for desktop
8. **Portfolio Comparison:** Compare multiple portfolio configurations side-by-side
9. **Export Functionality:** Export optimization results to CSV/PDF

## Known Limitations

1. **No Real-Time Data:** Uses mock data only
2. **Browser Compatibility:** Web Workers require modern browser support
3. **Covariance Estimation:** Uses simple sample covariance; could be improved with shrinkage estimators
4. **No Short Selling:** Weights are constrained to be non-negative (long-only)

## Dependencies

Key dependencies added for this MVP:
- `simple-statistics`: Statistical calculations
- `chart.js`: Data visualization

Note: `javascript-lp-solver` was installed but not directly used (custom optimizer implemented instead).

## Testing the Application

1. Start the dev server: `npm run dev`
2. Open http://localhost:3000
3. Select 2+ assets from the sidebar
4. Adjust risk parameters
5. Click "Optimize Portfolio"
6. View allocation and efficient frontier
7. Test stress scenarios at the bottom

## Build Information

- Build target: ES2022
- Bundle includes web worker for optimization
- CSS processed via Tailwind v4
