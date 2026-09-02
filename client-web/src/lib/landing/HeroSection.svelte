<script lang="ts">
  import { onMount } from "svelte";
  import Icon from "$lib/components/ui/Icon.svelte";
  import { faSignal, faNetworkWired, faBell } from "@fortawesome/free-solid-svg-icons";
  import { fetchPublicStats } from "$lib/api/stats";

  export let onPortalClick: (() => void) | undefined;

  let activeUsers = 0;
  let activeAssets = 0;
  let provincesServed = 0;

  $: liveStats = [
    { label: "Active Users", value: String(activeUsers), icon: faSignal },
    { label: "Provinces Served", value: String(provincesServed), icon: faNetworkWired },
    { label: "Active Assets", value: String(activeAssets), icon: faBell },
  ];

  const fleetImages = [
    {
      src: "/landing/omni-dashboard.png",
      alt: "Fleet performance dashboard and analytics",
    },
    {
      src: "/landing/omni-fleet-yard.jpg",
      alt: "Large fleet yard with vehicles staged for dispatch",
    },
    {
      src: "/landing/omni-truck-yard.jpg",
      alt: "Truck yard operations and fleet staging",
    },
  ];

  let heroIndex = 0;

  const nextHero = () => {
    heroIndex = (heroIndex + 1) % fleetImages.length;
  };

  const prevHero = () => {
    heroIndex = (heroIndex - 1 + fleetImages.length) % fleetImages.length;
  };

  onMount(async () => {
    try {
      const stats = await fetchPublicStats();
      activeUsers = stats.active_users;
      activeAssets = stats.active_assets;
      provincesServed = stats.provinces_served;
    } catch (error) {
      console.error("Failed to load public stats", error);
    }
  });
</script>

<section id="home" class="relative overflow-hidden rounded-3xl border bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-5 py-12 text-white shadow-2xl sm:px-8 md:px-12 md:py-16">
  <div class="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.15),_transparent_55%)]"></div>
  <div class="grid items-center gap-10 lg:grid-cols-[3fr_2fr]">
    <div class="space-y-6 md:space-y-8">
      <div>
        <h1 class="text-3xl font-black leading-tight tracking-tight sm:text-4xl md:text-5xl">
          Structured fleet intelligence infrastructure for operational control, compliance, and performance optimization.
        </h1>
        <p class="mt-2 text-sm uppercase tracking-[0.3em] text-cyan-200/80">Omni Logistics</p>
      </div>
      <div class="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium">
        <span>Built for certainty: compliance, support, and reliable operations</span>
      </div>
      <p class="max-w-2xl text-base text-slate-200 sm:text-lg">
        Omni Logistics delivers global-grade telematics capability with local execution in Zimbabwe. We manage onboarding,
        connectivity, governance, billing, and support while your teams retain clear operational visibility.
      </p>
      <div class="flex flex-wrap gap-4">
        <button
          type="button"
          class="group inline-flex items-center gap-3 rounded-full bg-cyan-400 px-6 py-3 text-base font-semibold text-slate-900 transition hover:bg-cyan-300"
          on:click={() => onPortalClick?.()}
        >
          Get Started
          <span aria-hidden="true" class="transition group-hover:translate-x-1">→</span>
        </button>
        <a
          href="/tracking"
          target="_blank"
          rel="noreferrer"
          class="inline-flex items-center gap-3 rounded-full border border-white/30 px-6 py-3 text-base font-semibold text-white transition hover:border-white hover:bg-white/5"
        >
          Tracking Portal
          <span aria-hidden="true" class="text-cyan-300">⟶</span>
        </a>
      </div>
      <div class="flex flex-wrap items-center gap-4 text-sm text-white/70 sm:gap-6">
        <div>
          <p class="text-2xl font-bold text-white sm:text-3xl">{activeAssets}</p>
          <p>Active assets</p>
        </div>
        <div class="hidden h-12 w-px bg-white/20 sm:block"></div>
        <div>
          <p class="text-2xl font-bold text-white sm:text-3xl">{activeUsers}</p>
          <p>Active users</p>
        </div>
        <div class="hidden h-12 w-px bg-white/20 sm:block"></div>
        <div>
          <p class="text-2xl font-bold text-white sm:text-3xl">{provincesServed}</p>
          <p>Provinces covered</p>
        </div>
      </div>
    </div>

    <div class="relative space-y-4">
      <div class="absolute inset-0 -z-10 rounded-3xl bg-gradient-to-br from-cyan-500/20 to-fuchsia-500/20 blur-3xl"></div>
      <div class="flex flex-col gap-4 rounded-3xl border border-white/15 bg-slate-900/60 p-4 shadow-2xl backdrop-blur sm:p-6">
        <div class="flex items-center justify-between text-sm text-white/80">
          <span>Live Operations</span>
          <span class="inline-flex items-center gap-1 rounded-full bg-white/10 px-3 py-1 text-xs">Updated · 1m</span>
        </div>
        <div class="space-y-3">
          {#each liveStats as stat}
            <div class="flex items-center justify-between rounded-2xl bg-white/5 px-4 py-3">
              <div class="flex items-center gap-3 text-sm">
                <span class="flex h-9 w-9 items-center justify-center rounded-2xl bg-white/10 sm:h-10 sm:w-10">
                  <Icon icon={stat.icon} className="h-4 w-4 text-cyan-200" />
                </span>
                <span>{stat.label}</span>
              </div>
                <span class="text-base font-semibold">{stat.value}</span>
            </div>
          {/each}
        </div>
        <div class="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm">
          <p class="text-xs uppercase tracking-wide text-cyan-200/80">Omni Eye Portal</p>
          <p class="text-base font-semibold">Onboarding ops & subscription oversight.</p>
          <p class="text-white/70">Omni Eye Portal access</p>
        </div>
      </div>
      <div class="overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-2xl">
        <div
          class="flex transition-transform duration-500"
          style={`transform: translateX(-${heroIndex * 100}%);`}
        >
          {#each fleetImages as image (image.src)}
            <div class="w-full shrink-0">
              <img
                src={image.src}
                alt={image.alt}
                class="h-44 w-full object-cover sm:h-56"
                loading="lazy"
              />
            </div>
          {/each}
        </div>
        <div class="flex items-center justify-between px-4 py-3">
          <button
            type="button"
            class="rounded-full border border-white/20 px-3 py-1 text-xs text-white/80"
            on:click={prevHero}
          >
            Prev
          </button>
          <div class="flex items-center gap-2">
            {#each fleetImages as _image, index (index)}
              <button
                type="button"
                class={`h-2 w-2 rounded-full ${index === heroIndex ? "bg-cyan-300" : "bg-white/30"}`}
                on:click={() => (heroIndex = index)}
                aria-label={`Go to slide ${index + 1}`}
              ></button>
            {/each}
          </div>
          <button
            type="button"
            class="rounded-full border border-white/20 px-3 py-1 text-xs text-white/80"
            on:click={nextHero}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</section>
