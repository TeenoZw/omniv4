<script lang="ts">
  import { page } from "$app/stores";
  import type { NavItem } from "./nav-items";
  import { cn } from "$lib/utils.js";
  import Icon from "$lib/components/ui/Icon.svelte";

  export let items: NavItem[] = [];
  export let label: string | null = null;
</script>

<div class="space-y-3">
  {#if label}
    <p class="px-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
      {label}
    </p>
  {/if}

  <nav class="space-y-1">
    {#each items as item}
      <a
        href={item.href}
        class={cn(
          "omni-nav-link",
          $page.url.pathname === item.href || $page.url.pathname.startsWith(`${item.href}/`)
            ? "omni-nav-link-active"
            : "omni-nav-link-idle"
        )}
      >
        <Icon icon={item.icon} className="h-4 w-4" fixedWidth />
        <span>{item.title}</span>
        {#if item.badge}
          <span class="ml-auto rounded-full bg-primary/20 px-2 py-0.5 text-xs text-primary">
            {item.badge}
          </span>
        {/if}
      </a>
    {/each}
  </nav>
</div>
