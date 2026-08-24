import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import solid from "vite-plugin-solid";
import { defineConfig } from "vitest/config";

// Under Vitest, Solid has to resolve to its client build and skip SSR codegen.
// Outside it, neither change is wanted, so both are gated rather than global.
const isTest = process.env.VITEST !== undefined;

export default defineConfig({
  plugins: [solid({ ssr: !isTest }), tailwindcss()],
  resolve: {
    alias: {
      "~": path.resolve(import.meta.dirname, "./src"),
    },
    ...(isTest ? { conditions: ["development", "browser"] } : {}),
  },
  build: {
    target: "ES2022",
    cssCodeSplit: true,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["solid-js", "@solidjs/router", "@solidjs/meta"],
        },
      },
    },
  },
  server: {
    port: 3000,
    strictPort: true,
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["./src/test-setup.ts"],
  },
});
