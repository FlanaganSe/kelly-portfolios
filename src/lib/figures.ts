/**
 * Read a figure record's value for a place that takes text rather than markup, such as a
 * `KeyNumbers` tile. The record stays the one place the number lives; the tile prints
 * whatever it says.
 */
import { getEntry } from "astro:content";

export async function figureValue(id: string): Promise<string> {
  const entry = await getEntry("figures", id);
  if (entry === undefined) {
    throw new Error(`figureValue("${id}"): no record at src/content/figures/${id}.yaml`);
  }
  return entry.data.value;
}
