import { type ParentComponent, Show } from "solid-js";

export type CalloutVariant = "caveat" | "mechanism" | "open-question";

const variantMeta: Record<CalloutVariant, { readonly label: string; readonly rule: string }> = {
  caveat: { label: "Caveat", rule: "var(--tone-caution)" },
  mechanism: { label: "Mechanism", rule: "var(--rule-strong)" },
  "open-question": { label: "Open question", rule: "var(--accent)" },
};

export interface CalloutProps {
  readonly variant: CalloutVariant;
  /** Overrides the default label. Keep it to a few words. */
  readonly label?: string;
  readonly class?: string;
}

/**
 * A rule and a label. Not a coloured box.
 *
 * `caveat` is what would break the claim, `mechanism` is why the effect should
 * exist at all, `open-question` is what the work has not settled.
 */
export const Callout: ParentComponent<CalloutProps> = (props) => {
  const meta = () => variantMeta[props.variant];
  return (
    <aside class={`my-6 max-w-measure border-l-2 pl-4 ${props.class ?? ""}`} style={{ "border-color": meta().rule }}>
      <p class="eyebrow mb-1.5">
        <Show when={props.label} fallback={meta().label}>
          {props.label}
        </Show>
      </p>
      <div class="text-base text-ink-muted [&>*+*]:mt-3">{props.children}</div>
    </aside>
  );
};
