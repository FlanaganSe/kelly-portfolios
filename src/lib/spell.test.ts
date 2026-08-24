import { describe, expect, it } from "vitest";
import { Spell, spell } from "~/lib/spell";

describe("spelling a count", () => {
  it("spells the small ones", () => {
    expect(spell(0)).toBe("zero");
    expect(spell(7)).toBe("seven");
    expect(spell(20)).toBe("twenty");
  });

  it("capitalises for the start of a heading", () => {
    expect(Spell(10)).toBe("Ten");
  });

  it("leaves anything it would have to hyphenate as a numeral", () => {
    expect(spell(21)).toBe("21");
    expect(spell(52)).toBe("52");
    expect(spell(-1)).toBe("-1");
    expect(spell(1.5)).toBe("1.5");
  });
});
