import { createSignal, onCleanup } from "solid-js";
import type { OptimizationResult, PortfolioConfig, PriceHistory, WorkerRequest, WorkerResponse } from "~/types";

// Import the worker using Vite's worker syntax
import OptimizerWorker from "./optimizer.worker?worker";

export interface UseOptimizerReturn {
  optimize: (priceHistory: PriceHistory[], config: PortfolioConfig) => Promise<OptimizationResult>;
  isOptimizing: () => boolean;
  progress: () => number;
  error: () => string | null;
  cancel: () => void;
}

export function useOptimizer(): UseOptimizerReturn {
  const [isOptimizing, setIsOptimizing] = createSignal(false);
  const [progress, setProgress] = createSignal(0);
  const [error, setError] = createSignal<string | null>(null);

  let worker: Worker | null = null;
  let currentResolve: ((result: OptimizationResult) => void) | null = null;
  let currentReject: ((error: Error) => void) | null = null;

  // Initialize worker
  function getWorker(): Worker {
    if (!worker) {
      worker = new OptimizerWorker();
      worker.onmessage = handleWorkerMessage;
      worker.onerror = handleWorkerError;
    }
    return worker;
  }

  function handleWorkerMessage(event: MessageEvent<WorkerResponse>): void {
    const { type, payload } = event.data;

    switch (type) {
      case "result":
        setIsOptimizing(false);
        setProgress(100);
        if (currentResolve) {
          currentResolve(payload as OptimizationResult);
          currentResolve = null;
          currentReject = null;
        }
        break;

      case "error":
        setIsOptimizing(false);
        setError(payload as string);
        if (currentReject) {
          currentReject(new Error(payload as string));
          currentResolve = null;
          currentReject = null;
        }
        break;

      case "progress":
        setProgress(payload as number);
        break;
    }
  }

  function handleWorkerError(event: ErrorEvent): void {
    setIsOptimizing(false);
    setError(event.message);
    if (currentReject) {
      currentReject(new Error(event.message));
      currentResolve = null;
      currentReject = null;
    }
  }

  function optimize(priceHistory: PriceHistory[], config: PortfolioConfig): Promise<OptimizationResult> {
    return new Promise((resolve, reject) => {
      setIsOptimizing(true);
      setProgress(0);
      setError(null);

      currentResolve = resolve;
      currentReject = reject;

      const request: WorkerRequest = {
        type: "optimize",
        payload: { priceHistory, config },
      };

      getWorker().postMessage(request);
    });
  }

  function cancel(): void {
    if (worker) {
      worker.terminate();
      worker = null;
      setIsOptimizing(false);
      setProgress(0);
      if (currentReject) {
        currentReject(new Error("Optimization cancelled"));
        currentResolve = null;
        currentReject = null;
      }
    }
  }

  // Cleanup on unmount
  onCleanup(() => {
    if (worker) {
      worker.terminate();
      worker = null;
    }
  });

  return {
    optimize,
    isOptimizing,
    progress,
    error,
    cancel,
  };
}

// Fallback for when workers aren't available (SSR, etc.)
export function useOptimizerSync(): UseOptimizerReturn {
  const [isOptimizing, setIsOptimizing] = createSignal(false);
  const [progress, setProgress] = createSignal(0);
  const [error, setError] = createSignal<string | null>(null);

  async function optimize(priceHistory: PriceHistory[], config: PortfolioConfig): Promise<OptimizationResult> {
    setIsOptimizing(true);
    setProgress(0);
    setError(null);

    try {
      // Dynamic import to avoid bundling in the main thread unnecessarily
      const { runOptimization } = await import("~/core/solver/optimizer");
      setProgress(50);
      const result = runOptimization(priceHistory, config);
      setProgress(100);
      setIsOptimizing(false);
      return result;
    } catch (e) {
      const message = e instanceof Error ? e.message : "Unknown error";
      setError(message);
      setIsOptimizing(false);
      throw e;
    }
  }

  function cancel(): void {
    // Can't cancel synchronous execution
    setIsOptimizing(false);
  }

  return {
    optimize,
    isOptimizing,
    progress,
    error,
    cancel,
  };
}
