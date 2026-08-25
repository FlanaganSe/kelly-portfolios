import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import solid from "vite-plugin-solid";
import { defineConfig } from "vitest/config";

// This file exists for Vitest only. Astro owns the site build; the Solid plugin here
// compiles the two islands and their tests. Under Vitest, Solid has to resolve to its
// client build and skip SSR codegen, so both changes are gated rather than global.
const isTest = process.env.VITEST !== undefined;

export default defineConfig({
  plugins: [solid({ ssr: !isTest }), tailwindcss()],
  resolve: {
    alias: {
      "~": path.resolve(import.meta.dirname, "./src"),
    },
    ...(isTest ? { conditions: ["development", "browser"] } : {}),
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["./src/test-setup.ts"],
  },
});
