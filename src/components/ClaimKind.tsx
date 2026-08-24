import { type Component, For, type JSX } from "solid-js";

/**
 * What kind of statement a block of the page is making.
 *
 * Four kinds, and the distinction between them is the one a reader most often loses:
 * a filed fee, a figure estimated from a window, an assumption about the future, and
 * an opinion. They are set in the same type and the same colour on purpose — the tag
 * is a label, not a rating, and dressing one of them up would defeat it.
 */

export type ClaimKind = "filed" | "estimated" | "assumed" | "editorial";

export const claimKindMeta = {
  filed: {
    label: "Filed fact",
    gloss:
      "Read off a prospectus, a regulatory filing or a statute. It can go stale; it cannot be wrong about the past.",
  },
  estimated: {
    label: "Estimated",
    gloss: "Measured over a stated window with a stated interval. A different window gives a different number.",
  },
  assumed: {
    label: "Forward assumption",
    gloss: "A number about the future that nothing here can measure. Change it and the conclusion changes.",
  },
  editorial: {
    label: "Editorial judgment",
    gloss: "An opinion held by this site, resting on the measurements named beside it. Nothing is promoted.",
  },
} as const satisfies Readonly<Record<ClaimKind, { readonly label: string; readonly gloss: string }>>;

export interface ClaimTagProps {
  readonly kind: ClaimKind;
  readonly class?: string;
}

/** A single tag, for beside a section heading. */
export const ClaimTag: Component<ClaimTagProps> = (props) => (
  <span
    class={`inline-flex items-baseline gap-1.5 whitespace-nowrap ${props.class ?? ""}`}
    title={claimKindMeta[props.kind].gloss}
  >
    <span aria-hidden="true" class="text-ink-faint">
      ·
    </span>
    <span class="eyebrow">
      <span class="sr-only">Section type: </span>
      {claimKindMeta[props.kind].label}
    </span>
  </span>
);

/** The legend. Printed once per page, above the first tagged section. */
export function ClaimLegend(props: { readonly class?: string }): JSX.Element {
  return (
    <dl class={`grid gap-x-8 gap-y-3 border-y border-rule py-5 sm:grid-cols-2 ${props.class ?? ""}`}>
      <For each={Object.entries(claimKindMeta)}>
        {([kind, meta]) => (
          <div class="flex flex-col gap-0.5" data-claim-kind={kind}>
            <dt class="eyebrow">{meta.label}</dt>
            <dd class="max-w-[46ch] text-sm text-ink-muted">{meta.gloss}</dd>
          </div>
        )}
      </For>
    </dl>
  );
}
