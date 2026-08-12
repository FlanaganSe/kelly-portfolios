import { For, type JSX, Show } from "solid-js";

export interface Column<Row> {
  /** Stable key. Used for the cell list, not for lookup. */
  readonly key: string;
  readonly header: string;
  /** Right-aligns and applies tabular numerals. Set it on every number column. */
  readonly numeric?: boolean;
  /** A CSS width for the column, e.g. `"12rem"` or `"30%"`. */
  readonly width?: string;
  /** Renders this column's cell. Return a string for plain values. */
  readonly cell: (row: Row, index: number) => JSX.Element;
  /** Renders the cell as a row header (`<th scope="row">`). At most one column. */
  readonly rowHeader?: boolean;
}

export interface DataTableProps<Row> {
  /** Required. Says what the table shows; screen readers announce it first. */
  readonly caption: string;
  /** Hide the caption visually. It stays in the accessibility tree. */
  readonly captionHidden?: boolean;
  readonly columns: readonly Column<Row>[];
  readonly rows: readonly Row[];
  /** Pins the header while a long table scrolls. */
  readonly stickyHeader?: boolean;
  /** A source line, unit note or caveat, printed under the table. */
  readonly footnote?: JSX.Element;
  readonly class?: string;
}

/**
 * A semantic table with a caption, right-aligned numeric columns and tabular
 * numerals. It scrolls sideways inside its own container, so a wide table never
 * makes the page body scroll.
 */
export function DataTable<Row>(props: DataTableProps<Row>): JSX.Element {
  return (
    <div class={props.class}>
      {/* tabindex makes the scroll region reachable by keyboard. */}
      <section
        class="overflow-x-auto overscroll-x-contain border-y border-rule focus-visible:outline-2 focus-visible:outline-accent"
        tabindex="0"
        aria-label={props.caption}
      >
        <table class="w-full border-collapse text-sm tabular-nums">
          <caption class={props.captionHidden ? "sr-only" : "caption-top pb-2 text-left text-sm text-ink-muted"}>
            {props.caption}
          </caption>

          <thead class={props.stickyHeader ? "sticky top-0 z-10 bg-paper" : undefined}>
            <tr>
              <For each={props.columns}>
                {(column) => (
                  <th
                    scope="col"
                    style={column.width ? { width: column.width } : undefined}
                    class={`eyebrow border-b border-rule-strong px-3 py-2 align-bottom whitespace-nowrap ${
                      column.numeric ? "text-right" : "text-left"
                    }`}
                  >
                    {column.header}
                  </th>
                )}
              </For>
            </tr>
          </thead>

          <tbody>
            <For each={props.rows}>
              {(row, index) => (
                <tr class="border-b border-rule last:border-b-0 hover:bg-sunken">
                  <For each={props.columns}>
                    {(column) => (
                      <Show
                        when={column.rowHeader}
                        fallback={
                          <td class={`px-3 py-2 align-top ${column.numeric ? "text-right tabular-nums" : "text-left"}`}>
                            {column.cell(row, index())}
                          </td>
                        }
                      >
                        <th scope="row" class="px-3 py-2 text-left align-top font-medium">
                          {column.cell(row, index())}
                        </th>
                      </Show>
                    )}
                  </For>
                </tr>
              )}
            </For>
          </tbody>
        </table>
      </section>

      <Show when={props.footnote}>
        <p class="mt-2 max-w-measure text-xs text-ink-muted">{props.footnote}</p>
      </Show>
    </div>
  );
}
