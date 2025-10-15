import {
  Chart,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  TimeScale,
  Title,
  Tooltip,
} from "chart.js";
import { createEffect, createSignal, onCleanup, Show } from "solid-js";
import "chart.js/auto";
import { Icon } from "./Icon";

// Register Chart.js components
Chart.register(LineController, LineElement, PointElement, LinearScale, TimeScale, Title, Tooltip, Legend);

interface VolatilityChartProps {
  symbol: string;
  historicalVol?: {
    "7day": number;
    "30day": number;
    "90day": number;
    "365day": number;
  };
}

type TimeRange = "7d" | "30d" | "90d" | "1y";

export function VolatilityChart(props: VolatilityChartProps) {
  const [timeRange, setTimeRange] = createSignal<TimeRange>("30d");
  let canvasRef: HTMLCanvasElement | undefined;
  let chartInstance: Chart | undefined;

  const getChartData = () => {
    if (!props.historicalVol) return null;

    const now = new Date();
    const ranges = {
      "7d": 7,
      "30d": 30,
      "90d": 90,
      "1y": 365,
    };

    const days = ranges[timeRange()];
    const data: { date: string; volatility: number }[] = [];

    // Generate simulated historical data based on the volatility values
    // In production, this would come from the API
    const currentVol =
      props.historicalVol[
        timeRange() === "7d" ? "7day" : timeRange() === "30d" ? "30day" : timeRange() === "90d" ? "90day" : "365day"
      ];

    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      // Add some variance to make it look realistic (±15% of current vol)
      const variance = (Math.random() - 0.5) * 0.3;
      const vol = currentVol * (1 + variance);

      data.push({
        date: date.toISOString().split("T")[0] || "",
        volatility: vol * 100, // Convert to percentage
      });
    }

    return data;
  };

  createEffect(() => {
    const data = getChartData();

    if (!canvasRef || !data) return;

    // Destroy existing chart
    if (chartInstance) {
      chartInstance.destroy();
    }

    // Create new chart
    const ctx = canvasRef.getContext("2d");
    if (!ctx) return;

    chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.map((d) => d.date),
        datasets: [
          {
            label: "Volatility (%)",
            data: data.map((d) => d.volatility),
            borderColor: "rgb(99, 102, 241)", // Indigo
            backgroundColor: "rgba(99, 102, 241, 0.1)",
            borderWidth: 2,
            fill: true,
            tension: 0.4, // Smooth curves
            pointRadius: 0,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: "index",
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: "rgba(15, 23, 42, 0.9)",
            padding: 12,
            titleColor: "#f1f5f9",
            bodyColor: "#e2e8f0",
            borderColor: "rgba(99, 102, 241, 0.5)",
            borderWidth: 1,
            displayColors: false,
            callbacks: {
              title: (items) => {
                return items[0]?.label || "";
              },
              label: (item) => {
                const value = item.parsed.y;
                return `Volatility: ${value?.toFixed(2) ?? "N/A"}%`;
              },
            },
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              maxTicksLimit: 6,
              color: "#94a3b8",
            },
          },
          y: {
            beginAtZero: true,
            grid: {
              color: "rgba(148, 163, 184, 0.1)",
            },
            ticks: {
              color: "#94a3b8",
              callback: (value) => `${value}%`,
            },
          },
        },
      },
    });
  });

  onCleanup(() => {
    if (chartInstance) {
      chartInstance.destroy();
    }
  });

  return (
    <div class="card p-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h3 class="text-lg font-semibold text-slate-900">Volatility History</h3>
          <p class="text-sm text-slate-500 mt-1">{props.symbol}</p>
        </div>

        <div class="flex gap-2">
          <button
            type="button"
            onClick={() => setTimeRange("7d")}
            class={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              timeRange() === "7d" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            7D
          </button>
          <button
            type="button"
            onClick={() => setTimeRange("30d")}
            class={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              timeRange() === "30d" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            30D
          </button>
          <button
            type="button"
            onClick={() => setTimeRange("90d")}
            class={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              timeRange() === "90d" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            90D
          </button>
          <button
            type="button"
            onClick={() => setTimeRange("1y")}
            class={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              timeRange() === "1y" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            1Y
          </button>
        </div>
      </div>

      <Show
        when={props.historicalVol}
        fallback={
          <div class="h-64 flex items-center justify-center text-slate-400">
            <div class="text-center">
              <Icon name="chart" size={12} class="mx-auto mb-4 opacity-30" />
              <p>No volatility data available</p>
            </div>
          </div>
        }
      >
        <div class="relative h-64">
          <canvas ref={canvasRef} />
        </div>

        <div class="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-200">
          <div class="text-center">
            <div class="text-xs font-medium text-slate-500 mb-1">7 Day</div>
            <div class="text-lg font-bold text-slate-900">
              {props.historicalVol?.["7day"] ? (props.historicalVol["7day"] * 100).toFixed(2) : "-"}%
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs font-medium text-slate-500 mb-1">30 Day</div>
            <div class="text-lg font-bold text-slate-900">
              {props.historicalVol?.["30day"] ? (props.historicalVol["30day"] * 100).toFixed(2) : "-"}%
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs font-medium text-slate-500 mb-1">90 Day</div>
            <div class="text-lg font-bold text-slate-900">
              {props.historicalVol?.["90day"] ? (props.historicalVol["90day"] * 100).toFixed(2) : "-"}%
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs font-medium text-slate-500 mb-1">1 Year</div>
            <div class="text-lg font-bold text-slate-900">
              {props.historicalVol?.["365day"] ? (props.historicalVol["365day"] * 100).toFixed(2) : "-"}%
            </div>
          </div>
        </div>
      </Show>
    </div>
  );
}
