import { describe, expect, it } from "vitest";
import { isThemeSetting, nextTheme, resolveTheme } from "~/lib/theme";

describe("nextTheme", () => {
  it("cycles system, light, dark and back", () => {
    expect(nextTheme("system")).toBe("light");
    expect(nextTheme("light")).toBe("dark");
    expect(nextTheme("dark")).toBe("system");
  });
});

describe("resolveTheme", () => {
  it("takes an explicit setting over the system preference, in both directions", () => {
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("dark", false)).toBe("dark");
  });

  it("follows the system preference when the setting is system", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
  });
});

describe("isThemeSetting", () => {
  it("rejects anything outside the three settings", () => {
    expect(isThemeSetting("dark")).toBe(true);
    expect(isThemeSetting("sepia")).toBe(false);
    expect(isThemeSetting(null)).toBe(false);
  });
});
