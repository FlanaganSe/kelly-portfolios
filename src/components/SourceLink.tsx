import { type Component, Show } from "solid-js";
import type { Citation } from "~/content/types";
import { citationHref } from "~/lib/citation";

export interface SourceLinkProps {
  readonly citation: Citation;
  /** Prefix the label with "Source: ". Use in a figure footer, not mid-sentence. */
  readonly prefix?: boolean;
  readonly class?: string;
}

/**
 * A link back to the page that owns the fact.
 *
 * The docs are Markdown in the repository and this client is static, so a
 * `docPath` resolves to the file on GitHub. An external primary source wins
 * when the citation carries one.
 */
export const SourceLink: Component<SourceLinkProps> = (props) => {
  const href = () => citationHref(props.citation);
  return (
    <a
      href={href()}
      target="_blank"
      rel="noopener noreferrer"
      class={`link inline-flex items-baseline gap-1 text-sm ${props.class ?? ""}`}
    >
      <Show when={props.prefix}>
        <span class="text-ink-faint no-underline">Source:</span>
      </Show>
      <span>{props.citation.label}</span>
      <svg viewBox="0 0 12 12" width="9" height="9" aria-hidden="true" class="shrink-0 self-center opacity-70">
        <path
          d="M4.5 1.5h6v6M10.5 1.5 5 7M8 8.5v2h-6.5V4h2"
          fill="none"
          stroke="currentColor"
          stroke-width="1.3"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <span class="sr-only">(opens in a new tab)</span>
    </a>
  );
};
