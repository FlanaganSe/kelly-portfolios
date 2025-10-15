import { createSignal, For, Show } from "solid-js";

interface CorrelationMatrixProps {
  symbols: string[];
  matrix: number[][];
  dataQuality?: "HIGH" | "MEDIUM" | "LOW";
}

export function CorrelationMatrix(props: CorrelationMatrixProps) {
  const [hoveredCell, setHoveredCell] = createSignal<{ row: number; col: number } | null>(null);

  /**
   * Get color intensity level (0-4)
   */
  const getIntensityLevel = (intensity: number): number => {
    if (intensity > 0.7) return 4;
    if (intensity > 0.5) return 3;
    if (intensity > 0.3) return 2;
    if (intensity > 0.1) return 1;
    return 0;
  };

  /**
   * Get color for correlation value
   * Red for negative, white for neutral, blue for positive
   */
  const getCorrelationColor = (value: number): string => {
    if (value === 1) {
      return "bg-slate-200 text-slate-700";
    }

    const intensity = Math.min(Math.abs(value), 1);
    const level = getIntensityLevel(intensity);
    const isPositive = value > 0;

    const colorMap = [
      { positive: "bg-blue-100 text-slate-900", negative: "bg-red-100 text-slate-900" },
      { positive: "bg-blue-300 text-slate-900", negative: "bg-red-300 text-slate-900" },
      { positive: "bg-blue-400 text-white", negative: "bg-red-400 text-white" },
      { positive: "bg-blue-500 text-white", negative: "bg-red-500 text-white" },
      { positive: "bg-blue-600 text-white", negative: "bg-red-600 text-white" },
    ];

    const colors = colorMap[level];
    if (!colors) return "bg-slate-100 text-slate-900";
    return isPositive ? colors.positive : colors.negative;
  };

  /**
   * Export matrix to CSV
   */
  const exportToCSV = () => {
    const headers = ["", ...props.symbols].join(",");
    const rows = props.matrix.map((row, i) => {
      return [props.symbols[i], ...row.map((v) => v.toFixed(4))].join(",");
    });

    const csv = [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `correlation-matrix-${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const hovered = hoveredCell();
  const isRowHighlighted = (row: number) => hovered?.row === row || hovered?.col === row;
  const isColHighlighted = (col: number) => hovered?.row === col || hovered?.col === col;

  return (
    <div class="card p-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h3 class="text-lg font-semibold text-slate-900">Correlation Matrix</h3>
          <p class="text-sm text-slate-500 mt-1">
            Correlation between {props.symbols.length} assets
            <Show when={props.dataQuality}>
              {" • "}
              <span
                class={
                  props.dataQuality === "HIGH"
                    ? "text-emerald-600"
                    : props.dataQuality === "MEDIUM"
                      ? "text-amber-600"
                      : "text-red-600"
                }
              >
                {props.dataQuality} quality
              </span>
            </Show>
          </p>
        </div>

        <button
          type="button"
          onClick={exportToCSV}
          class="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
        >
          Export CSV
        </button>
      </div>

      <Show
        when={props.matrix.length > 0}
        fallback={
          <div class="h-64 flex items-center justify-center text-slate-400">
            <div class="text-center">
              <p>No correlation data available</p>
              <p class="text-sm mt-2">Add more assets to calculate correlations</p>
            </div>
          </div>
        }
      >
        <div class="overflow-x-auto">
          <table class="w-full border-collapse">
            <thead>
              <tr>
                <th class="sticky left-0 z-10 bg-white p-3 text-left text-sm font-semibold text-slate-900 border-b-2 border-slate-300" />
                <For each={props.symbols}>
                  {(symbol, colIndex) => (
                    <th
                      class={`p-3 text-center text-sm font-semibold border-b-2 border-slate-300 transition-colors ${
                        isColHighlighted(colIndex()) ? "bg-indigo-100 text-indigo-900" : "text-slate-900 bg-white"
                      }`}
                    >
                      {symbol}
                    </th>
                  )}
                </For>
              </tr>
            </thead>
            <tbody>
              <For each={props.matrix}>
                {(row, rowIndex) => (
                  <tr>
                    <td
                      class={`sticky left-0 z-10 bg-white p-3 text-left text-sm font-semibold border-r-2 border-slate-300 transition-colors ${
                        isRowHighlighted(rowIndex()) ? "bg-indigo-100 text-indigo-900" : "text-slate-900"
                      }`}
                    >
                      {props.symbols[rowIndex()]}
                    </td>
                    <For each={row}>
                      {(value, colIndex) => (
                        <td
                          class={`p-0 border border-slate-200 transition-all cursor-pointer ${
                            hoveredCell()?.row === rowIndex() && hoveredCell()?.col === colIndex()
                              ? "ring-2 ring-indigo-500 ring-inset scale-105 z-20 relative"
                              : ""
                          }`}
                          onMouseEnter={() => setHoveredCell({ row: rowIndex(), col: colIndex() })}
                          onMouseLeave={() => setHoveredCell(null)}
                        >
                          <div
                            class={`w-full h-full min-w-[60px] min-h-[60px] flex items-center justify-center text-xs font-mono font-semibold transition-colors ${getCorrelationColor(value)}`}
                          >
                            {value.toFixed(2)}
                          </div>
                        </td>
                      )}
                    </For>
                  </tr>
                )}
              </For>
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div class="mt-6 flex items-center justify-center gap-8 text-sm">
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-red-600 rounded" />
            <span class="text-slate-600">Negative Correlation</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-white border-2 border-slate-300 rounded" />
            <span class="text-slate-600">No Correlation</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-blue-600 rounded" />
            <span class="text-slate-600">Positive Correlation</span>
          </div>
        </div>

        {/* Hover Info */}
        <Show when={hoveredCell()}>
          {(cell) => {
            const row = cell().row;
            const col = cell().col;
            const value = props.matrix[row]?.[col];
            const symbol1 = props.symbols[row];
            const symbol2 = props.symbols[col];

            if (value === undefined) return null;

            return (
              <div class="mt-4 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <p class="text-sm font-medium text-indigo-900">
                  Correlation between <span class="font-bold">{symbol1}</span> and{" "}
                  <span class="font-bold">{symbol2}</span>
                </p>
                <p class="text-lg font-bold text-indigo-600 mt-1">{value.toFixed(4)}</p>
                <p class="text-xs text-indigo-700 mt-2">
                  {value === 1
                    ? "Perfect correlation (same asset)"
                    : value > 0.7
                      ? "Strong positive correlation - assets move together"
                      : value > 0.3
                        ? "Moderate positive correlation"
                        : value > -0.3
                          ? "Weak or no correlation"
                          : value > -0.7
                            ? "Moderate negative correlation"
                            : "Strong negative correlation - assets move in opposite directions"}
                </p>
              </div>
            );
          }}
        </Show>
      </Show>
    </div>
  );
}
