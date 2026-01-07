import type { ChartConfiguration } from "chart.js";
import { Chart, LinearScale, LineController, LineElement, PointElement, Tooltip } from "chart.js";
import type { JSX } from "solid-js";
import { createEffect, onCleanup, onMount } from "solid-js";
import type { EfficientFrontierPoint, PortfolioStats } from "~/types";

// Register Chart.js components
Chart.register(LineController, PointElement, LineElement, LinearScale, Tooltip);

interface EfficientFrontierChartProps {
  frontier: EfficientFrontierPoint[];
  currentPortfolio?: PortfolioStats | null;
}

export function EfficientFrontierChart(props: EfficientFrontierChartProps): JSX.Element {
  let canvasRef: HTMLCanvasElement | undefined;
  let chartInstance: Chart | null = null;

  onMount(() => {
    if (!canvasRef) return;

    const ctx = canvasRef.getContext("2d");
    if (!ctx) return;

    // Sort frontier points by volatility
    const sortedFrontier = [...props.frontier].sort((a, b) => a.x - b.x);

    const frontierData = sortedFrontier.map((p) => ({
      x: p.x * 100, // Convert to percentage
      y: p.y * 100,
    }));

    const datasets: ChartConfiguration<"line">["data"]["datasets"] = [
      {
        label: "Efficient Frontier",
        data: frontierData,
        borderColor: "rgba(99, 102, 241, 0.8)",
        backgroundColor: "rgba(99, 102, 241, 0.1)",
        fill: false,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: "rgba(99, 102, 241, 1)",
        pointBorderColor: "rgba(255, 255, 255, 0.5)",
        pointBorderWidth: 1,
      },
    ];

    // Add current portfolio point if available
    if (props.currentPortfolio) {
      datasets.push({
        label: "Current Portfolio",
        data: [
          {
            x: props.currentPortfolio.portfolioVolatility * 100,
            y: props.currentPortfolio.portfolioReturn * 100,
          },
        ],
        borderColor: "rgba(34, 197, 94, 1)",
        backgroundColor: "rgba(34, 197, 94, 1)",
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: "star",
      });
    }

    const config: ChartConfiguration<"line"> = {
      type: "line",
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: "linear",
            title: {
              display: true,
              text: "Volatility (Risk) %",
              color: "#94a3b8",
            },
            ticks: { color: "#64748b" },
            grid: { color: "rgba(255, 255, 255, 0.05)" },
          },
          y: {
            type: "linear",
            title: {
              display: true,
              text: "Expected Return %",
              color: "#94a3b8",
            },
            ticks: { color: "#64748b" },
            grid: { color: "rgba(255, 255, 255, 0.05)" },
          },
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              color: "#94a3b8",
              usePointStyle: true,
              padding: 16,
            },
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
                const point = context.raw as { x: number; y: number };
                return [`Return: ${point.y.toFixed(1)}%`, `Risk: ${point.x.toFixed(1)}%`];
              },
            },
          },
        },
        interaction: {
          intersect: false,
          mode: "nearest",
        },
      },
    };

    chartInstance = new Chart(ctx, config);
  });

  // Update chart when data changes
  createEffect(() => {
    if (!chartInstance) return;

    const sortedFrontier = [...props.frontier].sort((a, b) => a.x - b.x);

    const frontierData = sortedFrontier.map((p) => ({
      x: p.x * 100,
      y: p.y * 100,
    }));

    chartInstance.data.datasets[0]!.data = frontierData;

    // Update current portfolio point
    if (props.currentPortfolio && chartInstance.data.datasets[1]) {
      chartInstance.data.datasets[1].data = [
        {
          x: props.currentPortfolio.portfolioVolatility * 100,
          y: props.currentPortfolio.portfolioReturn * 100,
        },
      ];
    } else if (props.currentPortfolio) {
      chartInstance.data.datasets.push({
        label: "Current Portfolio",
        data: [
          {
            x: props.currentPortfolio.portfolioVolatility * 100,
            y: props.currentPortfolio.portfolioReturn * 100,
          },
        ],
        borderColor: "rgba(34, 197, 94, 1)",
        backgroundColor: "rgba(34, 197, 94, 1)",
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: "star" as const,
      });
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
    <div class="h-72">
      <canvas ref={canvasRef} />
    </div>
  );
}
