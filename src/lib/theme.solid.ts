/** The Solid wrapper around the framework-free theme state in `./theme`. */

import { createSignal, onCleanup, onMount } from "solid-js";
import { applyTheme, nextTheme, readStoredTheme, resolveTheme, type ThemeSetting } from "~/lib/theme";

/** Reactive theme setting plus the resolved light/dark it produces. */
export function useTheme() {
  const [setting, setSetting] = createSignal<ThemeSetting>("system");
  const [prefersDark, setPrefersDark] = createSignal(false);

  onMount(() => {
    setSetting(readStoredTheme());

    const query = window.matchMedia("(prefers-color-scheme: dark)");
    setPrefersDark(query.matches);
    const onChange = (event: MediaQueryListEvent) => setPrefersDark(event.matches);
    query.addEventListener("change", onChange);
    onCleanup(() => query.removeEventListener("change", onChange));
  });

  const set = (next: ThemeSetting) => {
    setSetting(next);
    applyTheme(next);
  };

  return {
    setting,
    resolved: () => resolveTheme(setting(), prefersDark()),
    set,
    cycle: () => set(nextTheme(setting())),
  };
}
