# Portfolio Optimization Platform - Technical PRD

## Executive Summary

Transform the existing client-side Kelly Criterion calculator into a production-ready portfolio optimization platform with real-time ETF data, historical analysis, and black swan risk modeling. This PRD provides complete technical specifications for building a serverless AWS architecture that ingests financial data from Polygon.io, stores it efficiently, and serves it through a modern API.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Design](#database-design)
3. [API Specifications](#api-specifications)
4. [Data Ingestion Pipeline](#data-ingestion-pipeline)
5. [Client Application Updates](#client-application-updates)
6. [Security & Authentication](#security--authentication)
7. [Monitoring & Observability](#monitoring--observability)
8. [Implementation Phases](#implementation-phases)
9. [Testing Strategy](#testing-strategy)
10. [Deployment & CI/CD](#deployment--cicd)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CloudFront CDN                           │
│                    (Static Site Distribution)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SolidJS Client App                          │
│              (S3 + Static Site Hosting via SST)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (HTTP API)                        │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Public Routes  │  │ Lambda Auth  │  │  Admin Routes      │  │
│  │ (No Auth)      │  │ (API Key)    │  │  (Requires Auth)   │  │
│  └────────┬───────┘  └──────┬───────┘  └─────────┬──────────┘  │
└───────────┼──────────────────┼────────────────────┼─────────────┘
            │                  │                    │
            ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Lambda Functions                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ getAssets    │  │ getVolatility│  │ adminUpdateData      │  │
│  │              │  │              │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼────────────────────┼──────────────┘
          │                  │                    │
          ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  DynamoDB    │  │  DynamoDb    │  │    S3 Bucket         │  │
│  │  (Metadata & │  │  (Historical │  │    (Backups &        │  │
│  │   Current)   │  │   Prices)    │  │     Exports)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌─────────────────────────────────────────────────────────────────┐
│                    Data Ingestion Pipeline                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ EventBridge  │─▶│  SQS Queue   │─▶│ Ingestion Lambda     │  │
│  │ (Daily Cron) │  │ (Rate Limit) │  │ (Polygon.io)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                       │                          │
│                                       ▼                          │
│                                    ┌──────────────┐             │
│                                    │     DLQ      │             │
│                                    │ (Failed Jobs)│             │
│                                    └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- SolidJS 1.9.3 - Reactive UI framework
- @solidjs/router 0.15.2 - Client-side routing
- TailwindCSS 4.1.14 - Styling
- TypeScript 5.9.3 - Type safety

**Backend:**
- AWS Lambda (Node.js 20.x runtime) - Serverless compute
- API Gateway HTTP API - RESTful API
- DynamoDB - NoSQL for metadata and current data
- Amazon Timestream - Time-series historical data (changed to all dynamo)
- S3 - Object storage for backups and exports
- EventBridge - Scheduled job orchestration
- SQS - Message queue for rate limiting
- CloudWatch - Logging and monitoring

**Infrastructure:**
- SST v3 (Ion) - Infrastructure as Code
- Pulumi - Underlying IaC engine
- AWS Lambda Powertools (TypeScript) - Structured logging

**External APIs:**
- Polygon.io API - Financial market data

---

## Database Design

### DynamoDB Table: `Assets`

**Purpose:** Store ETF metadata, current volatility, and black swan parameters.

**Table Schema:**
```typescript
interface AssetRecord {
  PK: string;              // "ASSET#${symbol}" e.g., "ASSET#SPY"
  SK: string;              // "METADATA" for main record
  symbol: string;          // "SPY", "QQQ", etc.
  name: string;            // "SPDR S&P 500 ETF Trust"
  category: string;        // "Large Cap", "Technology", "Bonds", etc.
  assetClass: string;      // "Equity", "Fixed Income", "Commodity", etc.

  // Current volatility data
  currentImpliedVol30Day: number;     // 30-day implied volatility
  lastUpdated: string;                // ISO 8601 timestamp

  // Historical volatility metrics
  volatility7Day: number;             // 7-day historical volatility
  volatility30Day: number;            // 30-day historical volatility
  volatility90Day: number;            // 90-day historical volatility
  volatility1Year: number;            // 1-year historical volatility
  volatilityLongTerm: number;         // 5+ year historical volatility

  // Black swan parameters
  tailRiskFactor: number;             // Multiplier for extreme events (1.0-5.0)
  maxDrawdown1Year: number;           // Maximum 1-year drawdown (%)
  maxDrawdown5Year: number;           // Maximum 5-year drawdown (%)
  correlationBreakdownRisk: number;   // Risk of correlation breakdown (0-1)

  // Return data
  expectedReturn: number;             // Calculated expected annual return
  sharpeRatio: number;               // Risk-adjusted return metric

  // Metadata
  isActive: boolean;                 // Whether asset is actively tracked
  dataQuality: "HIGH" | "MEDIUM" | "LOW";  // Data completeness indicator
  createdAt: string;
  updatedAt: string;
}

// Volatility history sub-items
interface VolatilityRecord {
  PK: string;              // "ASSET#${symbol}"
  SK: string;              // "VOL#${YYYY-MM-DD}"
  date: string;            // "2025-10-13"
  impliedVol30Day: number;
  historicalVol: number;
  vixLevel?: number;       // Market-wide volatility index
}
```

**Access Patterns:**
1. Get single asset: `PK = "ASSET#SPY" AND SK = "METADATA"`
2. Get all assets: `Query` with `begins_with(PK, "ASSET#")`
3. Get volatility history: `Query` with `PK = "ASSET#SPY" AND begins_with(SK, "VOL#")`
4. Filter by category: GSI on `category` field

**Global Secondary Indexes:**

**GSI-1: CategoryIndex**
- Partition Key: `category`
- Sort Key: `symbol`
- Use case: List all ETFs by category (e.g., "Large Cap", "Technology")

**GSI-2: AssetClassIndex**
- Partition Key: `assetClass`
- Sort Key: `sharpeRatio` (descending)
- Use case: Find best risk-adjusted returns by asset class

**Capacity Planning:**
- On-Demand pricing initially
- Expected ~200 assets (ETFs)
- ~70,000 volatility records per year (200 assets × 365 days)
- Read: 10-50 RCU/sec (public API traffic)
- Write: 1-5 WCU/sec (daily ingestion)

### Amazon Timestream: Historical Price Data (timestream changed to all dynamo)

**Purpose:** Store historical OHLCV (Open, High, Low, Close, Volume) data for correlation matrix and return calculations.

**Database:** `PortfolioOptimizer`
**Table:** `HistoricalPrices`

**Schema:**
```typescript
interface HistoricalPriceRecord {
  symbol: string;           // Dimension
  date: string;             // Time column (ISO 8601)
  open: number;             // Measure
  high: number;             // Measure
  low: number;              // Measure
  close: number;            // Measure
  volume: number;           // Measure
  adjustedClose: number;    // Measure (split/dividend adjusted)
  dailyReturn: number;      // Measure (calculated)
}
```

**Retention Policy:**
- Memory Store: 7 days (fast queries for recent data)
- Magnetic Store: 20 years (cost-effective long-term storage)

**Query Examples:**
```sql
-- Get 1-year daily returns for correlation matrix
SELECT symbol, date, dailyReturn
FROM "PortfolioOptimizer"."HistoricalPrices"
WHERE time BETWEEN ago(365d) AND now()
  AND symbol IN ('SPY', 'QQQ', 'TLT')
ORDER BY time DESC

-- Calculate 30-day volatility
SELECT symbol,
       STDDEV(dailyReturn) * SQRT(252) as annualized_volatility
FROM "PortfolioOptimizer"."HistoricalPrices"
WHERE time BETWEEN ago(30d) AND now()
GROUP BY symbol
```

**Capacity Planning:**
- ~200 assets × 5,000 trading days = 1M records
- Memory Store: ~1,400 records (7 days × 200 assets)
- Magnetic Store: ~1M records
- Estimated cost: ~$5-10/month

### S3 Bucket: Data Backup and Exports

**Bucket:** `portfolio-optimizer-data-{stage}`

**Structure:**
```
portfolio-optimizer-data-production/
├── backups/
│   ├── dynamodb/
│   │   └── assets-backup-{timestamp}.json
│   └── timestream/ (changed to all dynamo)
│       └── historical-prices-{timestamp}.csv
├── exports/
│   ├── correlation-matrices/
│   │   └── correlation-{date}.json
│   └── reports/
│       └── volatility-report-{date}.pdf
└── polygon-raw/
    └── {symbol}/
        └── {date}.json
```

**Lifecycle Policies:**
- `backups/`: Transition to S3 Glacier after 30 days
- `exports/`: Delete after 90 days
- `polygon-raw/`: Delete after 7 days

---

## API Specifications

### Base URL

**Development:** `https://dev-api.kellyportfolios.com`
**Production:** `https://api.kellyportfolios.com`

### Public Endpoints (No Authentication)

#### GET `/assets`

Get list of all available assets.

**Query Parameters:**
```typescript
interface GetAssetsQuery {
  category?: string;        // Filter by category
  assetClass?: string;      // Filter by asset class
  limit?: number;           // Default: 100, Max: 500
  cursor?: string;          // Pagination cursor
  includeInactive?: boolean; // Default: false
}
```

**Response:**
```typescript
interface GetAssetsResponse {
  assets: Asset[];
  nextCursor?: string;
  total: number;
}

interface Asset {
  symbol: string;
  name: string;
  category: string;
  assetClass: string;
  currentImpliedVol30Day: number;
  volatility30Day: number;
  expectedReturn: number;
  sharpeRatio: number;
  lastUpdated: string;
}
```

**Example:**
```bash
GET /assets?category=Large%20Cap&limit=20
```

**Response:**
```json
{
  "assets": [
    {
      "symbol": "SPY",
      "name": "SPDR S&P 500 ETF Trust",
      "category": "Large Cap",
      "assetClass": "Equity",
      "currentImpliedVol30Day": 0.18,
      "volatility30Day": 0.16,
      "expectedReturn": 0.10,
      "sharpeRatio": 0.85,
      "lastUpdated": "2025-10-13T09:30:00Z"
    }
  ],
  "nextCursor": "eyJQSyI6IkFTU0VUI1NQWSIsIlNLIjoiTUVUQURBVEEifQ==",
  "total": 187
}
```

#### GET `/assets/{symbol}`

Get detailed information for a specific asset.

**Path Parameters:**
- `symbol` (string, required): Asset symbol (e.g., "SPY")

**Response:**
```typescript
interface AssetDetail extends Asset {
  volatility7Day: number;
  volatility90Day: number;
  volatility1Year: number;
  volatilityLongTerm: number;
  tailRiskFactor: number;
  maxDrawdown1Year: number;
  maxDrawdown5Year: number;
  correlationBreakdownRisk: number;
  dataQuality: "HIGH" | "MEDIUM" | "LOW";
  createdAt: string;
  updatedAt: string;
}
```

#### GET `/volatility/{symbol}`

Get historical volatility data for an asset.

**Path Parameters:**
- `symbol` (string, required): Asset symbol

**Query Parameters:**
```typescript
interface GetVolatilityQuery {
  startDate?: string;  // ISO 8601 date (default: 30 days ago)
  endDate?: string;    // ISO 8601 date (default: today)
}
```

**Response:**
```typescript
interface VolatilityHistory {
  symbol: string;
  data: VolatilityDataPoint[];
}

interface VolatilityDataPoint {
  date: string;
  impliedVol30Day: number;
  historicalVol: number;
  vixLevel?: number;
}
```

#### POST `/calculate/correlation`

Calculate correlation matrix for a set of assets.

**Request Body:**
```typescript
interface CorrelationRequest {
  symbols: string[];           // Array of asset symbols (max: 50)
  lookbackDays: number;        // 30, 90, 180, 365, or 1825 (5 years)
  includeBlackSwan?: boolean;  // Adjust for tail risk (default: false)
}
```

**Response:**
```typescript
interface CorrelationResponse {
  symbols: string[];
  correlationMatrix: number[][]; // NxN matrix
  lookbackDays: number;
  calculatedAt: string;
  dataQuality: {
    [symbol: string]: "HIGH" | "MEDIUM" | "LOW";
  };
}
```

**Example:**
```bash
POST /calculate/correlation
Content-Type: application/json

{
  "symbols": ["SPY", "QQQ", "TLT"],
  "lookbackDays": 365,
  "includeBlackSwan": false
}
```

#### POST `/calculate/kelly`

Calculate Kelly Criterion optimal allocations.

**Request Body:**
```typescript
interface KellyRequest {
  assets: KellyAssetInput[];
  riskFreeRate: number;        // Annual rate (e.g., 0.03 for 3%)
  riskAversion: number;        // Gamma parameter (default: 5)
  includeBlackSwan?: boolean;  // Adjust for tail risk
  blackSwanMultiplier?: number; // Stress test multiplier (1.0-5.0)
}

interface KellyAssetInput {
  symbol: string;
  // Optional: Use server-calculated values if not provided
  expectedReturn?: number;
  volatility?: number;
}
```

**Response:**
```typescript
interface KellyResponse {
  allocations: {
    symbol: string;
    weight: number;              // Optimal allocation (0-1)
    expectedReturn: number;
    volatility: number;
  }[];
  portfolioMetrics: {
    expectedReturn: number;
    portfolioVolatility: number;
    sharpeRatio: number;
    utility: number;
  };
  blackSwanAdjusted?: {
    allocations: { symbol: string; weight: number }[];
    expectedReturn: number;
    portfolioVolatility: number;
  };
}
```

### Admin Endpoints (Requires API Key)

#### POST `/admin/assets`

Create or update asset metadata.

**Headers:**
- `x-api-key`: Admin API key

**Request Body:**
```typescript
interface AdminAssetUpdate {
  symbol: string;
  name?: string;
  category?: string;
  assetClass?: string;
  isActive?: boolean;
  // Optionally override calculated values
  tailRiskFactor?: number;
  correlationBreakdownRisk?: number;
}
```

#### POST `/admin/ingest/trigger`

Manually trigger data ingestion for specific assets.

**Headers:**
- `x-api-key`: Admin API key

**Request Body:**
```typescript
interface TriggerIngestRequest {
  symbols: string[];           // Assets to update
  startDate?: string;          // Backfill from date
  priority?: "HIGH" | "NORMAL"; // Queue priority
}
```

#### POST `/admin/data/upload`

Upload structured data for bulk updates.

**Headers:**
- `x-api-key`: Admin API key

**Request Body:**
```typescript
interface BulkDataUpload {
  type: "VOLATILITY" | "PRICES" | "METADATA";
  data: Record<string, any>[];
  overwrite?: boolean;
}
```

**Example:**
```json
{
  "type": "VOLATILITY",
  "data": [
    {
      "symbol": "SPY",
      "date": "2025-10-13",
      "impliedVol30Day": 0.18,
      "historicalVol": 0.16
    }
  ],
  "overwrite": true
}
```

### Error Responses

All errors follow this structure:

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  requestId: string;
}
```

**Error Codes:**
- `INVALID_REQUEST` - Malformed request
- `ASSET_NOT_FOUND` - Asset does not exist
- `INSUFFICIENT_DATA` - Not enough historical data
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `UNAUTHORIZED` - Invalid or missing API key
- `INTERNAL_ERROR` - Server error

---

## Data Ingestion Pipeline

### Daily Ingestion Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  EventBridge Rule: Daily at 6:00 PM ET (After Market Close)    │
│  Expression: cron(0 23 * * ? *)                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Lambda: ScheduleIngestion                                       │
│  - Queries DynamoDB for all active assets                       │
│  - Sends one message per asset to SQS                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  SQS: IngestionQueue                                             │
│  - Visibility Timeout: 5 minutes                                │
│  - Max Receive Count: 3 (then → DLQ)                            │
│  - Message Deduplication: Enabled                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Lambda: ProcessIngestion                                        │
│  - Event Source: SQS (MaxConcurrency: 1)                        │
│  - Processes messages sequentially                              │
│  - Rate limits to 5 Polygon.io calls/min                        │
│  - Stores raw data in S3                                        │
│  - Writes to DynamoDB                                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Storage                                                         │
│  - S3: Raw Polygon.io responses                                 │
│  - DynamoDB: Asset metadata + current volatility                │
│  - DynamoDB: Historical OHLCV data                              │
└─────────────────────────────────────────────────────────────────┘
```

### Rate Limiting Strategy

**Polygon.io Free Tier Constraints:**
- 5 API calls per minute
- No rollover or burst capacity

**Implementation:**
1. **SQS FIFO Queue** with `MaximumConcurrency: 1` on Lambda
2. **Token Bucket Algorithm** in Lambda:
   ```typescript
   let lastCallTime = 0;
   const CALLS_PER_MINUTE = 5;
   const INTERVAL_MS = 60000 / CALLS_PER_MINUTE; // 12 seconds

   async function rateLimitedFetch(url: string) {
     const now = Date.now();
     const timeSinceLastCall = now - lastCallTime;

     if (timeSinceLastCall < INTERVAL_MS) {
       await new Promise(resolve =>
         setTimeout(resolve, INTERVAL_MS - timeSinceLastCall)
       );
     }

     lastCallTime = Date.now();
     return fetch(url);
   }
   ```

3. **DLQ Handling**: Failed messages after 3 retries trigger CloudWatch Alarm

### Polygon.io API Integration

**Endpoints Used:**
1. **Aggregates (Bars)**: `/v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}`
   - Gets daily OHLCV data
   - Up to 50,000 results per request

2. **Options Snapshot**: `/v3/snapshot/options/{underlyingAsset}`
   - Gets current implied volatility from options chain
   - Calculates 30-day IV from ATM options

**Data Processing:**
```typescript
interface PolygonAggregate {
  v: number;   // Volume
  vw: number;  // Volume Weighted Average Price
  o: number;   // Open
  c: number;   // Close
  h: number;   // High
  l: number;   // Low
  t: number;   // Timestamp (milliseconds)
  n: number;   // Number of transactions
}

async function processPolygonData(
  symbol: string,
  data: PolygonAggregate[]
) {
  // Calculate daily returns
  const returns = data.map((d, i) => {
    if (i === 0) return 0;
    return Math.log(d.c / data[i-1].c);
  });

  // Calculate various volatilities
  const vol7Day = calculateVolatility(returns.slice(-7));
  const vol30Day = calculateVolatility(returns.slice(-30));
  const vol1Year = calculateVolatility(returns.slice(-252));

  // Store in dynamo
  await storeHistoricalPrices(symbol, data);

  // Update DynamoDB
  await updateAssetVolatility(symbol, {
    volatility7Day: vol7Day,
    volatility30Day: vol30Day,
    volatility1Year: vol1Year,
    lastUpdated: new Date().toISOString()
  });
}
```

### Initial Data Seeding

**Asset List:**
Start with 100 most popular ETFs across categories:

**Large Cap Equity (20):**
- SPY, VOO, IVV (S&P 500)
- QQQ, QQQM (Nasdaq-100)
- VTI, ITOT (Total Market)
- DIA (Dow Jones)
- IWM, VB (Small Cap)
- VUG, IWF (Growth)
- VTV, IWD (Value)

**Sector ETFs (15):**
- XLK (Technology)
- XLF (Financial)
- XLV (Healthcare)
- XLE (Energy)
- XLI (Industrial)
- XLP (Consumer Staples)
- XLY (Consumer Discretionary)
- XLU (Utilities)
- XLRE (Real Estate)
- XLC (Communication)
- XLB (Materials)

**International (15):**
- VEA, IEFA (Developed Markets)
- VWO, IEMG (Emerging Markets)
- EFA (EAFE)
- FXI (China)
- EWJ (Japan)
- EWG (Germany)
- EWU (UK)

**Fixed Income (20):**
- AGG, BND (Aggregate Bond)
- TLT, IEF, SHY (Treasury - Long/Mid/Short)
- LQD (Investment Grade Corporate)
- HYG, JNK (High Yield)
- MUB (Municipal)
- TIP (TIPS - Inflation Protected)
- EMB (Emerging Market Bonds)

**Commodities & Alternatives (15):**
- GLD, IAU (Gold)
- SLV (Silver)
- USO (Oil)
- DBC (Commodities)
- VNQ (Real Estate)
- REIT (REIT)

**Volatility (5):**
- VXX (Short-term VIX Futures)
- VIXY (VIX Futures)

**Multi-Asset (10):**
- AOR, AOM, AOA (Vanguard Allocation)
- VBINX (Balanced Index)

### Backfilling Strategy

1. **Initial Load**: Fetch last 5 years of daily data
2. **Batch Processing**: Process 5 assets per day (respecting rate limits)
3. **Completion Time**: ~20 days for 100 assets
4. **Priority Order**: Most popular ETFs first (SPY, QQQ, TLT, AGG, etc.)

---

## Client Application Updates

### New Features

#### 1. Asset Search & Autocomplete

**Location:** `src/components/AssetSearch.tsx`

```typescript
interface AssetSearchProps {
  onSelect: (asset: Asset) => void;
  excludeSymbols?: string[];
}
```

**Features:**
- Debounced search (300ms)
- Search by symbol or name
- Category filters
- Display volatility and Sharpe ratio in results
- Keyboard navigation (arrow keys, enter)

**API Integration:**
```typescript
async function searchAssets(query: string): Promise<Asset[]> {
  const response = await fetch(
    `${API_BASE}/assets?limit=20&symbol=${encodeURIComponent(query)}`
  );
  return response.json();
}
```

#### 2. Volatility Display Component

**Location:** `src/components/VolatilityChart.tsx`

**Features:**
- Line chart showing 30-day historical volatility
- Current vs. historical average comparison
- VIX correlation indicator
- Time range selector (7d, 30d, 90d, 1y)

**Data Fetching:**
```typescript
async function getVolatilityHistory(
  symbol: string,
  days: number
): Promise<VolatilityDataPoint[]> {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  const response = await fetch(
    `${API_BASE}/volatility/${symbol}?startDate=${startDate.toISOString()}`
  );
  return response.json();
}
```

#### 3. Black Swan Toggle & Controls

**Location:** Updated `src/routes/calculator.tsx`

**New UI Elements:**
```typescript
interface BlackSwanSettings {
  enabled: boolean;
  multiplier: number;        // 1.0 - 5.0 (stress test severity)
  showComparison: boolean;   // Show side-by-side normal vs black swan
}
```

**Display:**
- Toggle switch: "Enable Black Swan Adjustment"
- Slider: "Stress Test Severity" (1x - 5x)
- Checkbox: "Show Comparison View"
- Info tooltip explaining tail risk modeling

#### 4. Enhanced Portfolio Metrics

**New Metrics to Display:**
- Maximum Drawdown (1Y, 5Y)
- Tail Risk Score (0-100)
- Correlation Breakdown Risk
- VaR (Value at Risk) at 95% and 99% confidence
- Expected Shortfall (CVaR)

#### 5. Correlation Matrix Visualization

**Location:** `src/components/CorrelationMatrix.tsx`

**Features:**
- Heatmap visualization (red = negative, white = 0, blue = positive)
- Hover for exact correlation values
- Click asset to highlight row/column
- Export to CSV

**Data Fetching:**
```typescript
async function getCorrelationMatrix(
  symbols: string[],
  lookbackDays: number,
  includeBlackSwan: boolean
): Promise<CorrelationResponse> {
  const response = await fetch(`${API_BASE}/calculate/correlation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbols, lookbackDays, includeBlackSwan })
  });
  return response.json();
}
```

### Updated Calculation Flow

**Old Flow (Client-side only):**
```
User enters asset data → Client calculates → Display results
```

**New Flow (Hybrid):**
```
User selects assets from search
  ↓
Fetch latest volatility & returns from API
  ↓
Option 1: Use server-calculated Kelly (POST /calculate/kelly)
Option 2: Use client-side with API data
  ↓
Display results with enhanced metrics
```

### API Client Service

**Location:** `src/services/api.ts`

```typescript
class PortfolioAPI {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async getAssets(params?: GetAssetsQuery): Promise<Asset[]> {
    const query = new URLSearchParams(params as any).toString();
    const response = await fetch(`${this.baseURL}/assets?${query}`);

    if (!response.ok) {
      throw new APIError(await response.json());
    }

    return response.json();
  }

  async getAsset(symbol: string): Promise<AssetDetail> {
    const response = await fetch(`${this.baseURL}/assets/${symbol}`);

    if (!response.ok) {
      throw new APIError(await response.json());
    }

    return response.json();
  }

  async calculateKelly(
    request: KellyRequest
  ): Promise<KellyResponse> {
    const response = await fetch(`${this.baseURL}/calculate/kelly`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new APIError(await response.json());
    }

    return response.json();
  }
}

export const api = new PortfolioAPI(
  import.meta.env.VITE_API_URL || 'https://api.kellyportfolios.com'
);
```

### Environment Configuration

**`.env.development`**
```
VITE_API_URL=https://dev-api.kellyportfolios.com
```

**`.env.production`**
```
VITE_API_URL=https://api.kellyportfolios.com
```

### State Management Updates

**New Store:** `src/stores/portfolioStore.ts`

```typescript
import { createStore } from "solid-js/store";

interface PortfolioStore {
  assets: Asset[];
  selectedAssets: AssetDetail[];
  blackSwanSettings: BlackSwanSettings;
  optimizationResult: KellyResponse | null;
  isLoading: boolean;
  error: string | null;
}

export const [portfolioStore, setPortfolioStore] = createStore<PortfolioStore>({
  assets: [],
  selectedAssets: [],
  blackSwanSettings: {
    enabled: false,
    multiplier: 2.0,
    showComparison: true
  },
  optimizationResult: null,
  isLoading: false,
  error: null
});
```

---

## Security & Authentication

### Admin API Key Authentication

**Implementation:** Lambda Authorizer

**Lambda:** `infra/functions/adminAuthorizer.ts`

```typescript
import { APIGatewayAuthorizerResult, APIGatewayTokenAuthorizerEvent } from 'aws-lambda';
import { SSMClient, GetParameterCommand } from '@aws-sdk/client-ssm';

const ssm = new SSMClient({});

export async function handler(
  event: APIGatewayTokenAuthorizerEvent
): Promise<APIGatewayAuthorizerResult> {
  const token = event.authorizationToken;

  // Get API key from SSM Parameter Store
  const { Parameter } = await ssm.send(new GetParameterCommand({
    Name: '/portfolio-optimizer/admin-api-key',
    WithDecryption: true
  }));

  const isValid = token === `Bearer ${Parameter?.Value}`;

  return {
    principalId: 'admin',
    policyDocument: {
      Version: '2012-10-17',
      Statement: [{
        Action: 'execute-api:Invoke',
        Effect: isValid ? 'Allow' : 'Deny',
        Resource: event.methodArn
      }]
    }
  };
}
```

**API Key Storage:**
```bash
# Store in SSM Parameter Store (SecureString)
aws ssm put-parameter \
  --name /portfolio-optimizer/admin-api-key \
  --value "$(openssl rand -hex 32)" \
  --type SecureString \
  --tier Standard
```

### Rate Limiting (Public Endpoints)

**Option 1: API Gateway Throttling**
- Steady-state: 100 requests/second
- Burst: 200 requests

**Option 2: AWS WAF Rate-Based Rule**
- 1,000 requests per 5-minute period per IP
- Automatic blocking for 10 minutes on violation

**SST Configuration:**
```typescript
// sst.config.ts
const api = new sst.aws.ApiGatewayV2("Api", {
  routes: {
    "GET /assets": "functions/getAssets.handler",
    // ...
  },
  throttle: {
    rate: 100,
    burst: 200
  }
});
```

### CORS Configuration

```typescript
const corsConfig = {
  allowOrigins: [
    'https://kellyportfolios.com',
    'https://www.kellyportfolios.com',
    'http://localhost:5173' // Development
  ],
  allowHeaders: ['Content-Type', 'Authorization', 'X-Api-Key'],
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  maxAge: 3600
};
```

### Secrets Management

**Secrets Stored in AWS Secrets Manager:**
1. Polygon.io API Key: `/portfolio-optimizer/polygon-api-key`
2. Admin API Key: `/portfolio-optimizer/admin-api-key`

**Access Pattern:**
```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

const secretsManager = new SecretsManagerClient({});

async function getPolygonApiKey(): Promise<string> {
  const { SecretString } = await secretsManager.send(
    new GetSecretValueCommand({
      SecretId: '/portfolio-optimizer/polygon-api-key'
    })
  );
  return SecretString!;
}
```

---

## Monitoring & Observability

### CloudWatch Log Groups

**Structure:**
```
/aws/lambda/portfolio-optimizer-dev-getAssets
/aws/lambda/portfolio-optimizer-dev-getVolatility
/aws/lambda/portfolio-optimizer-dev-calculateKelly
/aws/lambda/portfolio-optimizer-dev-scheduleIngestion
/aws/lambda/portfolio-optimizer-dev-processIngestion
/aws/lambda/portfolio-optimizer-dev-adminUpdateData
```

**Retention:** 14 days (dev), 90 days (production)

### Structured Logging with Powertools

**Setup:**
```typescript
import { Logger } from '@aws-lambda-powertools/logger';
import { Metrics, MetricUnits } from '@aws-lambda-powertools/metrics';

const logger = new Logger({ serviceName: 'portfolio-optimizer' });
const metrics = new Metrics({ namespace: 'PortfolioOptimizer' });

export async function handler(event: APIGatewayProxyEvent) {
  logger.info('Processing request', {
    path: event.path,
    method: event.httpMethod,
    requestId: event.requestContext.requestId
  });

  metrics.addMetric('ApiRequest', MetricUnits.Count, 1);

  try {
    // Process request
    const result = await processRequest(event);

    metrics.addMetric('ApiSuccess', MetricUnits.Count, 1);
    return result;
  } catch (error) {
    logger.error('Request failed', { error });
    metrics.addMetric('ApiError', MetricUnits.Count, 1);
    throw error;
  }
}
```

### CloudWatch Metrics

**Custom Metrics:**
- `ApiRequest` - Total API requests
- `ApiSuccess` - Successful requests
- `ApiError` - Failed requests
- `ApiLatency` - Response time (ms)
- `IngestionSuccess` - Successful data ingestions
- `IngestionFailure` - Failed data ingestions
- `PolygonApiCall` - Polygon.io API calls
- `CacheHit` / `CacheMiss` - Cache performance

**Dashboards:**
1. **API Performance Dashboard**
   - Request rate (RPM)
   - Error rate (%)
   - P50, P95, P99 latencies
   - Throttled requests

2. **Data Ingestion Dashboard**
   - Ingestion success rate
   - Polygon.io API usage
   - SQS queue depth
   - DLQ message count

3. **Cost Dashboard**
   - Lambda invocations & duration
   - DynamoDB read/write units
   - Dynamo queries
   - Data transfer costs

### CloudWatch Alarms

**Critical Alarms:**
1. **High Error Rate**
   - Metric: `ApiError` > 5% of requests
   - Action: SNS notification to ops team

2. **Ingestion Failures**
   - Metric: DLQ message count > 10
   - Action: SNS notification + PagerDuty

3. **API Latency**
   - Metric: P95 latency > 2 seconds
   - Action: SNS notification

4. **Polygon.io Rate Limit**
   - Metric: 429 responses from Polygon.io
   - Action: SNS notification

**SST Configuration:**
```typescript
const alarm = new cloudwatch.Alarm("HighErrorRate", {
  metric: api.metricServerError(),
  threshold: 5,
  evaluationPeriods: 2,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

new sns.Topic("AlertTopic", {
  subscribers: ["ops@kellyportfolios.com"]
});
```

### X-Ray Tracing

Enable AWS X-Ray for distributed tracing:

```typescript
// Enable X-Ray tracing
const api = new sst.aws.ApiGatewayV2("Api", {
  tracingEnabled: true,
  routes: { /* ... */ }
});

// Instrument SDK calls
import { captureAWSv3Client } from 'aws-xray-sdk-core';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';

const dynamodb = captureAWSv3Client(new DynamoDBClient({}));
```

---

## Implementation Phases

### Phase 1: Infrastructure Foundation (Week 1-2)

**Deliverables:**
- [x] DynamoDB table with GSIs
- [x] Timestream database and table
- [x] S3 bucket with lifecycle policies
- [x] Basic Lambda function scaffolding
- [x] API Gateway HTTP API
- [x] CloudWatch log groups

**Files to Create:**
```
infra/
├── database.ts          # DynamoDB
├── storage.ts           # S3 buckets
├── api.ts               # API Gateway
└── monitoring.ts        # CloudWatch setup

sst.config.ts            # Updated SST config
```

**Acceptance Criteria:**
- Can deploy infrastructure with `pnpm sst deploy --stage dev`
- DynamoDB table exists with correct schema
- DynamoDB database can be queried
- S3 bucket has lifecycle policies applied

### Phase 2: Data Ingestion Pipeline (Week 2-3)

**Deliverables:**
- [x] EventBridge scheduled rule
- [x] SQS queue with DLQ
- [x] Lambda: ScheduleIngestion
- [x] Lambda: ProcessIngestion
- [x] Polygon.io integration
- [x] Rate limiting implementation

**Files to Create:**
```
infra/
└── ingestion.ts         # EventBridge + SQS

functions/
├── scheduleIngestion/
│   ├── index.ts
│   └── handler.test.ts
└── processIngestion/
    ├── index.ts
    ├── polygon.ts       # Polygon.io client
    ├── rateLimit.ts     # Rate limiter
    └── handler.test.ts
```

**Acceptance Criteria:**
- EventBridge triggers daily at correct time
- SQS receives messages for all active assets
- ProcessIngestion respects 5 calls/min rate limit
- Data successfully written to DynamoDB and Timestream (changed to all dynamo)
- Failed messages move to DLQ after 3 attempts

### Phase 3: API Implementation (Week 3-4)

**Deliverables:**
- [x] GET /assets
- [x] GET /assets/{symbol}
- [x] GET /volatility/{symbol}
- [x] POST /calculate/correlation
- [x] POST /calculate/kelly
- [x] Error handling & validation
- [x] API documentation

**Files to Create:**
```
functions/
├── getAssets/
│   ├── index.ts
│   └── handler.test.ts
├── getAsset/
│   ├── index.ts
│   └── handler.test.ts
├── getVolatility/
│   ├── index.ts
│   └── handler.test.ts
├── calculateCorrelation/
│   ├── index.ts
│   ├── correlation.ts
│   └── handler.test.ts
└── calculateKelly/
    ├── index.ts
    ├── kelly.ts
    └── handler.test.ts

shared/
├── types.ts             # Shared TypeScript types
├── errors.ts            # Error handling
└── validation.ts        # Request validation
```

**Acceptance Criteria:**
- All endpoints return correct responses
- Input validation works correctly
- Error responses follow standard format
- API responds within 2 seconds (P95)

### Phase 4: Admin Endpoints & Authentication (Week 4)

**Deliverables:**
- [x] Lambda authorizer
- [x] POST /admin/assets
- [x] POST /admin/ingest/trigger
- [x] POST /admin/data/upload
- [x] API key management

**Files to Create:**
```
functions/
├── adminAuthorizer/
│   ├── index.ts
│   └── handler.test.ts
└── admin/
    ├── updateAssets.ts
    ├── triggerIngest.ts
    └── uploadData.ts
```

**Acceptance Criteria:**
- Admin endpoints reject requests without valid API key
- Valid API key grants access
- Bulk data upload processes correctly
- Manual ingestion trigger works

### Phase 5: Client Application Updates (Week 5-6)

**Deliverables:**
- [x] Asset search component
- [x] API integration service
- [x] Volatility chart component
- [x] Black swan toggle & controls
- [x] Enhanced portfolio metrics
- [x] Correlation matrix visualization

**Files to Create:**
```
src/
├── services/
│   ├── api.ts           # API client
│   └── types.ts         # API types
├── components/
│   ├── AssetSearch.tsx
│   ├── VolatilityChart.tsx
│   └── CorrelationMatrix.tsx
├── stores/
│   └── portfolioStore.ts
└── routes/
    └── calculator.tsx    # Updated

.env.development
.env.production
```

**Acceptance Criteria:**
- Asset search returns results within 500ms
- Volatility chart displays correctly
- Black swan toggle affects calculations
- All components are responsive
- Loading states are handled gracefully

### Phase 6: Initial Data Seeding (Week 6-7)

**Deliverables:**
- [x] Seed script for 100 ETFs
- [x] Backfill historical data
- [x] Validation of data quality

**Files to Create:**
```
scripts/
├── seed-assets.ts       # Create asset records
└── backfill-data.ts     # Fetch historical data
```

**Acceptance Criteria:**
- 100 ETFs seeded in DynamoDB
- 5 years of historical data in Timestream (changed to all dynamo)
- All assets have current volatility data
- Data quality metrics show "HIGH"

### Phase 7: Testing & Optimization (Week 7-8)

**Deliverables:**
- [x] Unit tests for all Lambda functions
- [x] Integration tests for API endpoints
- [x] Load testing
- [x] Performance optimization
- [x] Cost optimization

**Tools:**
- Jest for unit tests
- Artillery for load testing
- AWS Cost Explorer for cost analysis

**Acceptance Criteria:**
- 80%+ code coverage
- All API endpoints pass load test (100 RPS)
- P95 latency < 2 seconds
- Monthly cost < $50 for dev environment

### Phase 8: Production Deployment (Week 8)

**Deliverables:**
- [x] Production infrastructure
- [x] Custom domain setup
- [x] SSL certificates
- [x] CloudWatch alarms
- [x] Monitoring dashboards
- [x] Documentation

**Acceptance Criteria:**
- Production API accessible at api.kellyportfolios.com
- Client app deployed to kellyportfolios.com
- All alarms configured and tested
- Documentation complete and published

---

## Testing Strategy

### Unit Tests

**Framework:** Jest with ts-jest

**Coverage Requirements:**
- Lambda handlers: 80%+
- Business logic: 90%+
- Utilities: 95%+

**Example Test:**
```typescript
// functions/getAssets/handler.test.ts
import { handler } from './index';
import { mockClient } from 'aws-sdk-client-mock';
import { DynamoDBDocumentClient, QueryCommand } from '@aws-sdk/lib-dynamodb';

const ddbMock = mockClient(DynamoDBDocumentClient);

describe('getAssets', () => {
  beforeEach(() => {
    ddbMock.reset();
  });

  it('should return assets', async () => {
    ddbMock.on(QueryCommand).resolves({
      Items: [
        { symbol: 'SPY', name: 'SPDR S&P 500 ETF Trust' }
      ]
    });

    const event = {
      queryStringParameters: { limit: '10' }
    } as any;

    const response = await handler(event);

    expect(response.statusCode).toBe(200);
    expect(JSON.parse(response.body).assets).toHaveLength(1);
  });
});
```

### Integration Tests

**Framework:** Jest + Supertest

**Scope:**
- API endpoint to database
- Full request/response cycle
- Error handling

**Example Test:**
```typescript
// tests/integration/api.test.ts
import { fetch } from 'undici';

const API_URL = process.env.API_URL || 'http://localhost:3000';

describe('Assets API', () => {
  it('should fetch assets', async () => {
    const response = await fetch(`${API_URL}/assets?limit=10`);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.assets).toBeInstanceOf(Array);
    expect(data.total).toBeGreaterThan(0);
  });

  it('should fetch single asset', async () => {
    const response = await fetch(`${API_URL}/assets/SPY`);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.symbol).toBe('SPY');
    expect(data.volatility30Day).toBeGreaterThan(0);
  });
});
```

### Load Testing

**Tool:** Artillery

**Configuration:**
```yaml
# artillery-config.yml
config:
  target: "https://api.kellyportfolios.com"
  phases:
    - duration: 300
      arrivalRate: 10
      name: "Warm up"
    - duration: 600
      arrivalRate: 50
      name: "Sustained load"
    - duration: 120
      arrivalRate: 100
      name: "Peak load"
  processor: "./artillery-processor.js"

scenarios:
  - name: "Get assets"
    weight: 50
    flow:
      - get:
          url: "/assets?limit=20"

  - name: "Get single asset"
    weight: 30
    flow:
      - get:
          url: "/assets/SPY"

  - name: "Calculate Kelly"
    weight: 20
    flow:
      - post:
          url: "/calculate/kelly"
          json:
            assets:
              - symbol: "SPY"
              - symbol: "QQQ"
              - symbol: "TLT"
            riskFreeRate: 0.03
            riskAversion: 5
```

**Run:**
```bash
artillery run artillery-config.yml
```

### End-to-End Tests

**Framework:** Playwright

**Scope:**
- Full user workflows in browser
- Asset search → selection → optimization
- Black swan toggle scenarios

**Example:**
```typescript
// e2e/calculator.spec.ts
import { test, expect } from '@playwright/test';

test('should optimize portfolio', async ({ page }) => {
  await page.goto('http://localhost:5173/calculator');

  // Search for SPY
  await page.fill('[data-testid="asset-search"]', 'SPY');
  await page.waitForSelector('[data-testid="search-result"]');
  await page.click('[data-testid="search-result"]:first-child');

  // Verify asset added
  await expect(page.locator('[data-testid="selected-asset"]')).toHaveCount(1);

  // Optimize
  await page.click('[data-testid="optimize-button"]');
  await page.waitForSelector('[data-testid="optimization-result"]');

  // Check results
  const weight = await page.textContent('[data-testid="asset-weight"]');
  expect(parseFloat(weight!)).toBeGreaterThan(0);
});
```

---

## Deployment & CI/CD

### GitHub Actions Workflow

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

env:
  AWS_REGION: us-east-1

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        run: pnpm install

      - name: Run type checking
        run: pnpm typecheck

      - name: Run linting
        run: pnpm biome:fix

      - name: Run unit tests
        run: pnpm test:unit
        env:
          CI: true

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage/coverage-final.json

  deploy:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        run: pnpm install

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Determine stage
        id: stage
        run: |
          if [ "${{ github.ref }}" == "refs/heads/main" ]; then
            echo "stage=production" >> $GITHUB_OUTPUT
          else
            echo "stage=dev" >> $GITHUB_OUTPUT
          fi

      - name: Deploy infrastructure
        run: pnpm sst deploy --stage ${{ steps.stage.outputs.stage }}

      - name: Run integration tests
        if: steps.stage.outputs.stage == 'dev'
        run: pnpm test:integration
        env:
          API_URL: ${{ steps.deploy.outputs.api_url }}
```

### Pre-deployment Checklist

**Development → Production:**
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Load tests completed successfully
- [ ] Cost analysis reviewed
- [ ] CloudWatch alarms configured
- [ ] Documentation updated
- [ ] Stakeholder approval obtained

### Rollback Strategy

**Automated Rollback:**
- CloudWatch Alarm triggers on high error rate
- Lambda function versions allow instant revert

**Manual Rollback:**
```bash
# Revert to previous version
pnpm sst deploy --stage production --rollback
```

### Blue-Green Deployment

For zero-downtime deployments:

1. Deploy new Lambda versions
2. Update API Gateway to point to new versions
3. Monitor error rates for 5 minutes
4. If errors > threshold, revert API Gateway routes
5. If successful, remove old Lambda versions

---

## Appendix

### Glossary

- **Kelly Criterion**: Mathematical formula for optimal position sizing
- **ETF**: Exchange-Traded Fund
- **Implied Volatility**: Market's forecast of asset price movement
- **Black Swan**: Rare, high-impact unpredictable event
- **Correlation Matrix**: Table showing correlations between assets
- **Sharpe Ratio**: Risk-adjusted return metric
- **VaR**: Value at Risk - potential loss at confidence level
- **Tail Risk**: Risk of extreme losses in distribution tails

### References

1. Kelly Criterion: https://en.wikipedia.org/wiki/Kelly_criterion
2. Modern Portfolio Theory: Markowitz (1952)
3. Polygon.io API Docs: https://polygon.io/docs
4. AWS Lambda Best Practices: https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
5. DynamoDB Time Series Patterns: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html

### Contact

**Technical Questions:** dev@kellyportfolios.com
**Infrastructure:** ops@kellyportfolios.com
**Security:** security@kellyportfolios.com

---

## Document Version

**Version:** 1.0.0
**Last Updated:** 2025-10-13
**Authors:** System Architect Team
**Approvers:** Engineering Lead, Product Manager, CTO
