import "@testing-library/jest-dom/vitest";

// A test that only reads files runs under the node environment, where there is
// no window at all. Guard rather than assume jsdom.
if (typeof window !== "undefined" && !window.matchMedia) {
  // jsdom has no matchMedia. The theme controller asks for one on mount.
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}
