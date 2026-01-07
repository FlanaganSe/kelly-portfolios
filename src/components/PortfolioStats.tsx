import type { JSX } from "solid-js";
import { Show } from "solid-js";
import type { PortfolioStats as PortfolioStatsType } from "~/types";

interface PortfolioStatsProps {
  stats: PortfolioStatsType | null;
}

export function PortfolioStats(props: PortfolioStatsProps): JSX.Element {
  return (
    <Show
      when={props.stats}
      fallback={
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Expected Return" value="--" />
          <StatCard label="Volatility" value="--" />
          <StatCard label="Sharpe Ratio" value="--" />
          <StatCard label="Leverage" value="--" />
        </div>
      }
    >
      {(stats) => (
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Expected Return"
            value={`${(stats().portfolioReturn * 100).toFixed(1)}%`}
            isPositive={stats().portfolioReturn > 0}
            subtext="Annual"
          />
          <StatCard
            label="Volatility"
            value={`${(stats().portfolioVolatility * 100).toFixed(1)}%`}
            isNeutral
            subtext="Annual Std Dev"
          />
          <StatCard
            label="Sharpe Ratio"
            value={stats().sharpeRatio.toFixed(2)}
            isPositive={stats().sharpeRatio > 1}
            isNeutral={stats().sharpeRatio >= 0.5 && stats().sharpeRatio <= 1}
            subtext={getSharpeLabel(stats().sharpeRatio)}
          />
          <StatCard
            label="Leverage"
            value={`${stats().totalLeverage.toFixed(2)}x`}
            isNeutral={stats().totalLeverage <= 1}
            isWarning={stats().totalLeverage > 1}
            subtext={getLeverageLabel(stats().totalLeverage)}
          />
        </div>
      )}
    </Show>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  subtext?: string;
  isPositive?: boolean;
  isNeutral?: boolean;
  isWarning?: boolean;
}

function StatCard(props: StatCardProps): JSX.Element {
  const valueColor = () => {
    if (props.isWarning) return "text-amber-400";
    if (props.isPositive) return "text-emerald-400";
    if (props.isNeutral) return "text-blue-400";
    return "text-white";
  };

  return (
    <div class="glass-panel p-4">
      <div class="text-xs text-slate-400 mb-1">{props.label}</div>
      <div class={`text-2xl font-bold ${valueColor()}`}>{props.value}</div>
      <Show when={props.subtext}>
        <div class="text-xs text-slate-500 mt-1">{props.subtext}</div>
      </Show>
    </div>
  );
}

function getSharpeLabel(sharpe: number): string {
  if (sharpe >= 2) return "Excellent";
  if (sharpe >= 1) return "Good";
  if (sharpe >= 0.5) return "Acceptable";
  if (sharpe >= 0) return "Poor";
  return "Negative";
}

function getLeverageLabel(leverage: number): string {
  if (leverage <= 1) return "No margin";
  if (leverage <= 1.5) return "Low margin";
  if (leverage <= 2) return "Moderate";
  return "High margin";
}
