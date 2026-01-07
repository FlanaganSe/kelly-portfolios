import type { JSX } from "solid-js";

interface DashboardLayoutProps {
  sidebar: JSX.Element;
  children: JSX.Element;
}

export function DashboardLayout(props: DashboardLayoutProps): JSX.Element {
  return (
    <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Background decoration */}
      <div class="fixed inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl" />
        <div class="absolute top-1/2 -left-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl" />
        <div class="absolute -bottom-40 right-1/3 w-80 h-80 bg-emerald-500/20 rounded-full blur-3xl" />
      </div>

      {/* Content */}
      <div class="relative flex min-h-screen">
        {/* Sidebar */}
        <aside class="w-80 flex-shrink-0 border-r border-white/10">
          <div class="sticky top-0 h-screen overflow-y-auto p-4">{props.sidebar}</div>
        </aside>

        {/* Main content */}
        <main class="flex-1 p-6 overflow-y-auto">
          <div class="max-w-6xl mx-auto">{props.children}</div>
        </main>
      </div>
    </div>
  );
}
