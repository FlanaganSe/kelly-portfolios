# Portfolio Optimization Platform - Product Overview

## Vision

Build a production-ready web application that empowers individual investors to optimize their portfolios using the Kelly Criterion and advanced quantitative finance techniques, previously accessible only to institutional investors.

## Problem Statement

Individual investors face several challenges when building investment portfolios:

1. **Information Overload**: Manually tracking volatility, returns, and correlations across hundreds of ETFs is impossible
2. **Lack of Tools**: Professional portfolio optimization tools are expensive and complex
3. **Static Data**: Existing calculators use outdated or manually-entered data
4. **Missing Risk Assessment**: Most tools ignore black swan events and tail risk
5. **No Historical Context**: Difficult to understand how current volatility compares to historical patterns

## Solution

A modern web application that:
- **Automatically tracks** 100+ popular ETFs with daily data updates
- **Provides real-time volatility** calculations from market data
- **Calculates optimal allocations** using the Kelly Criterion
- **Models black swan events** to stress-test portfolios
- **Visualizes correlations** between assets
- **Offers historical context** for informed decision-making

---

## User Stories

### Primary User: Individual Investor (Retail Trader)

**Story 1: Finding Assets to Include**
```
As an investor, I want to search and discover ETFs by category
so that I can build a diversified portfolio without manual research.

Acceptance Criteria:
- I can search by symbol (e.g., "SPY") or name (e.g., "S&P 500")
- Results show current volatility and expected returns
- I can filter by category (Large Cap, Bonds, International, etc.)
- Search responds in under 500ms
```

**Story 2: Understanding Current Risk Levels**
```
As an investor, I want to see how volatile an asset is right now
compared to its historical average,
so that I can assess whether it's a good time to invest.

Acceptance Criteria:
- I see a chart showing 30-day volatility trends
- Current volatility is highlighted
- Historical average is shown for comparison
- I can switch between 7-day, 30-day, 90-day, and 1-year views
```

**Story 3: Optimizing Portfolio Allocation**
```
As an investor, I want to calculate the optimal allocation across
my selected assets using the Kelly Criterion,
so that I maximize long-term growth while managing risk.

Acceptance Criteria:
- I can add multiple assets to my portfolio (3-50 assets)
- System calculates correlation matrix automatically
- Results show percentage allocation for each asset
- I see portfolio-level metrics: expected return, risk, Sharpe ratio
- Calculation completes in under 3 seconds
```

**Story 4: Stress-Testing for Black Swan Events**
```
As an investor, I want to see how my portfolio would perform
during extreme market events (black swan scenarios),
so that I can understand and prepare for worst-case outcomes.

Acceptance Criteria:
- I can toggle "Black Swan Mode" on/off
- I can adjust severity (1x to 5x stress test)
- Side-by-side comparison shows normal vs. black swan allocations
- I see worst-case drawdown scenarios
- Results explain what "black swan" means in plain language
```

### Secondary User: Platform Administrator

**Story 5: Managing Asset Data**
```
As an admin, I want to manually update asset metadata
when I identify data quality issues,
so that users always have accurate information.

Acceptance Criteria:
- I can authenticate with an API key
- I can update individual asset properties
- I can bulk upload data via JSON
- Changes are reflected immediately
- Audit log tracks all admin actions
```

**Story 6: Monitoring Data Ingestion**
```
As an admin, I want to monitor the daily data ingestion process
and receive alerts when it fails,
so that I can maintain data freshness.

Acceptance Criteria:
- Dashboard shows last successful ingestion time
- Failed ingestions trigger email alerts
- I can manually trigger ingestion for specific assets
- I can see queue status and progress
```

---

## Key Features

### 1. Real-Time Asset Discovery

**What It Does:**
Users can search through 100+ popular ETFs across multiple categories (Large Cap, Technology, Bonds, Commodities, International, etc.). Each asset displays:
- Current 30-day implied volatility
- Historical volatility trends
- Expected annual return
- Sharpe ratio (risk-adjusted return)
- Last updated timestamp

**Why It Matters:**
Eliminates hours of manual research. Users can instantly find suitable assets for their investment strategy without visiting multiple financial websites.

**Technical Implementation:**
- DynamoDB stores asset metadata with sub-second query times
- API Gateway provides fast, scalable access
- Client-side search is instant with autocomplete

### 2. Automated Volatility Tracking

**What It Does:**
Daily updates pull the latest market data to calculate:
- 7-day, 30-day, 90-day, and 1-year historical volatility
- Current 30-day implied volatility from options markets
- Comparison to long-term historical averages
- VIX correlation (market-wide fear gauge)

**Why It Matters:**
Volatility is the most critical input for portfolio optimization. Fresh data ensures allocations reflect current market conditions, not stale historical averages.

**Technical Implementation:**
- Scheduled daily job at 6 PM ET (after market close)
- Polygon.io API integration for market data
- Rate-limited to 5 API calls/minute (free tier)
- Amazon Timestream stores 5+ years of historical data

### 3. Kelly Criterion Portfolio Optimization

**What It Does:**
Given a set of assets, the system calculates the mathematically optimal allocation that maximizes long-term growth while accounting for:
- Expected returns for each asset
- Volatility (risk) of each asset
- Correlations between assets
- User's risk tolerance (risk aversion parameter)

**Why It Matters:**
The Kelly Criterion is a proven mathematical formula used by legendary investors like Warren Buffett. It finds the "sweet spot" between aggressive growth and prudent risk management.

**Technical Implementation:**
- Can be calculated client-side for instant results
- Or server-side for complex portfolios (10+ assets)
- Uses gradient descent optimization algorithm
- Handles constraints (e.g., no short selling, position limits)

### 4. Correlation Matrix Visualization

**What It Does:**
Displays a heatmap showing how each asset moves relative to others:
- **Blue (positive)**: Assets move together (e.g., SPY and QQQ both track US stocks)
- **Red (negative)**: Assets move opposite (e.g., stocks and bonds)
- **White (zero)**: No correlation

Users can click any asset to highlight its correlations with all others.

**Why It Matters:**
Diversification is key to risk management. Understanding correlations helps investors build portfolios where losses in one asset are offset by gains in another.

**Technical Implementation:**
- Calculates from historical price data in Timestream
- Supports multiple lookback periods (30d, 90d, 1y, 5y)
- Interactive chart built with D3.js or similar
- Export to CSV for further analysis

### 5. Black Swan Risk Modeling

**What It Does:**
Simulates extreme market events (like 2008 financial crisis or 2020 COVID crash) and shows:
- How allocations change to protect against tail risk
- Maximum expected drawdown in worst-case scenarios
- Portfolio value at various confidence levels (95%, 99%, 99.9%)
- Comparison between "normal" and "black swan-adjusted" portfolios

**Why It Matters:**
Markets occasionally experience events that are 3-5 standard deviations from normal. Traditional models ignore these, leading to catastrophic losses. Black swan modeling prepares investors for the unexpected.

**Technical Implementation:**
- Tail risk factors stored per asset in DynamoDB
- Stress-tests portfolio by multiplying volatility by 1x-5x
- Calculates Value at Risk (VaR) and Conditional VaR (CVaR)
- Client can toggle between normal and stress-tested views

### 6. Historical Context & Trends

**What It Does:**
For any asset, users can see:
- Volatility over time (chart showing 6-12 months)
- How current volatility compares to historical percentiles
- Periods of high/low volatility highlighted
- Major market events annotated on timeline

**Why It Matters:**
Context is crucial for decision-making. Knowing that current volatility is at the 90th percentile suggests caution, while 10th percentile might indicate opportunity.

**Technical Implementation:**
- Timestream provides fast queries for time-series data
- Frontend charting library (Chart.js or Recharts)
- Annotations from market event database
- Responsive design for mobile viewing

---

## Success Metrics

### User Engagement
- **Active Users**: 1,000+ monthly active users within 6 months
- **Session Duration**: Average 5+ minutes per session
- **Return Rate**: 40%+ of users return within 7 days
- **Portfolio Calculations**: 10,000+ optimizations per month

### Data Quality
- **Data Freshness**: 95%+ of assets updated daily
- **Data Accuracy**: < 0.1% error rate vs. source data
- **Uptime**: 99.9% API availability

### Performance
- **API Response Time**: P95 < 2 seconds
- **Page Load Time**: < 3 seconds on 4G connection
- **Search Response**: < 500ms

### Business
- **Cost per User**: < $0.10 per active user per month
- **Total Infrastructure Cost**: < $200/month for 1,000 users
- **Data Ingestion Success**: 99%+ of daily jobs complete

---

## User Workflows

### Workflow 1: Building a Portfolio from Scratch

```
1. User visits calculator page
   └─ Clean interface with empty portfolio

2. User clicks "Add Asset" or uses search box
   └─ Types "tech" to find technology ETFs

3. Search returns results:
   - QQQ (Nasdaq-100, 0.22 volatility, 12% return)
   - XLK (Technology Sector, 0.25 volatility, 11% return)
   - VGT (Tech ETF, 0.23 volatility, 11.5% return)

4. User clicks QQQ → Added to portfolio
   └─ Card appears showing QQQ details

5. User repeats for TLT (bonds) and GLD (gold)

6. User clicks "Optimize" button
   └─ Loading indicator (1-2 seconds)

7. Results appear:
   - QQQ: 55% allocation
   - TLT: 35% allocation
   - GLD: 10% allocation
   - Portfolio Expected Return: 8.5%
   - Portfolio Volatility: 14.2%
   - Sharpe Ratio: 0.52

8. User toggles "Black Swan Mode"
   └─ New allocations appear:
   - QQQ: 40% (reduced)
   - TLT: 45% (increased - safer)
   - GLD: 15% (increased - hedge)

9. User satisfied, bookmarks page or exports results
```

### Workflow 2: Researching an Asset

```
1. User heard about "SPY" from friend

2. User navigates to /assets/SPY
   └─ Detailed asset page loads

3. User sees:
   - Name: SPDR S&P 500 ETF Trust
   - Current 30-day volatility: 18%
   - Historical average: 16%
   - Expected return: 10% annually
   - Sharpe ratio: 0.85

4. User scrolls to volatility chart
   └─ Line chart shows last 6 months
   └─ Sees spike in August (market selloff)

5. User switches to "1 Year" view
   └─ Chart extends, shows longer trends

6. User sees current volatility is above average
   └─ Decides to wait for volatility to decrease

7. User adds SPY to watchlist (future feature)
```

### Workflow 3: Admin Data Update

```
1. Admin notices volatility data for SPY is stale

2. Admin authenticates with API key

3. Admin navigates to /admin/data/upload

4. Admin prepares JSON file:
   {
     "type": "VOLATILITY",
     "data": [{
       "symbol": "SPY",
       "date": "2025-10-13",
       "impliedVol30Day": 0.18,
       "historicalVol": 0.16
     }],
     "overwrite": true
   }

5. Admin uploads file
   └─ System validates format
   └─ System writes to DynamoDB
   └─ Success message appears

6. Admin verifies on public site
   └─ SPY volatility now shows latest data
```

---

## Competitive Analysis

### Competitor 1: Portfolio Visualizer
**Strengths:**
- Extensive historical data
- Many portfolio optimization methods
- Backtesting capabilities

**Weaknesses:**
- Complex interface, steep learning curve
- Requires manual data entry for most features
- No real-time data
- Paid subscription for advanced features

**Our Advantage:**
- Simpler, focused on Kelly Criterion
- Automatic data updates
- Free tier with real-time data
- Modern, intuitive UI

### Competitor 2: Thinkorswim / Trader Workstation
**Strengths:**
- Professional-grade tools
- Real-time data
- Advanced charting

**Weaknesses:**
- Overwhelming for retail investors
- Requires brokerage account
- No Kelly Criterion optimization
- Not web-based (desktop apps only)

**Our Advantage:**
- Web-based, accessible anywhere
- Focused on portfolio optimization
- No account required
- Educational approach

### Competitor 3: Custom Excel Spreadsheets
**Strengths:**
- Free
- Fully customizable
- Familiar to many users

**Weaknesses:**
- Manual data entry
- Prone to errors
- No automation
- Doesn't scale

**Our Advantage:**
- Automated data updates
- No manual work
- Professional calculations
- Scalable to many assets

---

## Roadmap

### Phase 1: MVP (Months 1-2)
- ✅ 100 ETFs with daily data updates
- ✅ Basic Kelly Criterion calculator
- ✅ Asset search and discovery
- ✅ Volatility charts
- ✅ Admin data management

**Launch Criteria:**
- All 100 ETFs tracked daily
- API response time < 2 seconds
- Calculator handles 3-10 asset portfolios
- Zero critical bugs

### Phase 2: Enhanced Features (Months 3-4)
- 🔄 Black swan risk modeling
- 🔄 Correlation matrix visualization
- 🔄 Enhanced portfolio metrics (VaR, CVaR, etc.)
- 🔄 Export functionality (PDF reports, CSV)
- 🔄 Mobile-responsive design improvements

**Launch Criteria:**
- Black swan calculations accurate
- Charts render smoothly on mobile
- User feedback score > 4.0/5.0

### Phase 3: Growth (Months 5-6)
- 🔜 Expand to 200+ assets (stocks, commodities, crypto)
- 🔜 User accounts (save portfolios)
- 🔜 Portfolio watchlists with alerts
- 🔜 Historical backtesting
- 🔜 Social features (share portfolios)

**Launch Criteria:**
- 1,000+ monthly active users
- Database handles 200+ assets efficiently
- User retention > 40%

### Phase 4: Monetization (Months 6+)
- 🔜 Premium tier ($9.99/month):
  - Unlimited assets per portfolio
  - Advanced analytics
  - Priority data updates
  - Custom correlation periods
- 🔜 API access for developers
- 🔜 White-label solutions for financial advisors

**Launch Criteria:**
- 10%+ conversion to paid tier
- Premium features demonstrably valuable
- Customer support infrastructure ready

---

## Technical Architecture Overview

**Frontend:**
- SolidJS for reactive UI
- TailwindCSS for styling
- Hosted on AWS CloudFront + S3

**Backend:**
- AWS Lambda (serverless functions)
- API Gateway for REST API
- DynamoDB for metadata & current data
- Amazon Timestream for historical prices
- S3 for backups

**Data Ingestion:**
- EventBridge (cron scheduler)
- SQS queue for rate limiting
- Polygon.io API for market data
- Daily updates at 6 PM ET

**Monitoring:**
- CloudWatch Logs & Metrics
- Custom dashboards
- Automated alerts

**Cost Estimate:**
- Dev environment: ~$20/month
- Production (1,000 users): ~$100/month
- Production (10,000 users): ~$300/month

---

## Risk Assessment

### Technical Risks

**Risk: Polygon.io API Rate Limits**
- **Impact**: Data ingestion fails or slows down
- **Likelihood**: Medium (free tier has strict 5 calls/min limit)
- **Mitigation**:
  - SQS queue with rate limiting
  - Spread ingestion over multiple hours
  - Upgrade to paid tier if needed ($200/month for 500 calls/min)

**Risk: Cold Start Latency**
- **Impact**: Slow API responses (3-5 seconds)
- **Likelihood**: Medium (Lambda cold starts in Node.js)
- **Mitigation**:
  - Provisioned concurrency for critical endpoints
  - Keep functions warm with scheduled pings
  - Optimize bundle size

**Risk: Timestream Query Costs**
- **Impact**: Higher than expected costs for complex queries
- **Likelihood**: Low (queries are simple aggregations)
- **Mitigation**:
  - Cache frequent queries in DynamoDB
  - Limit query ranges to necessary periods
  - Monitor costs weekly

### Business Risks

**Risk: Low User Adoption**
- **Impact**: Effort doesn't provide value to users
- **Likelihood**: Low (clear market need)
- **Mitigation**:
  - Launch with educational content
  - Share on investing subreddits/forums
  - Gather user feedback early

**Risk: Data Quality Issues**
- **Impact**: Users lose trust in calculations
- **Likelihood**: Medium (external API dependency)
- **Mitigation**:
  - Cross-validate with multiple data sources
  - Display data quality indicators
  - Admin tools for manual corrections
  - Automated anomaly detection

### Legal/Compliance Risks

**Risk: Financial Advice Liability**
- **Impact**: Legal issues if users claim they followed bad advice
- **Likelihood**: Low (not providing personalized advice)
- **Mitigation**:
  - Clear disclaimers: "Not financial advice"
  - Educational framing: "Learn about portfolio optimization"
  - Terms of service reviewed by lawyer

---

## Open Questions

1. **Should we support individual stocks?**
   - Pro: More flexibility for users
   - Con: Thousands more assets to track, higher costs
   - **Decision**: Start with ETFs only, add stocks in Phase 3

2. **Should calculations be client-side or server-side?**
   - Client-side: Faster, free, works offline
   - Server-side: More accurate, can use latest data, easier to update
   - **Decision**: Hybrid - client-side for simple, server-side for complex

3. **How to handle international users?**
   - Current focus: US ETFs only
   - Future: Add European, Asian ETFs
   - **Decision**: US-only for MVP, gather demand for international

4. **What about options and futures?**
   - Complex instruments require different models
   - **Decision**: Out of scope for MVP, possible future feature

5. **Should we show intraday data?**
   - Real-time data is expensive
   - **Decision**: Daily updates only for MVP, real-time in paid tier

---

## Appendix: Financial Concepts Explained

### Kelly Criterion
Formula for optimal position sizing that maximizes long-term growth. Balances expected returns against risk of loss.

**Example:** If an asset has a 60% chance of +10% return and 40% chance of -5% return, Kelly Criterion calculates the optimal percentage of your portfolio to allocate.

### Volatility
Measure of how much an asset's price fluctuates. Higher volatility = higher risk but potentially higher returns.

**Example:** An asset with 20% volatility typically moves up or down 20% per year (with ~68% confidence).

### Correlation
How two assets move together. +1 = perfectly together, -1 = perfectly opposite, 0 = independent.

**Example:** Stocks and bonds often have negative correlation (when stocks fall, bonds rise), providing diversification.

### Sharpe Ratio
Risk-adjusted return metric. Higher is better. Measures excess return per unit of risk.

**Example:** Two assets both return 10%, but one has 20% volatility and one has 10%. The second has a better Sharpe ratio (less risk for same return).

### Black Swan
Rare, unpredictable event with extreme impact. Named after the discovery of black swans in Australia (Europeans thought all swans were white).

**Examples:** 2008 financial crisis, 2020 COVID crash, 9/11 attacks

### VaR (Value at Risk)
Worst expected loss at a given confidence level over a time period.

**Example:** "There's a 95% chance we won't lose more than $10,000 this year" means VaR(95%) = $10,000.

---

## Document Information

**Version:** 1.0.0
**Last Updated:** October 13, 2025
**Document Owner:** Product Manager
**Stakeholders:** Engineering, Design, Marketing, Legal
**Status:** Approved for Implementation

**Next Review Date:** November 13, 2025 (after Phase 1 completion)
