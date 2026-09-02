<script lang="ts">
  import { config } from "@fortawesome/fontawesome-svg-core";
  import "@fortawesome/fontawesome-svg-core/styles.css";
  import "../app.css";
  import FloatingThemeToggle from "$lib/components/FloatingThemeToggle.svelte";
  import { page } from "$app/stores";

  config.autoAddCss = false;

  $: hideFloatingThemeToggle = ["/portal", "/login"].includes($page.url.pathname);
</script>

<slot />
{#if !hideFloatingThemeToggle}
  <FloatingThemeToggle />
{/if}
