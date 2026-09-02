<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Sheet, SheetContent, SheetTrigger } from "$lib/components/ui/sheet";
  import { Separator } from "$lib/components/ui/separator";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import UserMenu from "./UserMenu.svelte";
  import SidebarNav from "./SidebarNav.svelte";
  import { mainNav, secondaryNav } from "./nav-items";
  import { buttonVariants } from "$lib/components/ui/button";
  import Icon from "$lib/components/ui/Icon.svelte";
  import { cn } from "$lib/utils.js";
  import {
    faBars,
    faMagnifyingGlass,
    faArrowUpRightFromSquare,
  } from "@fortawesome/free-solid-svg-icons";
  import { sessionStore, switchHub } from "$lib/api/session";

  $: session = $sessionStore;
  $: hubs = session?.hubs ?? [];
  $: selectedHubId = session?.hubId ?? "";
  $: selectedHubRole = hubs.find((hub) => hub.id === selectedHubId)?.role;

  function handleHubChange(event: Event) {
    const nextHubId = (event.target as HTMLSelectElement).value;
    if (!nextHubId || nextHubId === selectedHubId) return;
    switchHub(nextHubId);
  }
</script>

<header class="mx-4 mt-4 flex items-center justify-between rounded-[1.8rem] border border-white/70 bg-white/72 px-4 py-3 shadow-xl backdrop-blur dark:border-slate-800 dark:bg-slate-950/68 sm:mx-6 lg:mx-8">
  <div class="flex flex-1 items-center gap-3">
    <Sheet>
      <SheetTrigger
        class={cn(buttonVariants({ variant: "ghost", size: "icon" }), "md:hidden")}
        aria-label="Open navigation"
      >
        <Icon icon={faBars} className="h-5 w-5" />
      </SheetTrigger>
      <SheetContent side="left" class="w-72 p-0">
        <div class="px-4 py-4">
          <SidebarNav items={mainNav} label="Overview" />
          <Separator class="my-4" />
          <SidebarNav items={secondaryNav} label="Account" />
        </div>
      </SheetContent>
    </Sheet>

    <div class="hidden min-w-0 flex-col md:flex">
      <span class="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-700 dark:text-cyan-300">Client workspace</span>
      <span class="mt-1 text-lg font-semibold leading-tight text-foreground">
        {session?.hubName ?? "Subscription overview"}
      </span>
      <span class="text-xs text-muted-foreground">
        {session?.hubCode ?? "Customer workspace"}
        {#if selectedHubRole}
          · {selectedHubRole}
        {/if}
      </span>
    </div>

    {#if hubs.length > 1}
      <label class="hidden min-w-[240px] md:block">
        <span class="sr-only">Switch hub</span>
        <select
          class="omni-select py-2.5"
          value={selectedHubId}
          on:change={handleHubChange}
        >
          {#each hubs as hub (hub.id)}
            <option value={hub.id}>{hub.name} · {hub.code}</option>
          {/each}
        </select>
      </label>
    {/if}

    <div class="relative ml-auto hidden max-w-sm flex-1 md:block">
      <Input
        type="search"
        placeholder="Search billing, support, devices..."
        class="rounded-2xl border-white/70 bg-white/80 pl-9 shadow-sm dark:border-slate-800 dark:bg-slate-950/55"
        aria-label="Search"
      />
      <Icon
        icon={faMagnifyingGlass}
        className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
      />
    </div>
  </div>

  <div class="flex items-center gap-2">
    <button
      type="button"
      class={cn(buttonVariants({ size: "sm" }), "hidden md:inline-flex items-center gap-2 rounded-xl")}
      on:click={() => window.open("/tracking", "_blank")}
    >
      <Icon icon={faArrowUpRightFromSquare} className="h-4 w-4" />
      Tracking Portal
    </button>
    <ThemeToggle />
    <UserMenu />
  </div>
</header>
