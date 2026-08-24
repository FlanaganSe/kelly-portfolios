import { describe, expect, it } from "vitest";
import { families } from "~/content/families";
import { lessons } from "~/content/lessons";

/** Site paths the short course is allowed to point at, beyond a research family. */
const STATIC_TARGETS = new Set(["/lab", "/funds", "/method", "/portfolios", "/concepts", "/research"]);

describe("the short course", () => {
  it("has a unique id per lesson", () => {
    expect(new Set(lessons.map((one) => one.id)).size).toBe(lessons.length);
  });

  it("states a claim rather than naming a topic", () => {
    for (const lesson of lessons) {
      expect(lesson.title.length, lesson.id).toBeGreaterThan(24);
      expect(lesson.body.length, lesson.id).toBeGreaterThan(160);
    }
  });

  it("points every lesson at a page that exists", () => {
    for (const lesson of lessons) {
      const slug = lesson.href.startsWith("/research/") ? lesson.href.slice("/research/".length) : null;
      const resolved = slug === null ? STATIC_TARGETS.has(lesson.href) : families.some((one) => one.slug === slug);
      expect(resolved, `${lesson.id} -> ${lesson.href}`).toBe(true);
    }
  });
});
