import path from "node:path";
import preact from "@preact/preset-vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    preact({
      prerender: { enabled: true },
      devtoolsInProd: false,
    }),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "~": path.resolve(import.meta.dirname, "./src"),
    },
  },
  build: {
    target: "ES2022",
    cssCodeSplit: true,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["preact", "preact/hooks", "wouter"],
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
});
