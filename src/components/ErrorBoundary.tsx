import { Component, type ComponentChildren } from "preact";
import { Icon } from "~/components/Icon";

interface Props {
  children: ComponentChildren;
  fallback?: ComponentChildren;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
            <div className="max-w-md w-full">
              <div className="bg-white border border-red-200 rounded-2xl p-8 shadow-lg">
                <div className="flex items-center justify-center mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg">
                    <Icon name="error" size={8} className="text-white" aria-label="Error" />
                  </div>
                </div>
                <h2 className="text-2xl font-bold text-slate-900 text-center mb-4">Something went wrong</h2>
                <p className="text-slate-600 text-center mb-6">
                  We encountered an unexpected error. Please refresh the page to try again.
                </p>
                <div className="flex justify-center">
                  <button
                    type="button"
                    onClick={() => window.location.reload()}
                    className="btn-primary text-lg px-6 py-3"
                  >
                    Refresh Page
                  </button>
                </div>
                {this.state.error && (
                  <details className="mt-6">
                    <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-700">
                      Error Details
                    </summary>
                    <pre className="mt-2 text-xs text-red-600 bg-red-50 p-3 rounded-lg overflow-auto">
                      {this.state.error.message}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
