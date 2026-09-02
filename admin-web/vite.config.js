import path from "node:path";
import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  resolve: {
    alias: {
      $lib: path.resolve(__dirname, "./src/lib"),
      src: path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("recharts")) return "charts";
            if (id.includes("lucide-svelte") || id.includes("@lucide")) return "icons";
            if (id.includes("mode-watcher") || id.includes("runed") || id.includes("svelte-toolbelt")) {
              return "theme";
            }
            return "vendor";
          }
        },
      },
    },
  },
});
