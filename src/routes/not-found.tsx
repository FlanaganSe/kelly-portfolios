import { Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { For, type JSX } from "solid-js";
import { PageHeader } from "~/components/PageHeader";
import { NAV_ITEMS } from "~/lib/nav";

/**
 * The 404, which is also reached from a detail route whose id or ticker is unknown —
 * so it has to be useful to someone who followed a stale link to a fund, not only to
 * someone who mistyped a URL.
 */

const WHERE: Readonly<Record<string, string>> = {
  "/": "The argument, and the two benchmarks hiding inside “beat the market”.",
  "/portfolios": "Candidate constructions with exact weights, notional exposure and named failure modes.",
  "/research": "Research families, each put through the same seven questions.",
  "/funds": "Every fund this repository has priced or regressed, with its delivered exposure.",
  "/lab": "Set an edge and a tracking error and see the wait they imply.",
  "/concepts": "The vocabulary, defined once.",
  "/method": "How a result earns a status here, and where the machinery is broken.",
};

export default function NotFound(): JSX.Element {
  return (
    <>
      <Title>Not found — Portfolio Edge</Title>
      <PageHeader
        title="No such page"
        standfirst="That address does not match anything here. If you followed a link to a fund, it may be one this repository has never audited — the shelf holds what was priced, not the whole market."
      />
      <ul class="space-y-4">
        <For each={NAV_ITEMS}>
          {(item) => (
            <li class="border-l-2 border-rule-strong pl-4">
              <A href={item.href} class="link font-medium">
                {item.label}
              </A>
              <p class="mt-0.5 max-w-measure text-sm text-ink-muted">{WHERE[item.href]}</p>
            </li>
          )}
        </For>
      </ul>
    </>
  );
}
