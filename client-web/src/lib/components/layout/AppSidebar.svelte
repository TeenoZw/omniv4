<script lang="ts">
  import SidebarNav from "./SidebarNav.svelte";
  import { Separator } from "$lib/components/ui/separator";
  import { mainNav, secondaryNav } from "./nav-items";
</script>

<aside class="hidden h-screen w-72 flex-col md:flex">
  <div class="m-4 flex h-[calc(100vh-2rem)] flex-col gap-6 rounded-[1.8rem] border border-white/70 bg-white/72 px-4 py-6 shadow-xl backdrop-blur dark:border-slate-800 dark:bg-slate-950/68">
    <div class="flex items-center gap-3 px-2">
      <img src="/brand/omni-logo-horizontal.svg" alt="Omni Industrial Solutions" class="h-12 w-auto object-contain" />
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-700 dark:text-cyan-300">Client workspace</p>
        <p class="mt-1 text-sm font-semibold tracking-wide text-foreground">Omni Logistics</p>
      </div>
    </div>

    <SidebarNav items={mainNav} label="Overview" />
    <Separator />
    <SidebarNav items={secondaryNav} label="Account" />
  </div>
</aside>
