import { type ParentComponent, ErrorBoundary as SolidErrorBoundary } from "solid-js";
import { Icon } from "~/components/Icon";

export const ErrorBoundary: ParentComponent = (props) => {
  return (
    <SolidErrorBoundary
      fallback={(err, _reset) => (
        <div class="min-h-screen bg-slate-50 flex items-center justify-center p-6">
          <div class="max-w-md w-full">
            <div class="bg-white border border-red-200 rounded-2xl p-8 shadow-lg">
              <div class="flex items-center justify-center mb-6">
                <div class="w-16 h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Icon name="error" size={8} class="text-white" aria-label="Error" />
                </div>
              </div>
              <h2 class="text-2xl font-bold text-slate-900 text-center mb-4">Something went wrong</h2>
              <p class="text-slate-600 text-center mb-6">
                We encountered an unexpected error. Please refresh the page to try again.
              </p>
              <div class="flex justify-center">
                <button type="button" onClick={() => window.location.reload()} class="btn-primary text-lg px-6 py-3">
                  Refresh Page
                </button>
              </div>
              <details class="mt-6">
                <summary class="cursor-pointer text-sm text-slate-500 hover:text-slate-700">Error Details</summary>
                <pre class="mt-2 text-xs text-red-600 bg-red-50 p-3 rounded-lg overflow-auto">{err.message}</pre>
              </details>
            </div>
          </div>
        </div>
      )}
    >
      {props.children}
    </SolidErrorBoundary>
  );
};
