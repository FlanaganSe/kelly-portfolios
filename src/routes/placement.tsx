import { Title } from "@solidjs/meta";
import { PageHeader } from "~/components/PageHeader";

/** Stub. A content agent owns the body of this page. */
export default function Placement() {
  return (
    <>
      <Title>Where it's held — Portfolio Edge</Title>
      <PageHeader title="Where it's held" standfirst="Account placement, fund structure, and the tax-lot method." />
      <p class="text-ink-faint">Placeholder. The placement content agent fills this page.</p>
    </>
  );
}
