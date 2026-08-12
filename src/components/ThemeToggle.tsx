import { type Component, Match, Switch } from "solid-js";
import { nextTheme, type ThemeSetting, useTheme } from "~/lib/theme";

const settingLabel: Record<ThemeSetting, string> = {
  system: "match the system",
  light: "light",
  dark: "dark",
};

/** Cycles system, light, dark. Persisted in `localStorage`. */
export const ThemeToggle: Component<{ class?: string }> = (props) => {
  const theme = useTheme();

  return (
    <button
      type="button"
      onClick={theme.cycle}
      title={`Theme: ${settingLabel[theme.setting()]}`}
      aria-label={`Theme is set to ${settingLabel[theme.setting()]}. Switch to ${settingLabel[nextTheme(theme.setting())]}.`}
      class={`inline-flex h-8 w-8 items-center justify-center rounded-[3px] border border-rule text-ink-muted transition-colors hover:border-rule-strong hover:text-ink ${props.class ?? ""}`}
    >
      <Switch>
        <Match when={theme.setting() === "light"}>
          <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor">
            <circle cx="8" cy="8" r="3.1" stroke-width="1.4" />
            <path
              d="M8 1v1.6M8 13.4V15M1 8h1.6M13.4 8H15M3.05 3.05l1.13 1.13M11.82 11.82l1.13 1.13M12.95 3.05l-1.13 1.13M4.18 11.82l-1.13 1.13"
              stroke-width="1.4"
              stroke-linecap="round"
            />
          </svg>
        </Match>
        <Match when={theme.setting() === "dark"}>
          <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
            <path
              d="M13.5 10.2A5.8 5.8 0 0 1 5.8 2.5a5.8 5.8 0 1 0 7.7 7.7Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.4"
              stroke-linejoin="round"
            />
          </svg>
        </Match>
        {/* System: a disc half light, half dark. */}
        <Match when={theme.setting() === "system"}>
          <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">
            <circle cx="8" cy="8" r="5.3" fill="none" stroke="currentColor" stroke-width="1.4" />
            <path d="M8 2.7a5.3 5.3 0 0 1 0 10.6Z" fill="currentColor" />
          </svg>
        </Match>
      </Switch>
    </button>
  );
};
