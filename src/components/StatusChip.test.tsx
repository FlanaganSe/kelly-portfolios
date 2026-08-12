import { render } from "@solidjs/testing-library";
import { describe, expect, it } from "vitest";
import { StatusChip } from "~/components/StatusChip";
import { statusMeta } from "~/content/types";

describe("StatusChip", () => {
  it("renders the label from the content vocabulary", () => {
    const { getByText } = render(() => <StatusChip status="rejected" />);
    expect(getByText(statusMeta.rejected.label)).toBeInTheDocument();
  });

  it("prints the gloss on request, and not otherwise", () => {
    const { queryByText } = render(() => <StatusChip status="unresolved" />);
    expect(queryByText(statusMeta.unresolved.gloss)).toBeNull();

    const shown = render(() => <StatusChip status="unresolved" showGloss />);
    expect(shown.getByText(statusMeta.unresolved.gloss)).toBeInTheDocument();
  });

  it("carries the tone with a mark, not colour alone", () => {
    const { container } = render(() => <StatusChip status="rejected" />);
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
