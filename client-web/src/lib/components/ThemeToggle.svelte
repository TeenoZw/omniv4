<script lang="ts">
  import { onMount } from "svelte";
  import { buttonVariants } from "$lib/components/ui/button";
  import Icon from "$lib/components/ui/Icon.svelte";
  import { cn } from "$lib/utils.js";
  import { faMoon, faSun } from "@fortawesome/free-solid-svg-icons";

  type ThemeMode = "light" | "dark";

  let theme: ThemeMode = "light";
  let mounted = false;

  onMount(() => {
    mounted = true;
    const stored = localStorage.getItem("theme") as ThemeMode | null;
    if (stored) {
      setTheme(stored);
      return;
    }

    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(prefersDark ? "dark" : "light");
  });

  function setTheme(next: ThemeMode) {
    theme = next;
    const root = document.documentElement;
    root.classList.toggle("dark", next === "dark");
    localStorage.setItem("theme", next);
  }

  function toggleTheme() {
    setTheme(theme === "dark" ? "light" : "dark");
  }
</script>

<button
  type="button"
  class={cn(buttonVariants({ variant: "ghost", size: "icon" }), "h-9 w-9")}
  aria-label="Toggle color mode"
  on:click={toggleTheme}
  disabled={!mounted}
>
  <Icon
    icon={faSun}
    className={cn("h-4 w-4 transition-opacity", theme === "dark" ? "opacity-0" : "opacity-100")}
  />
  <Icon
    icon={faMoon}
    className={cn(
      "absolute h-4 w-4 transition-opacity",
      theme === "dark" ? "opacity-100" : "opacity-0"
    )}
  />
  <span class="sr-only">Toggle theme</span>
</button>
