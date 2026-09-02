<svelte:head>
  <title>Omni Logistics · Industries</title>
</svelte:head>

<script lang="ts">
  import MarketingShell from "$lib/marketing/MarketingShell.svelte";

  const sectors = [
    {
      title: "Mining and heavy industry",
      copy: "Vehicle and equipment tracking for sites where downtime, misuse, and poor visibility are expensive.",
      image: "/landing/omni-quarry.jpg",
    },
    {
      title: "Transport and logistics",
      copy: "Fleet visibility, route review, driver accountability, and support for day-to-day transport operations.",
      image: "/landing/omni-truck-yard.jpg",
    },
    {
      title: "Construction and equipment",
      copy: "Tracking support for vehicles and equipment moving between sites, yards, and projects.",
      image: "/landing/omni-loader.jpg",
    },
    {
      title: "Utilities and field services",
      copy: "Better visibility for field teams, service vehicles, and work carried out away from the office.",
      image: "/landing/omni-mobile.jpg",
    },
    {
      title: "Government and public sector",
      copy: "Controlled access, clearer reporting, and better oversight for public fleet management.",
      image: "/landing/omni-fleet-yard.jpg",
    },
    {
      title: "Public transport operators",
      copy: "Route visibility, vehicle monitoring, and practical support for passenger transport operators.",
      image: "/landing/omni-excavators.jpg",
    },
  ];
</script>

<MarketingShell
  currentPath="/industries"
  title="Fleet visibility for different operating environments."
  kicker="Sector fit"
  intro="Omni supports businesses and organisations that need to know where their vehicles are, how they are being used, and when attention is required."
  image="/landing/omni-excavators.jpg"
  imageAlt="Heavy equipment and industrial fleet environment"
>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="grid gap-6 lg:grid-cols-3">
      {#each sectors as sector}
        <article class="group overflow-hidden rounded-[1.75rem] border border-white/70 bg-white/75 shadow-xl backdrop-blur transition hover:-translate-y-1 dark:border-slate-800 dark:bg-slate-900/75">
          <div class="overflow-hidden">
            <img src={sector.image} alt={sector.title} class="h-52 w-full object-cover transition duration-500 group-hover:scale-[1.04]" />
          </div>
          <div class="p-6">
            <h2 class="text-xl font-bold">{sector.title}</h2>
            <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{sector.copy}</p>
          </div>
        </article>
      {/each}
    </div>
  </section>

  <section class="mx-auto mt-10 max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="marketing-card">
      <span class="marketing-pill">Common outcomes</span>
      <div class="mt-5 grid gap-5 lg:grid-cols-4">
        {#each [
          "Operational visibility",
          "Asset protection and risk reduction",
          "Governance and compliance",
          "Performance intelligence",
        ] as item}
          <div class="rounded-[1.4rem] border border-slate-200/80 bg-slate-50 p-5 text-center text-sm font-semibold dark:border-slate-800 dark:bg-slate-950">
            {item}
          </div>
        {/each}
      </div>
    </div>
  </section>
</MarketingShell>
