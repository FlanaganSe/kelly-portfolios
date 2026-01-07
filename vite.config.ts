import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import solid from "vite-plugin-solid";

export default defineConfig({
  plugins: [solid({ ssr: false }), tailwindcss()],
  resolve: {
    alias: {
      "~": path.resolve(import.meta.dirname, "./src"),
    },
  },
  worker: {
    format: "es",
    plugins: () => [solid({ ssr: false })],
    rollupOptions: {
      output: {
        entryFileNames: "[name].js",
      },
    },
  },
  build: {
    target: "ES2022",
    cssCodeSplit: true,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["solid-js", "@solidjs/router", "@solidjs/meta"],
          charts: ["chart.js"],
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
