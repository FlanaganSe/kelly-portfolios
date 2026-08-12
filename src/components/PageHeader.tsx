import { type Component, type JSX, Show } from "solid-js";

export interface PageHeaderProps {
  readonly title: string;
  /** The one-paragraph summary under the title. */
  readonly standfirst?: JSX.Element;
  /** ISO date the page was last checked against `docs/research/`. */
  readonly lastChecked?: string;
  /** Small label above the title, e.g. a section name. */
  readonly eyebrow?: string;
  readonly class?: string;
}

/** Page title, standfirst, and the date the page was last checked. */
export const PageHeader: Component<PageHeaderProps> = (props) => (
  <header class={`mb-10 border-b border-rule pb-6 ${props.class ?? ""}`}>
    <Show when={props.eyebrow}>
      <p class="eyebrow mb-2">{props.eyebrow}</p>
    </Show>

    <h1 class="max-w-[22ch] font-serif text-3xl font-normal tracking-[-0.015em] text-balance sm:text-4xl">
      {props.title}
    </h1>

    <Show when={props.standfirst}>
      <p class="mt-4 max-w-measure font-serif text-lg text-ink-muted">{props.standfirst}</p>
    </Show>

    <Show when={props.lastChecked}>
      {(date) => (
        <p data-numeric class="mt-4 text-xs text-ink-faint">
          Last checked {date()}
        </p>
      )}
    </Show>
  </header>
);
