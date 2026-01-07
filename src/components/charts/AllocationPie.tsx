import type { ChartConfiguration } from "chart.js";
import { ArcElement, Chart, DoughnutController, Legend, Tooltip } from "chart.js";
import type { JSX } from "solid-js";
import { createEffect, For, onCleanup, onMount } from "solid-js";

// Register Chart.js components
Chart.register(DoughnutController, ArcElement, Tooltip, Legend);

interface AllocationPieProps {
  weights: Record<string, number>;
}

// Color palette for assets
const ASSET_COLORS: Record<string, string> = {
  SPY: "#3B82F6", // Blue
  QQQ: "#8B5CF6", // Purple
  TLT: "#10B981", // Green
  GLD: "#F59E0B", // Amber
  VNQ: "#EC4899", // Pink
  BTC: "#F97316", // Orange
  ETH: "#6366F1", // Indigo
  HYG: "#14B8A6", // Teal
  LQD: "#06B6D4", // Cyan
  CASH: "#6B7280", // Gray
};

function getAssetColor(ticker: string, index: number): string {
  return ASSET_COLORS[ticker] ?? `hsl(${(index * 137.5) % 360}, 70%, 50%)`;
}

export function AllocationPie(props: AllocationPieProps): JSX.Element {
  let canvasRef: HTMLCanvasElement | undefined;
  let chartInstance: Chart<"doughnut"> | null = null;

  const sortedWeights = () => {
    return Object.entries(props.weights)
      .filter(([, w]) => w > 0.001)
      .sort((a, b) => b[1] - a[1]);
  };

  onMount(() => {
    if (!canvasRef) return;

    const ctx = canvasRef.getContext("2d");
    if (!ctx) return;

    const entries = sortedWeights();
    const labels = entries.map(([ticker]) => ticker);
    const data = entries.map(([, weight]) => weight * 100);
    const colors = entries.map(([ticker], i) => getAssetColor(ticker, i));

    const config: ChartConfiguration<"doughnut"> = {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data,
            backgroundColor: colors,
            borderColor: "rgba(15, 23, 42, 0.8)",
            borderWidth: 2,
            hoverOffset: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "65%",
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: "rgba(15, 23, 42, 0.95)",
            titleColor: "#fff",
            bodyColor: "#cbd5e1",
            borderColor: "rgba(255, 255, 255, 0.1)",
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
            callbacks: {
              label: (context) => {
                const value = context.parsed;
                return ` ${context.label}: ${value.toFixed(1)}%`;
              },
            },
          },
        },
      },
    };

    chartInstance = new Chart(ctx, config);
  });

  // Update chart when weights change
  createEffect(() => {
    if (!chartInstance) return;

    const entries = sortedWeights();
    const labels = entries.map(([ticker]) => ticker);
    const data = entries.map(([, weight]) => weight * 100);
    const colors = entries.map(([ticker], i) => getAssetColor(ticker, i));

    chartInstance.data.labels = labels;
    const dataset = chartInstance.data.datasets[0];
    if (dataset) {
      dataset.data = data;
      dataset.backgroundColor = colors;
    }
    chartInstance.update("none");
  });

  onCleanup(() => {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  });

  return (
    <div class="relative">
      <div class="h-64">
        <canvas ref={canvasRef} />
      </div>

      {/* Legend */}
      <div class="mt-4 grid grid-cols-2 gap-2">
        <For each={sortedWeights()}>
          {([ticker, weight], index) => (
            <div class="flex items-center gap-2 text-sm">
              <div
                class="w-3 h-3 rounded-sm flex-shrink-0"
                style={{ "background-color": getAssetColor(ticker, index()) }}
              />
              <span class="text-slate-300 truncate">{ticker}</span>
              <span class="text-white font-medium ml-auto">{(weight * 100).toFixed(1)}%</span>
            </div>
          )}
        </For>
      </div>
    </div>
  );
}
