import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

const isVitest = process.env.VITEST === "true";

export default defineConfig({
  plugins: [sveltekit()],
  resolve: isVitest
    ? {
        conditions: ["browser", "module", "import", "default"],
      }
    : undefined,
  test: {
    include: ["src/**/*.{test,spec}.{js,ts}", "src/**/*.{test,spec}.svelte"],
    environment: "jsdom",
    setupFiles: ["src/setupTests.ts"],
    css: true,
    globals: true,
  },
});
