/**
 * Theme state. Three settings, not two.
 *
 * `system` is the absence of a `data-theme` attribute, which is what the CSS in
 * `styles.css` treats as "follow `prefers-color-scheme`". Choosing light or dark
 * stamps the attribute and wins over the media query in both directions.
 *
 * Nothing in this module imports a framework, so the Astro shell's inline toggle and
 * any island can share one implementation of the cycle.
 */

export const THEME_SETTINGS = ["system", "light", "dark"] as const;

export type ThemeSetting = (typeof THEME_SETTINGS)[number];

const STORAGE_KEY = "pe-theme";

export function isThemeSetting(value: unknown): value is ThemeSetting {
  return typeof value === "string" && (THEME_SETTINGS as readonly string[]).includes(value);
}

/** What is stored, or `system` when nothing usable is. */
export function readStoredTheme(): ThemeSetting {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return isThemeSetting(stored) ? stored : "system";
  } catch {
    return "system";
  }
}

/** The next setting in the cycle: system to light to dark and back. */
export function nextTheme(current: ThemeSetting): ThemeSetting {
  const index = THEME_SETTINGS.indexOf(current);
  return THEME_SETTINGS[(index + 1) % THEME_SETTINGS.length] ?? "system";
}

/** The theme actually rendered, once the system preference is resolved. */
export function resolveTheme(setting: ThemeSetting, prefersDark: boolean): "light" | "dark" {
  if (setting !== "system") return setting;
  return prefersDark ? "dark" : "light";
}

/** Stamps the attribute and stores the choice. Safe to call before hydration. */
export function applyTheme(setting: ThemeSetting): void {
  const root = document.documentElement;
  if (setting === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", setting);
  }
  try {
    if (setting === "system") localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, setting);
  } catch {
    // A blocked storage API costs persistence, not the toggle.
  }
}
