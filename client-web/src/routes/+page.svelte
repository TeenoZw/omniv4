<svelte:head>
  <title>Omni Logistics | Managed Fleet Intelligence</title>
  <meta
    name="description"
    content="Omni Logistics delivers managed fleet intelligence, telematics onboarding, installation coordination, billing support, and customer operations for Zimbabwean fleets."
  />
</svelte:head>

<script lang="ts">
  import { browser } from "$app/environment";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import MarketingShell from "$lib/marketing/MarketingShell.svelte";

  onMount(() => {
    if (browser && import.meta.env.VITE_OMNI_SURFACE === "portal") {
      goto("/portal", { replaceState: true });
    }
  });

  const measures = [
    { value: "24/7", label: "fleet visibility" },
    { value: "1", label: "managed account layer" },
    { value: "3", label: "connected portals" },
  ];

  const operatingModel = [
    {
      step: "01",
      title: "Understand the fleet",
      body: "We review your vehicles, routes, users, risks, and reporting needs before recommending a setup.",
    },
    {
      step: "02",
      title: "Install with control",
      body: "Trackers, SIM cards, installation work, and activation are recorded properly so every vehicle is accounted for.",
    },
    {
      step: "03",
      title: "Run the service",
      body: "Your team gets access to fleet records, support, invoices, documents, and tracking without chasing separate systems.",
    },
  ];

  const platformAreas = [
    "Fleet tracking",
    "Installation jobs",
    "Tracker and SIM inventory",
    "Customer portal",
    "Billing support",
    "Maintenance context",
    "Documents",
    "Support tickets",
  ];

  const connectivityNotes = [
    {
      title: "Live when the network is available",
      body: "When a tracker has GPS signal, power, and cellular data, positions can be sent through quickly for live monitoring.",
    },
    {
      title: "Stored when coverage drops",
      body: "In weak or unavailable cellular coverage, quality trackers can keep recording movement and upload the trip once connectivity returns.",
    },
    {
      title: "Smoothed with dead reckoning",
      body: "Dead reckoning uses movement signals to estimate what happened between confirmed GPS points, reducing gaps in trip history.",
    },
  ];

  const journeys = [
    {
      href: "/solutions",
      title: "Managed fleet intelligence",
      body: "See how Omni combines tracking, installation, billing, support, and account management into one service.",
      image: "/landing/omni-dashboard.png",
    },
    {
      href: "/industries",
      title: "Built for field-heavy businesses",
      body: "Support logistics, construction, mining, utilities, public sector, and service fleets with practical tracking and support.",
      image: "/landing/omni-quarry.jpg",
    },
    {
      href: "/platform",
      title: "A practical service platform",
      body: "Explore how Omni manages enquiries, customer accounts, installations, fleet records, support, and billing.",
      image: "/landing/omni-devices.png",
    },
  ];
</script>

<MarketingShell
  currentPath="/"
  title="Empowering your fleet, driving your success"
  kicker="Omni Logistics"
  intro="Fleet tracking, installation coordination, support, billing, and customer account management handled through one professional service."
  image="/landing/omni-truck-yard.jpg"
  imageAlt="Omni Logistics fleet vehicles in an operational yard"
>
  <section class="relative -mt-8 px-4 sm:px-6 lg:px-8">
    <div class="mx-auto grid max-w-7xl gap-3 rounded-[1.25rem] border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:grid-cols-3">
      {#each measures as item}
        <div class="rounded-2xl px-5 py-5 transition duration-300 hover:bg-slate-50 dark:hover:bg-slate-800/60">
          <p class="text-3xl font-semibold text-slate-950 dark:text-white">{item.value}</p>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{item.label}</p>
        </div>
      {/each}
    </div>
  </section>

  <section class="mx-auto grid max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[0.8fr_1.2fr] lg:px-8">
    <div class="marketing-reveal">
      <span class="marketing-pill">Operating model</span>
      <h2 class="mt-5 max-w-xl text-3xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-4xl">
        Built around the work that happens after installation.
      </h2>
      <p class="mt-5 max-w-lg text-base leading-7 text-slate-600 dark:text-slate-300">
        Good tracking depends on more than a device. Omni helps manage the setup, installation, support,
        billing, documents, and service follow-up that keep the system useful over time.
      </p>
    </div>

    <div class="grid gap-4">
      {#each operatingModel as item}
        <article class="group grid gap-4 rounded-[1.25rem] border border-slate-200 bg-white p-5 shadow-sm transition duration-300 hover:-translate-y-1 hover:border-cyan-200 hover:shadow-lg dark:border-slate-800 dark:bg-slate-900/70 dark:hover:border-cyan-400/30 sm:grid-cols-[72px_1fr]">
          <p class="text-sm font-semibold text-cyan-700 dark:text-cyan-300">{item.step}</p>
          <div>
            <h3 class="text-xl font-semibold text-slate-950 dark:text-white">{item.title}</h3>
            <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p>
          </div>
        </article>
      {/each}
    </div>
  </section>

  <section class="mx-auto grid max-w-7xl gap-10 px-4 pb-20 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
    <div class="marketing-reveal">
      <span class="marketing-pill">Dead-reckoning</span>
      <h2 class="mt-5 max-w-xl text-3xl font-semibold leading-tight text-slate-950 dark:text-white sm:text-4xl">
        Dead-reckoning helps keep trip history readable when the network is not perfect.
      </h2>
      <p class="mt-5 max-w-lg text-base leading-7 text-slate-600 dark:text-slate-300">
        Real-time tracking depends on cellular connectivity. When a vehicle travels through an area with little or no
        network coverage, no platform can transmit positions at that exact moment. Dead-reckoning helps explain what
        likely happened between confirmed GPS points, so trip replays feel smoother and easier to understand once the
        vehicle comes back online.
      </p>
    </div>

    <div class="rounded-[1.25rem] border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/70 sm:p-6">
      <div class="grid gap-4">
        {#each connectivityNotes as note}
          <article class="rounded-2xl border border-slate-100 bg-slate-50 p-4 transition duration-300 hover:-translate-y-0.5 hover:border-cyan-200 hover:bg-white dark:border-slate-800 dark:bg-slate-950/55 dark:hover:border-cyan-400/30">
            <h3 class="text-lg font-semibold text-slate-950 dark:text-white">{note.title}</h3>
            <p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{note.body}</p>
          </article>
        {/each}
      </div>

      <div class="mt-5 rounded-2xl border border-cyan-100 bg-cyan-50 px-4 py-4 dark:border-cyan-400/20 dark:bg-cyan-400/10">
        <p class="text-sm font-semibold text-cyan-900 dark:text-cyan-100">Why Dead-reckoning matters</p>
        <p class="mt-2 text-sm leading-6 text-cyan-950/75 dark:text-cyan-50/80">
          You get a clearer replay of the route: confirmed points where the tracker had coverage, stored updates
          uploaded after reconnection, and Dead-reckoning estimates that make coverage gaps easier to understand.
        </p>
      </div>
    </div>
  </section>

  <section class="bg-slate-950 px-4 py-20 text-white sm:px-6 lg:px-8">
    <div class="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_0.9fr] lg:items-center">
      <div>
        <span class="marketing-pill marketing-pill-dark">How it works</span>
        <h2 class="mt-5 max-w-2xl text-3xl font-semibold leading-tight sm:text-4xl">
          A clear customer experience backed by organised fleet operations.
        </h2>
        <p class="mt-5 max-w-2xl text-base leading-7 text-slate-300">
          Customers get simple access to the information they need. Behind that, Omni keeps track of customers,
          hubs, vehicles, trackers, SIMs, installations, invoices, maintenance notes, and support requests.
        </p>
      </div>

      <div class="grid grid-cols-2 gap-3">
        {#each platformAreas as area}
          <div class="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-4 text-sm font-medium text-white/84 backdrop-blur transition duration-300 hover:-translate-y-0.5 hover:bg-white/[0.1]">
            {area}
          </div>
        {/each}
      </div>
    </div>
  </section>

  <section class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <span class="marketing-pill">Explore</span>
        <h2 class="mt-5 text-3xl font-semibold text-slate-950 dark:text-white sm:text-4xl">
          Choose where to go next.
        </h2>
      </div>
      <a
        href="/enquiry"
        class="inline-flex w-fit rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-cyan-700 dark:bg-cyan-300 dark:text-slate-950 dark:hover:bg-white"
      >
        Start an enquiry
      </a>
    </div>

    <div class="mt-8 grid gap-5 lg:grid-cols-3">
      {#each journeys as item}
        <a
          href={item.href}
          class="group overflow-hidden rounded-[1.25rem] border border-slate-200 bg-white shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900/70"
        >
          <div class="overflow-hidden">
            <img src={item.image} alt="" class="h-56 w-full object-cover transition duration-700 group-hover:scale-[1.04]" />
          </div>
          <div class="p-5">
            <h3 class="text-xl font-semibold text-slate-950 dark:text-white">{item.title}</h3>
            <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p>
            <p class="mt-5 text-sm font-semibold text-cyan-700 dark:text-cyan-300">Open page</p>
          </div>
        </a>
      {/each}
    </div>
  </section>
</MarketingShell>
