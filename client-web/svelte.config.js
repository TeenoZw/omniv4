import adapter from "@sveltejs/adapter-cloudflare";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

const useCloudflareAdapter = process.env.OMNI_SVELTE_ADAPTER !== "none";

const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: useCloudflareAdapter ? adapter() : undefined,
    alias: {
      $lib: "src/lib",
      $components: "src/lib/components",
      $ui: "src/lib/components/ui",
      $utils: "src/lib/utils",
      $hooks: "src/lib/hooks",
    },
  },
};

export default config;
