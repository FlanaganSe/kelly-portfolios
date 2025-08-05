import path from "node:path";
import preact from "@preact/preset-vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [preact({ prerender: { enabled: true } }), tailwindcss()],
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "./src"),
    },
  },
});
