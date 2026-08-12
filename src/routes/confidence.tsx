import { Title } from "@solidjs/meta";
import { PageHeader } from "~/components/PageHeader";

/** Stub. A content agent owns the body of this page. */
export default function Confidence() {
  return (
    <>
      <Title>Confidence — Portfolio Edge</Title>
      <PageHeader title="Confidence" standfirst="How long it takes before a result could be told apart from luck." />
      <p class="text-ink-faint">Placeholder. The confidence content agent fills this page.</p>
    </>
  );
}
