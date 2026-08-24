import { type Component, createMemo, createSignal, For, onMount, Show } from "solid-js";
import { NumberField, SelectField } from "~/components/islands/controls";
import {
  againstAWorkingLife,
  bpFromPercent,
  chanceAhead,
  formatChance,
  type HorizonOutcome,
  percentFromBp,
  timeToKnow,
} from "~/components/islands/horizon-model";
import { defaultPreset, type HorizonPreset, horizonPresets } from "~/components/islands/horizon-presets";
import { formatYears } from "~/lib/format";
import { defaultLabConfig, parseLabConfig, toSearchParams } from "~/lib/lab/config";

/**
 * How long before your own account could tell you whether a choice worked.
 *
 * Every number on screen comes from `horizonForConfidence` and
 * `probabilityOfOutperformance` by way of `~/components/islands/horizon-model`. Nothing
 * is computed twice and nothing is typed twice.
 *
 * The configuration rides in the query string through `~/lib/lab/config`, which is
 * lossless both ways and already tested, so a reader can send someone else the exact
 * pair of numbers they were looking at.
 */

/** The three confidence levels shown. 90% is the headline; the other two frame it. */
const LEVELS = [
  { confidence: 0.75, label: "3 chances in 4" },
  { confidence: 0.9, label: "9 chances in 10" },
  { confidence: 0.99, label: "99 times in 100" },
] as const;

const HEADLINE_CONFIDENCE = 0.9;
const CUSTOM = "custom";

function say(outcome: HorizonOutcome): string {
  if (outcome.kind === "never") return "no horizon at all";
  if (outcome.kind === "immediate") return "at once";
  return formatYears(outcome.years);
}

export const HowLongTool: Component = () => {
  const [presetId, setPresetId] = createSignal<string>(defaultPreset.id);
  const [edgePercent, setEdgePercent] = createSignal(percentFromBp(defaultPreset.edgeBp));
  const [driftPercent, setDriftPercent] = createSignal(percentFromBp(defaultPreset.trackingErrorBp));

  const edgeBp = () => bpFromPercent(edgePercent());
  const driftBp = () => bpFromPercent(driftPercent());

  const applyPreset = (preset: HorizonPreset) => {
    setPresetId(preset.id);
    setEdgePercent(percentFromBp(preset.edgeBp));
    setDriftPercent(percentFromBp(preset.trackingErrorBp));
  };

  const choose = (id: string) => {
    const preset = horizonPresets.find((entry) => entry.id === id);
    if (preset !== undefined) applyPreset(preset);
  };

  /** A typed figure is nobody's published claim any more, so the label stops claiming it. */
  const editEdge = (value: number) => {
    setPresetId(CUSTOM);
    setEdgePercent(value);
  };
  const editDrift = (value: number) => {
    setPresetId(CUSTOM);
    setDriftPercent(value);
  };

  // A shared link wins over the opening preset, and only on the client: the server has
  // no query string to read and renders the preset every reader sees first.
  onMount(() => {
    const incoming = parseLabConfig(window.location.search);
    const carriesPair =
      incoming.edgeBp !== defaultLabConfig.edgeBp || incoming.trackingErrorBp !== defaultLabConfig.trackingErrorBp;
    if (carriesPair) {
      setPresetId(CUSTOM);
      setEdgePercent(percentFromBp(incoming.edgeBp));
      setDriftPercent(percentFromBp(incoming.trackingErrorBp));
    }
  });

  const shareQuery = createMemo(() =>
    toSearchParams({ ...defaultLabConfig, edgeBp: edgeBp(), trackingErrorBp: driftBp() }).toString()
  );

  const [shareHref, setShareHref] = createSignal("");
  const syncAddressBar = () => {
    const query = shareQuery();
    const href = `${window.location.pathname}${query === "" ? "" : `?${query}`}`;
    window.history.replaceState(null, "", href);
    setShareHref(`${window.location.origin}${href}`);
  };

  const headline = createMemo(() =>
    timeToKnow({ edgeBp: edgeBp(), trackingErrorBp: driftBp(), confidence: HEADLINE_CONFIDENCE })
  );

  const named = () => horizonPresets.find((entry) => entry.id === presetId());
  const against = () => named()?.against ?? "against whatever you are comparing yourself with";

  const rows = createMemo(() =>
    LEVELS.map((level) => ({
      label: level.label,
      text: say(timeToKnow({ edgeBp: edgeBp(), trackingErrorBp: driftBp(), confidence: level.confidence })),
    }))
  );

  const chances = createMemo(() =>
    [10, 30].map((years) => ({
      years,
      text: formatChance(chanceAhead({ edgeBp: edgeBp(), trackingErrorBp: driftBp(), horizonYears: years })),
    }))
  );

  const options = [
    ...horizonPresets.map((preset) => ({ value: preset.id, label: preset.label })),
    { value: CUSTOM, label: "Your own numbers" },
  ];

  return (
    <div class="not-prose">
      <div class="grid gap-6 rounded-[3px] border border-rule bg-raised p-5 sm:grid-cols-2">
        <SelectField
          class="sm:col-span-2"
          label="Start from one of the claims on this site"
          value={presetId()}
          options={options}
          onChange={choose}
          hint="Pick one, then change either number and watch the wait move."
        />

        <NumberField
          label="How much better you expect to do, a year"
          value={edgePercent()}
          onInput={editEdge}
          min={0}
          max={10}
          {/* Three decimals, not two. The budget measured against a cheap index is 5.4
              basis points, and a two-decimal step cannot hold 0.054 — it showed 0.05,
              which is a different number and returns a different wait. */}
          step={0.001}
          unit="%"
          hint="0.89 means you expect to finish 0.89 percentage points a year ahead of whatever you are comparing yourself with."
        />

        <NumberField
          label="How far it can wander from that comparison in a year"
          value={driftPercent()}
          onInput={editDrift}
          min={0}
          max={30}
          step={0.01}
          unit="%"
          hint="A cheaper share class of the same index fund wanders by almost nothing. A portfolio built differently from the index wanders by several points."
        />
      </div>

      {/* One live region, because the wait, the three levels and the two odds are all
          one answer and a screen reader should hear them as one update. */}
      <div aria-live="polite" class="mt-8">
        <p class="eyebrow">Time until there is a 9-in-10 chance you are ahead</p>
        <p data-numeric class="mt-1 font-serif text-5xl tracking-[-0.02em] text-ink">
          {say(headline())}
        </p>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          {againstAWorkingLife(headline())} Measured {against()}, at {edgePercent()}% a year of expected advantage
          against {driftPercent()}% a year of drift.
        </p>

        <dl class="mt-6 grid max-w-page gap-x-8 gap-y-3 sm:grid-cols-3">
          <For each={rows()}>
            {(row) => (
              <div class="border-t border-rule pt-2">
                <dt class="text-xs text-ink-faint">Sure enough to call it: {row.label}</dt>
                <dd data-numeric class="text-lg font-semibold text-ink">
                  {row.text}
                </dd>
              </div>
            )}
          </For>
        </dl>

        <dl class="mt-6 grid max-w-page gap-x-8 gap-y-3 sm:grid-cols-3">
          <For each={chances()}>
            {(chance) => (
              <div class="border-t border-rule pt-2">
                <dt class="text-xs text-ink-faint">Chance of being ahead after {chance.years} years</dt>
                <dd data-numeric class="text-lg font-semibold text-ink">
                  {chance.text}
                </dd>
              </div>
            )}
          </For>
        </dl>
      </div>

      <div class="mt-8 flex flex-wrap items-baseline gap-3">
        <button
          type="button"
          class="inline-flex h-9 items-center rounded-[3px] border border-rule px-3 text-sm text-ink-muted transition-colors hover:border-rule-strong hover:text-ink"
          onClick={syncAddressBar}
        >
          Put these numbers in the address bar
        </button>
        <Show when={shareHref() !== ""}>
          <span data-numeric class="max-w-full truncate text-xs text-ink-faint">
            {shareHref()}
          </span>
        </Show>
      </div>
    </div>
  );
};

export default HowLongTool;
