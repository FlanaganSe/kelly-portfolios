This is a comprehensive Product Requirements Document (PRD) designed to serve as the "Source of Truth" for an AI or engineering team to build the MVP of **Portfolio Optimizer V2**.

It addresses the architectural decisions we agreed upon: Client-side QP solver, Web Workers for performance, Damodaran-style estimates, and a "Short Cash" approach to leverage.


# *****Product Requirements Document: Portfolio Optimizer V2 (MVP)**

|                  |                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Project Name** | **Portfolio Optimizer V2 (Project "Alpha-Retail")**                                                                       |
| **Version**      | 2.0 (MVP Draft)                                                                                                           |
| **Status**       | Ready for Development                                                                                                     |
| **Tech Stack**   | SolidJS, Vite, TailwindCSS, TypeScript, Web Workers                                                                       |
| **Core Goal**    | Democratize hedge-fund quality **Mean-Variance Optimization** and **Risk Analysis** for retail investors with <20 assets. |


## *****1. Executive Summary**

The Portfolio Optimizer V2 is a high-performance, privacy-focused web application. Unlike typical portfolio trackers, this tool is **prescriptive**: it tells users _what they should hold_ based on mathematical optimization, not just what they currently hold.

It bridges the gap between "Gut Feeling" and "Quant Finance" by allowing users to optimize for **Growth (Kelly-aligned)** or **Stability (Sharpe-aligned)**, apply **Leverage** safely, and stress-test portfolios against historical **Black Swan** events (e.g., 2008 Crisis).


### **Key Differentiators**

1. **Client-Side Compute:** Zero latency. No backend required for math. Privacy-first (portfolio data never leaves the browser).

2. **Professional Math:** Uses Quadratic Programming (QP) solvers, not brittle iterative guessing.

3. **Realistic Leverage:** Models the _cost of borrowing_ (Margin Rates) to prevent "free lunch" leverage assumptions.


## *****2. User Flows & UX**

The application is a Single Page Application (SPA) designed as a "Financial Dashboard."


### **2.1 The "Optimizer" Loop (Primary Flow)**

1. **Asset Selection:** User searches and adds 3-10 tickers (e.g., SPY, TLT, GLD, BTC).

2. **Parameter Configuration:** User tweaks global settings:

- _Risk Aversion:_ Slider (Aggressive <-> Conservative).

- _Leverage Limit:_ Dropdown (1.0x to 3.0x).

- _Rates:_ Risk-Free Rate (e.g., 4.5%) and Borrow Rate (e.g., 6.0%).

3. **Refine Inputs (Optional):** User reviews the calculated "Expected Return" for each asset. If they disagree with the specific CAPM estimate, they override it manually.

4. **Visualize:** The main view updates in real-time (via Web Worker) to show:

- Optimal Weights (Donut Chart).

- Efficient Frontier Curve.

- Historical "Backtest" of this optimized allocation.


### **2.2 The "Stress Test" Flow (Secondary Flow)**

1. User clicks "Simulate Crash."

2. System applies historical returns from specific periods (2008, 2020) to the _current_ optimized weights.

3. Display: "In 2008, this portfolio would have drawn down **-22%** (vs SPY -55%)."


## *****3. Mathematical Specification (The "Engine")**

**Constraint:** The AI Developer must strictly follow this mathematical formulation to ensure convexity and solvency.


### **3.1 The Optimization Problem (Quadratic Programming)**

We solve for vector $\mathbf{w}$ (weights) to maximize Utility ($U$).

Objective Function:

\


$$\text{Maximize } U = \mathbf{w}^T \mathbf{\mu}\_{net} - \frac{\gamma}{2} \mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$$

Where:

- $\mathbf{w}$: Vector of asset weights (size $N$).

- $\mathbf{\Sigma}$: Covariance Matrix ($N \times N$).

- $\gamma$ (Gamma): Risk Aversion parameter (User input: 1.0 to 10.0).

- $\mathbf{\mu}\_{net}$: Net Expected Returns vector, adjusted for leverage costs.

Handling Leverage (The Linear Trick):

To keep this solvable by a standard QP solver without integer constraints, we define the return of the portfolio as:

\


$$R\_p = \sum (w\_i \cdot R\_i) - (\sum w\_i - 1) \cdot R\_{borrow}$$

(Meaning: Any allocation sum above 100% incurs the Borrow Rate).

Standard Form for QP Solvers (Minimize):

\


$$\text{Minimize } \frac{1}{2} \mathbf{w}^T (\gamma \mathbf{\Sigma}) \mathbf{w} - \mathbf{q}^T \mathbf{w}$$

Where linear vector $\mathbf{q}$ is:

\


$$q\_i = E\[R\_i] - R\_{borrow}$$

(Note: This assumes the portfolio is fully invested or leveraged. Cash is treated as "Unused Capacity" if $\sum w < 1$.)

**Constraints:**

1. $w\_i \ge 0$ (Long only for assets).

2. $\sum w\_i \ge 0.1$ (Must invest something).

3. $\sum w\_i \le \text{MaxLeverage}$ (e.g., 1.5).


### **3.2 Estimates & Inputs**

- Returns ($\mu$): CAPM Model.\
  \
  $$E\[R\_i] = R\_{riskfree} + \beta\_i \times (R\_{market} - R\_{riskfree})$$

- **Beta ($\beta$):** Calculated via client-side regression of Asset Weekly Returns vs. Benchmark (SPY) Weekly Returns over trailing 2 years.

- **Covariance ($\Sigma$):** Standard sample covariance of weekly logarithmic returns.


## *****4. Technical Architecture**

### **4.1 System Diagram**

Code snippet

\


graph TD\
    User\[User] --> UI\[SolidJS Frontend]\
    UI -->|1. Assets & Constraints| Worker\[Web Worker (Optimization Engine)]\
   \
    subgraph "Main Thread"\
        UI\
        Store\[Solid Store (State)]\
        Chart\[Chart.js / Vis]\
    end\
   \
    subgraph "Background Thread"\
        Worker -->|2. Compute Covariance| Math\[Math Lib (Matrix Ops)]\
        Worker -->|3. Solve QP| Solver\[OSQP.js / LP-Solver]\
        Solver -->|4. Optimal Weights| Worker\
    end\
   \
    Worker -->|5. Result Payload| UI\
   \
    subgraph "Data Layer"\
        UI -->|Fetch History| DataService\[Data Service Interface]\
        DataService -->|JSON| MockData\[Mock/Real API]\
    end


### **4.2 Stack & Libraries**

- **Framework:** SolidJS (signals for high-performance reactivity).

- **Bundler:** Vite.

- **Solver:** javascript-lp-solver (easier for pure JS) OR osqp.js (WASM, more robust). _Recommendation for MVP: javascript-lp-solver is sufficient for <20 assets._

- **Math:** mathjs or simple-statistics for covariance/matrix math.

- **Styling:** TailwindCSS.


### **4.3 Directory Structure**

Plaintext

\


/src\
  /assets           # Static assets\
  /components       # UI Components\
    /charts         # AllocationPie, EfficientFrontierChart\
    /controls       # AssetSearch, RiskSlider, LeverageInput\
    /layout         # DashboardLayout, Sidebar\
  /core             # Core Logic (Non-UI)\
    /math           # statistics.ts (Beta, Covariance), returns.ts (CAPM)\
    /solver         # optimizer.ts (The QP implementation)\
  /data             # Data fetching & Types\
    /mock           # mockAssets.ts, mockHistory.ts (CRITICAL for MVP)\
    api.ts          # Repository pattern for fetching data\
  /workers          # optimizer.worker.ts (Handles heavy compute)\
  App.tsx\
  index.tsx


## *****5. Data Models & Interfaces**

### **5.1 The Asset Entity**

TypeScript

\


interface Asset {\
  id: string;        // "SPY"\
  name: string;      // "SPDR S\&P 500 ETF"\
  category: string;  // "Equity" | "Bond" | "Commodity"\
  price: number;     // Current Price\
  metrics: {\
    volatility: number; // Annualized StdDev\
    beta: number;       // vs SPY\
    expectedReturn: number; // The CAPM estimate\
  }\
}


### **5.2 The User Configuration (State)**

TypeScript

\


interface PortfolioConfig {\
  assets: string\[];           // List of Tickers \["SPY", "TLT"]\
  riskFreeRate: number;       // e.g. 0.045\
  borrowRate: number;         // e.g. 0.065\
  riskAversion: number;       // 1.0 (Aggressive) to 10.0 (Conservative)\
  maxLeverage: number;        // 1.0 to 3.0\
  userReturnOverrides: Record\<string, number>; // { "BTC": 0.15 }\
}


### **5.3 The Optimizer Output**

TypeScript

\


interface OptimizationResult {\
  weights: Record\<string, number>; // { "SPY": 0.6, "TLT": 0.4 }\
  stats: {\
    portfolioReturn: number;\
    portfolioVolatility: number;\
    sharpeRatio: number;\
    totalLeverage: number;\
  }\
  efficientFrontier: { x: number, y: number }\[]; // Points for plotting\
}


## *****6. Development Phases (MVP)**

### **Phase 1: The "Skeleton" & Mock Data**

- **Goal:** Get the UI rendering with hardcoded data.

- **Action:** Create mockHistory.ts containing 2 years of weekly closes for \~10 tickers (SPY, QQQ, TLT, GLD, VNQ, BTC, ETH, HYG, LQD, CASH).

- **Action:** Build the DataService that simply returns this JSON with a 500ms delay (simulating network).


### **Phase 2: The Math Core (Worker)**

- **Goal:** Implement the math in a pure TypeScript environment.

- **Action:** Write statistics.ts to convert Price History -> Returns -> Covariance Matrix.

- **Action:** Write optimizer.ts using javascript-lp-solver. Formulate the QP model described in Section 3.1.

- **Test:** Ensure that setting Risk Aversion to "High" results in lower volatility assets (Bonds) being selected.


### **Phase 3: The UI Integration**

- **Goal:** Connect the UI sliders to the Worker.

- **Action:** Build the Sidebar (Inputs) and Main Dashboard (Donut Chart).

- **Action:** Implement the "Override" table where users can edit Expected Returns.


### **Phase 4: Scenario Analysis (Black Swan)**

- **Goal:** The "Crash Test" button.

- **Action:** Create a config file scenarios.ts:\
  TypeScript\
  export const SCENARIOS = \[\
    { name: "2008 Crash", impacts: { "SPY": -0.45, "TLT": 0.15, "GLD": 0.05, ... } },\
    { name: "2020 Covid", impacts: { "SPY": -0.33, "TLT": 0.08, "GLD": -0.02, ... } }\
  ]

- **Action:** When user clicks "Simulate", apply weights to these impact factors and show the weighted sum.


## *****7. Open Questions & Future Considerations (Post-MVP)**

The following items are **Out of Scope** for MVP but documented for the AI Developer to allow for architectural hooks.

1. **Data Source:**

- _Current:_ Mock Data.

- _Future:_ Where do we get live prices? (AlphaVantage? Yahoo Finance Proxy? FMP?).

- _Hook:_ Ensure DataService is an interface so the implementation can be swapped later.

2. **Persistence:**

- _Current:_ State resets on refresh.

- _Future:_ Save portfolios to LocalStorage or a cloud DB.

- _Hook:_ Use Solid's createStore effectively so serialization is easy.

3. **Taxes:**

- _Current:_ Ignored.

- _Future:_ Tax-loss harvesting logic.

4. **Correlation Breakdown:**

- _Note:_ During crashes, correlations often converge to 1. The MVP uses static historical covariance. Future versions might need "Stress Covariance Matrices."


## *****8. Instructions for the AI Builder**

- **Start with the Data Layer:** Create robust mock data. The logic is impossible to test without realistic price movements.

- **Strict Math:** Do not hallucinate the QP formula. Use the linear approximation for leverage cost described in Section 3.1.

- **Performance:** Do not run matrix multiplication in the UI thread. Use the Worker pattern immediately.

- **Style:** Use "Glassmorphism" (translucent backgrounds, gradients) as requested for a modern "FinTech" feel.
