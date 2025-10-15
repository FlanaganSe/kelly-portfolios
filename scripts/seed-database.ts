#!/usr/bin/env tsx
/**
 * Seed script to populate DynamoDB with 100 ETFs and mock historical price data
 */

import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand, BatchWriteCommand } from "@aws-sdk/lib-dynamodb";

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({ region: "us-east-1" }));

// 100 popular ETFs across different categories
const etfs = [
  // Large Cap US Equity
  { symbol: "SPY", name: "SPDR S&P 500 ETF Trust", category: "Large Cap", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.16 },
  { symbol: "VOO", name: "Vanguard S&P 500 ETF", category: "Large Cap", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.16 },
  { symbol: "IVV", name: "iShares Core S&P 500 ETF", category: "Large Cap", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.16 },
  { symbol: "VTI", name: "Vanguard Total Stock Market ETF", category: "Total Market", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.17 },
  { symbol: "ITOT", name: "iShares Core S&P Total U.S. Stock Market ETF", category: "Total Market", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.17 },

  // Technology
  { symbol: "QQQ", name: "Invesco QQQ Trust", category: "Technology", assetClass: "Equity", expectedReturn: 0.13, volatility: 0.22 },
  { symbol: "QQQM", name: "Invesco NASDAQ 100 ETF", category: "Technology", assetClass: "Equity", expectedReturn: 0.13, volatility: 0.22 },
  { symbol: "XLK", name: "Technology Select Sector SPDR Fund", category: "Technology", assetClass: "Equity", expectedReturn: 0.13, volatility: 0.23 },
  { symbol: "VGT", name: "Vanguard Information Technology ETF", category: "Technology", assetClass: "Equity", expectedReturn: 0.13, volatility: 0.23 },
  { symbol: "FTEC", name: "Fidelity MSCI Information Technology ETF", category: "Technology", assetClass: "Equity", expectedReturn: 0.13, volatility: 0.23 },

  // Small/Mid Cap
  { symbol: "IWM", name: "iShares Russell 2000 ETF", category: "Small Cap", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.24 },
  { symbol: "IJH", name: "iShares Core S&P Mid-Cap ETF", category: "Mid Cap", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.20 },
  { symbol: "MDY", name: "SPDR S&P MidCap 400 ETF Trust", category: "Mid Cap", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.20 },
  { symbol: "VB", name: "Vanguard Small-Cap ETF", category: "Small Cap", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.24 },
  { symbol: "VTWO", name: "Vanguard Russell 2000 ETF", category: "Small Cap", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.24 },

  // International Developed
  { symbol: "VEA", name: "Vanguard FTSE Developed Markets ETF", category: "International", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.18 },
  { symbol: "IEFA", name: "iShares Core MSCI EAFE ETF", category: "International", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.18 },
  { symbol: "EFA", name: "iShares MSCI EAFE ETF", category: "International", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.18 },
  { symbol: "SCHF", name: "Schwab International Equity ETF", category: "International", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.18 },
  { symbol: "VEU", name: "Vanguard FTSE All-World ex-US ETF", category: "International", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.19 },

  // Emerging Markets
  { symbol: "VWO", name: "Vanguard FTSE Emerging Markets ETF", category: "Emerging Markets", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.22 },
  { symbol: "IEMG", name: "iShares Core MSCI Emerging Markets ETF", category: "Emerging Markets", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.22 },
  { symbol: "EEM", name: "iShares MSCI Emerging Markets ETF", category: "Emerging Markets", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.22 },
  { symbol: "SCHE", name: "Schwab Emerging Markets Equity ETF", category: "Emerging Markets", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.22 },

  // Bonds - Treasury
  { symbol: "AGG", name: "iShares Core U.S. Aggregate Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.04, volatility: 0.06 },
  { symbol: "BND", name: "Vanguard Total Bond Market ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.04, volatility: 0.06 },
  { symbol: "TLT", name: "iShares 20+ Year Treasury Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.14 },
  { symbol: "IEF", name: "iShares 7-10 Year Treasury Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.08 },
  { symbol: "SHY", name: "iShares 1-3 Year Treasury Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.02, volatility: 0.02 },
  { symbol: "VGIT", name: "Vanguard Intermediate-Term Treasury ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.07 },
  { symbol: "VGLT", name: "Vanguard Long-Term Treasury ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.14 },
  { symbol: "GOVT", name: "iShares U.S. Treasury Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.06 },

  // Bonds - Corporate
  { symbol: "LQD", name: "iShares iBoxx Investment Grade Corporate Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.05, volatility: 0.09 },
  { symbol: "VCIT", name: "Vanguard Intermediate-Term Corporate Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.05, volatility: 0.08 },
  { symbol: "VCSH", name: "Vanguard Short-Term Corporate Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.04, volatility: 0.04 },
  { symbol: "USIG", name: "iShares Broad USD Investment Grade Corporate Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.05, volatility: 0.08 },

  // High Yield
  { symbol: "HYG", name: "iShares iBoxx High Yield Corporate Bond ETF", category: "High Yield", assetClass: "Fixed Income", expectedReturn: 0.06, volatility: 0.12 },
  { symbol: "JNK", name: "SPDR Bloomberg High Yield Bond ETF", category: "High Yield", assetClass: "Fixed Income", expectedReturn: 0.06, volatility: 0.12 },

  // Commodities
  { symbol: "GLD", name: "SPDR Gold Shares", category: "Commodities", assetClass: "Commodity", expectedReturn: 0.05, volatility: 0.18 },
  { symbol: "IAU", name: "iShares Gold Trust", category: "Commodities", assetClass: "Commodity", expectedReturn: 0.05, volatility: 0.18 },
  { symbol: "SLV", name: "iShares Silver Trust", category: "Commodities", assetClass: "Commodity", expectedReturn: 0.06, volatility: 0.28 },
  { symbol: "DBC", name: "Invesco DB Commodity Index Tracking Fund", category: "Commodities", assetClass: "Commodity", expectedReturn: 0.05, volatility: 0.20 },
  { symbol: "GSG", name: "iShares S&P GSCI Commodity-Indexed Trust", category: "Commodities", assetClass: "Commodity", expectedReturn: 0.05, volatility: 0.22 },

  // Sector - Energy
  { symbol: "XLE", name: "Energy Select Sector SPDR Fund", category: "Energy", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.28 },
  { symbol: "VDE", name: "Vanguard Energy ETF", category: "Energy", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.28 },

  // Sector - Financials
  { symbol: "XLF", name: "Financial Select Sector SPDR Fund", category: "Financials", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.20 },
  { symbol: "VFH", name: "Vanguard Financials ETF", category: "Financials", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.20 },

  // Sector - Healthcare
  { symbol: "XLV", name: "Health Care Select Sector SPDR Fund", category: "Healthcare", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.15 },
  { symbol: "VHT", name: "Vanguard Health Care ETF", category: "Healthcare", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.15 },

  // Sector - Consumer
  { symbol: "XLY", name: "Consumer Discretionary Select Sector SPDR Fund", category: "Consumer", assetClass: "Equity", expectedReturn: 0.12, volatility: 0.19 },
  { symbol: "XLP", name: "Consumer Staples Select Sector SPDR Fund", category: "Consumer", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.12 },
  { symbol: "VCR", name: "Vanguard Consumer Discretionary ETF", category: "Consumer", assetClass: "Equity", expectedReturn: 0.12, volatility: 0.19 },
  { symbol: "VDC", name: "Vanguard Consumer Staples ETF", category: "Consumer", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.12 },

  // Sector - Industrials
  { symbol: "XLI", name: "Industrial Select Sector SPDR Fund", category: "Industrials", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.18 },
  { symbol: "VIS", name: "Vanguard Industrials ETF", category: "Industrials", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.18 },

  // Sector - Materials
  { symbol: "XLB", name: "Materials Select Sector SPDR Fund", category: "Materials", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.20 },
  { symbol: "VAW", name: "Vanguard Materials ETF", category: "Materials", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.20 },

  // Sector - Utilities
  { symbol: "XLU", name: "Utilities Select Sector SPDR Fund", category: "Utilities", assetClass: "Equity", expectedReturn: 0.07, volatility: 0.14 },
  { symbol: "VPU", name: "Vanguard Utilities ETF", category: "Utilities", assetClass: "Equity", expectedReturn: 0.07, volatility: 0.14 },

  // Sector - Real Estate
  { symbol: "VNQ", name: "Vanguard Real Estate ETF", category: "Real Estate", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.20 },
  { symbol: "XLRE", name: "Real Estate Select Sector SPDR Fund", category: "Real Estate", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.20 },
  { symbol: "IYR", name: "iShares U.S. Real Estate ETF", category: "Real Estate", assetClass: "Equity", expectedReturn: 0.08, volatility: 0.20 },

  // Dividend
  { symbol: "VYM", name: "Vanguard High Dividend Yield ETF", category: "Dividend", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.15 },
  { symbol: "SCHD", name: "Schwab U.S. Dividend Equity ETF", category: "Dividend", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.15 },
  { symbol: "DVY", name: "iShares Select Dividend ETF", category: "Dividend", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.16 },
  { symbol: "HDV", name: "iShares Core High Dividend ETF", category: "Dividend", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.16 },
  { symbol: "DGRO", name: "iShares Core Dividend Growth ETF", category: "Dividend", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.16 },

  // Growth
  { symbol: "VUG", name: "Vanguard Growth ETF", category: "Growth", assetClass: "Equity", expectedReturn: 0.12, volatility: 0.19 },
  { symbol: "IVW", name: "iShares S&P 500 Growth ETF", category: "Growth", assetClass: "Equity", expectedReturn: 0.12, volatility: 0.19 },
  { symbol: "SCHG", name: "Schwab U.S. Large-Cap Growth ETF", category: "Growth", assetClass: "Equity", expectedReturn: 0.12, volatility: 0.19 },

  // Value
  { symbol: "VTV", name: "Vanguard Value ETF", category: "Value", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.16 },
  { symbol: "IVE", name: "iShares S&P 500 Value ETF", category: "Value", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.16 },
  { symbol: "SCHV", name: "Schwab U.S. Large-Cap Value ETF", category: "Value", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.16 },

  // Factor - Momentum
  { symbol: "MTUM", name: "iShares MSCI USA Momentum Factor ETF", category: "Factor", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.18 },
  { symbol: "PDP", name: "Invesco DWA Momentum ETF", category: "Factor", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.19 },

  // Factor - Quality
  { symbol: "QUAL", name: "iShares MSCI USA Quality Factor ETF", category: "Factor", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.16 },
  { symbol: "SPHQ", name: "Invesco S&P 500 Quality ETF", category: "Factor", assetClass: "Equity", expectedReturn: 0.11, volatility: 0.16 },

  // Factor - Low Volatility
  { symbol: "USMV", name: "iShares MSCI USA Min Vol Factor ETF", category: "Factor", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.12 },
  { symbol: "SPLV", name: "Invesco S&P 500 Low Volatility ETF", category: "Factor", assetClass: "Equity", expectedReturn: 0.09, volatility: 0.12 },

  // ESG
  { symbol: "ESGU", name: "iShares MSCI USA ESG Select ETF", category: "ESG", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.17 },
  { symbol: "VSGX", name: "Vanguard ESG U.S. Stock ETF", category: "ESG", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.17 },
  { symbol: "DSI", name: "iShares MSCI KLD 400 Social ETF", category: "ESG", assetClass: "Equity", expectedReturn: 0.10, volatility: 0.17 },

  // Balanced
  { symbol: "AOR", name: "iShares Core Growth Allocation ETF", category: "Balanced", assetClass: "Mixed", expectedReturn: 0.07, volatility: 0.10 },
  { symbol: "AOM", name: "iShares Core Moderate Allocation ETF", category: "Balanced", assetClass: "Mixed", expectedReturn: 0.06, volatility: 0.08 },
  { symbol: "AOK", name: "iShares Core Conservative Allocation ETF", category: "Balanced", assetClass: "Mixed", expectedReturn: 0.05, volatility: 0.06 },

  // Bitcoin
  { symbol: "BITO", name: "ProShares Bitcoin Strategy ETF", category: "Crypto", assetClass: "Alternative", expectedReturn: 0.15, volatility: 0.70 },

  // Leveraged (for advanced users)
  { symbol: "UPRO", name: "ProShares UltraPro S&P500", category: "Leveraged", assetClass: "Equity", expectedReturn: 0.30, volatility: 0.48 },
  { symbol: "TQQQ", name: "ProShares UltraPro QQQ", category: "Leveraged", assetClass: "Equity", expectedReturn: 0.39, volatility: 0.66 },

  // International Bonds
  { symbol: "BNDX", name: "Vanguard Total International Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.08 },
  { symbol: "IAGG", name: "iShares Core International Aggregate Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.08 },

  // TIPS
  { symbol: "TIP", name: "iShares TIPS Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.03, volatility: 0.07 },
  { symbol: "VTIP", name: "Vanguard Short-Term Inflation-Protected Securities ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.02, volatility: 0.03 },

  // Emerging Market Bonds
  { symbol: "EMB", name: "iShares J.P. Morgan USD Emerging Markets Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.05, volatility: 0.12 },
  { symbol: "VWOB", name: "Vanguard Emerging Markets Government Bond ETF", category: "Bonds", assetClass: "Fixed Income", expectedReturn: 0.05, volatility: 0.12 },
];

/**
 * Generate mock historical price data for an ETF
 * Uses random walk with drift to simulate realistic price movements
 */
function generateHistoricalPrices(
  symbol: string,
  expectedReturn: number,
  volatility: number,
  days: number = 365
): Array<{ timestamp: string; open: number; high: number; low: number; close: number; volume: number }> {
  const prices: Array<{ timestamp: string; open: number; high: number; low: number; close: number; volume: number }> = [];
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  let price = 100; // Start at $100

  // Daily return parameters
  const dailyReturn = expectedReturn / 252; // Annualized to daily
  const dailyVol = volatility / Math.sqrt(252); // Annualized to daily

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    // Random walk with drift
    const randomReturn = dailyReturn + dailyVol * (Math.random() * 2 - 1);
    const open = price;
    const close = price * (1 + randomReturn);

    // Intraday high/low
    const dailyRange = Math.abs(close - open) * 1.5;
    const high = Math.max(open, close) + dailyRange * Math.random();
    const low = Math.min(open, close) - dailyRange * Math.random();

    // Volume (random between 1M and 10M)
    const volume = Math.floor(1000000 + Math.random() * 9000000);

    prices.push({
      timestamp: date.toISOString(),
      open,
      high,
      low,
      close,
      volume,
    });

    price = close;
  }

  return prices;
}

async function seedAsset(etf: typeof etfs[0]) {
  const now = new Date().toISOString();

  // Calculate Sharpe ratio
  const riskFreeRate = 0.03;
  const sharpeRatio = etf.volatility > 0 ? (etf.expectedReturn - riskFreeRate) / etf.volatility : 0;

  // Seed asset metadata
  await dynamodb.send(
    new PutCommand({
      TableName: "portfolio-optimizer-dev-AssetsTableTable-baznawsn",
      Item: {
        PK: `ASSET#${etf.symbol}`,
        SK: "METADATA",
        symbol: etf.symbol,
        name: etf.name,
        category: etf.category,
        assetClass: etf.assetClass,
        currentImpliedVol30Day: etf.volatility,
        volatility7Day: etf.volatility * 0.95,
        volatility30Day: etf.volatility,
        volatility90Day: etf.volatility * 1.05,
        volatility1Year: etf.volatility * 1.1,
        volatilityLongTerm: etf.volatility,
        expectedReturn: etf.expectedReturn,
        sharpeRatio,
        tailRiskFactor: 2.0,
        maxDrawdown1Year: -etf.volatility * 2,
        maxDrawdown5Year: -etf.volatility * 3,
        correlationBreakdownRisk: 0.1,
        isActive: true,
        dataQuality: "MEDIUM",
        createdAt: now,
        updatedAt: now,
        lastUpdated: now,
      },
    })
  );

  console.log(`✓ Seeded ${etf.symbol} - ${etf.name}`);
}

async function seedHistoricalPrices(etf: typeof etfs[0]) {
  const prices = generateHistoricalPrices(etf.symbol, etf.expectedReturn, etf.volatility, 365);

  // Batch write in chunks of 25 (DynamoDB limit)
  const chunkSize = 25;
  for (let i = 0; i < prices.length; i += chunkSize) {
    const chunk = prices.slice(i, i + chunkSize);

    const putRequests = chunk.map((price) => ({
      PutRequest: {
        Item: {
          PK: `PRICE#${etf.symbol}`,
          SK: price.timestamp,
          symbol: etf.symbol,
          open: price.open,
          high: price.high,
          low: price.low,
          close: price.close,
          volume: price.volume,
          // TTL: 20 years from now
          expirationTime: Math.floor(Date.now() / 1000) + 20 * 365 * 24 * 60 * 60,
        },
      },
    }));

    await dynamodb.send(
      new BatchWriteCommand({
        RequestItems: {
          "portfolio-optimizer-dev-HistoricalPricesTableTable-mbrxhuee": putRequests,
        },
      })
    );
  }

  console.log(`  ✓ Added ${prices.length} historical prices for ${etf.symbol}`);
}

async function main() {
  console.log("🌱 Seeding database with 100 ETFs...\n");

  for (const etf of etfs) {
    await seedAsset(etf);
    await seedHistoricalPrices(etf);
  }

  console.log(`\n✅ Successfully seeded ${etfs.length} ETFs with historical data!`);
  console.log("\nYou can now test the API endpoints:");
  console.log("  GET /assets");
  console.log("  GET /assets/SPY");
  console.log("  GET /volatility/SPY");
  console.log("  POST /calculate/correlation");
  console.log("  POST /calculate/kelly");
}

main().catch((error) => {
  console.error("❌ Seeding failed:", error);
  process.exit(1);
});
