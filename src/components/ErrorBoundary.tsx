import { type ParentComponent, ErrorBoundary as SolidErrorBoundary } from "solid-js";

export const ErrorBoundary: ParentComponent = (props) => (
  <SolidErrorBoundary
    fallback={(err, reset) => (
      <div class="mx-auto flex min-h-screen max-w-measure flex-col justify-center px-6 py-16">
        <p class="eyebrow">Error</p>
        <h1 class="mt-2 font-serif text-3xl">This page did not render</h1>
        <p class="mt-4 text-ink-muted">
          Something in the page threw before it finished. The research itself is unaffected — it lives in Markdown in
          the repository.
        </p>

        <div class="mt-6 flex flex-wrap gap-3">
          <button type="button" onClick={reset} class="control cursor-pointer font-medium">
            Try again
          </button>
          <button type="button" onClick={() => window.location.assign("/")} class="control cursor-pointer font-medium">
            Back to the start
          </button>
        </div>

        <details class="mt-8">
          <summary class="cursor-pointer text-sm text-ink-faint transition-colors hover:text-ink">Details</summary>
          <pre class="mt-2 overflow-x-auto border-l-2 border-rule-strong bg-sunken p-3 font-mono text-xs whitespace-pre-wrap">
            {err instanceof Error ? err.message : String(err)}
          </pre>
        </details>
      </div>
    )}
  >
    {props.children}
  </SolidErrorBoundary>
);
