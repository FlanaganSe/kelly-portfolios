import type { StressScenario } from "~/types";

// Historical crisis scenarios with approximate asset returns
export const STRESS_SCENARIOS: StressScenario[] = [
  {
    name: "2008 Financial Crisis",
    description:
      "The Global Financial Crisis caused by the subprime mortgage collapse. Peak-to-trough drawdown period.",
    impacts: {
      SPY: -0.55, // S&P 500 fell ~55%
      QQQ: -0.52, // Nasdaq fell ~52%
      TLT: 0.33, // Long treasuries rallied ~33% (flight to safety)
      GLD: 0.05, // Gold was mixed, slight positive
      VNQ: -0.68, // REITs were devastated
      BTC: 0, // Bitcoin didn't exist yet
      ETH: 0, // Ethereum didn't exist yet
      HYG: -0.25, // High yield bonds fell significantly
      LQD: -0.08, // Investment grade bonds fell moderately
      CASH: 0.02, // Cash returned ~2% (fed funds rate)
    },
  },
  {
    name: "2020 Covid Crash",
    description: "The rapid market decline in Feb-March 2020 due to COVID-19 pandemic fears.",
    impacts: {
      SPY: -0.34, // S&P 500 fell ~34%
      QQQ: -0.28, // Nasdaq fell ~28%
      TLT: 0.22, // Treasuries rallied as Fed cut rates
      GLD: -0.03, // Gold initially sold off in liquidity crunch
      VNQ: -0.42, // REITs hit hard
      BTC: -0.38, // Bitcoin crashed with everything
      ETH: -0.45, // Ethereum crashed harder
      HYG: -0.2, // High yield spreads widened
      LQD: -0.15, // Corp bonds fell on credit fears
      CASH: 0.001, // Near-zero rates
    },
  },
  {
    name: "2022 Rate Hike Cycle",
    description: "The Fed's aggressive rate hiking cycle to combat inflation caused bond and equity losses.",
    impacts: {
      SPY: -0.25, // S&P 500 fell ~25%
      QQQ: -0.35, // Nasdaq fell ~35% (growth stocks hit hard)
      TLT: -0.4, // Long bonds crushed by rising rates
      GLD: -0.05, // Gold fell modestly
      VNQ: -0.3, // REITs fell with rates rising
      BTC: -0.65, // Bitcoin collapsed
      ETH: -0.68, // Ethereum collapsed
      HYG: -0.15, // High yield fell
      LQD: -0.2, // Corp bonds fell significantly
      CASH: 0.04, // Cash finally earned something
    },
  },
  {
    name: "Dot-Com Crash (2000-2002)",
    description: "The bursting of the tech bubble. Extended bear market in technology stocks.",
    impacts: {
      SPY: -0.49, // S&P 500 fell ~49%
      QQQ: -0.83, // Nasdaq fell ~83%
      TLT: 0.25, // Treasuries did well
      GLD: -0.1, // Gold was weak during this period
      VNQ: 0.15, // REITs actually did okay
      BTC: 0, // Didn't exist
      ETH: 0, // Didn't exist
      HYG: -0.15, // High yield suffered
      LQD: 0.05, // IG bonds held up
      CASH: 0.05, // Cash returned ~5%
    },
  },
  {
    name: "Black Monday (1987)",
    description: "The single-day crash of October 19, 1987. Markets fell 22% in one day.",
    impacts: {
      SPY: -0.34, // Including the period around Black Monday
      QQQ: -0.3, // Tech wasn't dominant yet
      TLT: 0.1, // Flight to safety
      GLD: 0.05, // Gold benefited slightly
      VNQ: -0.2, // Real estate fell
      BTC: 0, // Didn't exist
      ETH: 0, // Didn't exist
      HYG: -0.1, // Junk bonds fell
      LQD: 0.02, // IG bonds flat
      CASH: 0.06, // Cash returned ~6%
    },
  },
];

// Calculate portfolio impact under a scenario
export function calculateScenarioImpact(weights: Record<string, number>, scenario: StressScenario): number {
  let totalImpact = 0;

  for (const [ticker, weight] of Object.entries(weights)) {
    const impact = scenario.impacts[ticker] ?? 0;
    totalImpact += weight * impact;
  }

  return totalImpact;
}
