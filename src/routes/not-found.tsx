import { Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { PageHeader } from "~/components/PageHeader";

export default function NotFound() {
  return (
    <>
      <Title>Not found — Portfolio Edge</Title>
      <PageHeader title="No such page" standfirst="That URL does not match anything on this site." />
      <p>
        <A href="/" class="link">
          Back to the start
        </A>
      </p>
    </>
  );
}
