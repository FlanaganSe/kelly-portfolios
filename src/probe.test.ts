import { experimental_AstroContainer as AstroContainer } from "astro/container";
import { expect, it } from "vitest";
import StackingCeiling from "~/components/charts/StackingCeiling.astro";

it("renders", async () => {
  const container = await AstroContainer.create();
  const html = await container.renderToString(StackingCeiling);
  expect(html).toContain("<svg");
});
