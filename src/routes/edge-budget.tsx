import { Title } from "@solidjs/meta";
import { PageHeader } from "~/components/PageHeader";

/** Stub. A content agent owns the body of this page. */
export default function EdgeBudget() {
  return (
    <>
      <Title>Edge budget — Portfolio Edge</Title>
      <PageHeader
        title="Edge budget"
        standfirst="What is available against the portfolio you would otherwise have owned, line by line."
      />
      <p class="text-ink-faint">Placeholder. The edge-budget content agent fills this page.</p>
    </>
  );
}
