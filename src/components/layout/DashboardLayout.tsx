import type { JSX } from "solid-js";
import { createSignal, Show } from "solid-js";

interface DashboardLayoutProps {
  sidebar: JSX.Element;
  children: JSX.Element;
}

export function DashboardLayout(props: DashboardLayoutProps): JSX.Element {
  const [isSidebarOpen, setIsSidebarOpen] = createSignal(false);

  return (
    <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Background decoration */}
      <div class="fixed inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl" />
        <div class="absolute top-1/2 -left-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl" />
        <div class="absolute -bottom-40 right-1/3 w-80 h-80 bg-emerald-500/20 rounded-full blur-3xl" />
      </div>

      {/* Mobile Header */}
      <div class="lg:hidden fixed top-0 left-0 right-0 z-40 glass-panel border-b border-white/10 px-4 py-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsSidebarOpen(true)}
          class="p-2 rounded-lg hover:bg-white/10 text-white"
          aria-label="Open menu"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 class="text-lg font-bold text-white">Portfolio Optimizer</h1>
        <div class="w-10" />
      </div>

      {/* Mobile Sidebar Overlay */}
      <Show when={isSidebarOpen()}>
        <div
          class="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        />
      </Show>

      {/* Content */}
      <div class="relative flex min-h-screen">
        {/* Sidebar - Desktop: static, Mobile: slide-in */}
        <aside
          class={`fixed lg:static inset-y-0 left-0 z-50 w-80 flex-shrink-0 border-r border-white/10
                  transform transition-transform duration-300 ease-in-out lg:translate-x-0 bg-slate-900/95 lg:bg-transparent
                  ${isSidebarOpen() ? "translate-x-0" : "-translate-x-full"}`}
        >
          {/* Mobile close button */}
          <div class="lg:hidden absolute top-3 right-3">
            <button
              type="button"
              onClick={() => setIsSidebarOpen(false)}
              class="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white"
              aria-label="Close menu"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="sticky top-0 h-screen overflow-y-auto p-4">{props.sidebar}</div>
        </aside>

        {/* Main content */}
        <main class="flex-1 p-4 lg:p-6 overflow-y-auto pt-16 lg:pt-6">
          <div class="max-w-6xl mx-auto">{props.children}</div>
        </main>
      </div>
    </div>
  );
}
