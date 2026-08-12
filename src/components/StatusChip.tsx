import { type Component, Show } from "solid-js";
import { type CertaintyClass, certaintyMeta, type EvidenceStatus, statusMeta, type Tone } from "~/content/types";

const toneColor: Record<Tone, string> = {
  positive: "var(--tone-positive)",
  caution: "var(--tone-caution)",
  negative: "var(--tone-negative)",
  neutral: "var(--tone-neutral)",
};

/**
 * A distinct mark per tone, so the reading survives greyscale, colour blindness
 * and a printout. Colour is the second signal, never the only one.
 */
const ToneMark: Component<{ tone: Tone }> = (props) => (
  <svg viewBox="0 0 12 12" width="9" height="9" aria-hidden="true" class="shrink-0">
    <Show when={props.tone === "positive"}>
      <circle cx="6" cy="6" r="5" fill="currentColor" />
    </Show>
    <Show when={props.tone === "caution"}>
      <circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="1.4" />
      <path d="M6 1.5A4.5 4.5 0 0 1 6 10.5Z" fill="currentColor" />
    </Show>
    <Show when={props.tone === "negative"}>
      <circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="1.4" />
      <path d="M3.2 8.8 8.8 3.2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
    </Show>
    <Show when={props.tone === "neutral"}>
      <circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="1.4" />
    </Show>
  </svg>
);

interface ChipProps {
  readonly kind: string;
  readonly label: string;
  readonly gloss: string;
  readonly tone: Tone;
  readonly showGloss?: boolean;
  readonly class?: string;
}

const Chip: Component<ChipProps> = (props) => (
  <span class={`inline-flex flex-wrap items-baseline gap-x-2 gap-y-1 ${props.class ?? ""}`}>
    <span
      class="inline-flex items-center gap-1.5 border border-rule-strong rounded-[3px] px-1.5 py-0.5 font-sans text-2xs font-semibold uppercase tracking-[0.07em] whitespace-nowrap"
      style={{ color: toneColor[props.tone] }}
      title={props.gloss}
    >
      <span class="sr-only">{props.kind}: </span>
      <ToneMark tone={props.tone} />
      {props.label}
    </span>
    <Show when={props.showGloss}>
      <span class="text-sm text-ink-muted">{props.gloss}</span>
    </Show>
  </span>
);

export interface StatusChipProps {
  readonly status: EvidenceStatus;
  /** Print the one-line gloss beside the chip. */
  readonly showGloss?: boolean;
  readonly class?: string;
}

/** Renders an `EvidenceStatus` with its label, tone mark and gloss. */
export const StatusChip: Component<StatusChipProps> = (props) => {
  const meta = () => statusMeta[props.status];
  return (
    <Chip
      kind="Evidence status"
      label={meta().label}
      gloss={meta().gloss}
      tone={meta().tone}
      showGloss={props.showGloss}
      class={props.class}
    />
  );
};

export interface CertaintyChipProps {
  readonly certainty: CertaintyClass;
  readonly showGloss?: boolean;
  readonly class?: string;
}

/** The same chip for a `CertaintyClass`. A risk premium may never read as an edge. */
export const CertaintyChip: Component<CertaintyChipProps> = (props) => {
  const meta = () => certaintyMeta[props.certainty];
  return (
    <Chip
      kind="Certainty class"
      label={meta().label}
      gloss={meta().gloss}
      tone={meta().tone}
      showGloss={props.showGloss}
      class={props.class}
    />
  );
};
