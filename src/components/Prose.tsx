import type { ParentComponent } from "solid-js";
import { Dynamic } from "solid-js/web";

interface ProseProps {
  /** The element to render. `article` and `section` are the usual choices. */
  readonly as?: "div" | "article" | "section";
  readonly class?: string;
}

/**
 * The long-form text wrapper: measure, rhythm, list and link styling.
 *
 * Write ordinary HTML inside it. Headings, lists, links, `code` and
 * `blockquote` are styled by the `prose` class in `styles.css`. Anything that
 * has to break the measure — a wide table, a figure row — goes outside it.
 */
export const Prose: ParentComponent<ProseProps> = (props) => (
  <Dynamic component={props.as ?? "div"} class={`prose ${props.class ?? ""}`}>
    {props.children}
  </Dynamic>
);
