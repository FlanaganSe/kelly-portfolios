// Web Worker for portfolio optimization
// This runs heavy computations off the main thread

import { runOptimization } from "~/core/solver/optimizer";
import type { OptimizationResult, WorkerRequest, WorkerResponse } from "~/types";

// Handle messages from the main thread
self.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const { type, payload } = event.data;

  if (type === "optimize") {
    try {
      // Send progress update
      postProgressMessage(10);

      const { priceHistory, config } = payload;

      // Validate inputs
      if (!priceHistory || priceHistory.length === 0) {
        throw new Error("No price history provided");
      }

      if (!config.assets || config.assets.length === 0) {
        throw new Error("No assets selected");
      }

      postProgressMessage(30);

      // Run the optimization
      const result = runOptimization(priceHistory, config);

      postProgressMessage(90);

      // Send the result
      postResultMessage(result);

      postProgressMessage(100);
    } catch (error) {
      postErrorMessage(error instanceof Error ? error.message : "Unknown error occurred");
    }
  }
};

function postResultMessage(result: OptimizationResult): void {
  const response: WorkerResponse = {
    type: "result",
    payload: result,
  };
  self.postMessage(response);
}

function postErrorMessage(message: string): void {
  const response: WorkerResponse = {
    type: "error",
    payload: message,
  };
  self.postMessage(response);
}

function postProgressMessage(progress: number): void {
  const response: WorkerResponse = {
    type: "progress",
    payload: progress,
  };
  self.postMessage(response);
}

// Export for type checking
export type { WorkerRequest, WorkerResponse };
