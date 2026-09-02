<svelte:head>
  <title>Omni Logistics · Platform</title>
</svelte:head>

<script lang="ts">
  import MarketingShell from "$lib/marketing/MarketingShell.svelte";

  const workflows = [
    "Customer enquiry and needs review",
    "Customer account and access setup",
    "Subscription activation and billing",
    "Technician job records and installation details",
    "Support, service follow-up, and account updates",
  ];

  const features = [
    {
      title: "Omni Eye portal",
      body: "Customer access to fleet records, support requests, documents, invoices, and subscription information.",
    },
    {
      title: "Admin control surface",
      body: "Internal tools for managing customers, hubs, vehicles, installations, tracker stock, SIMs, billing, and support.",
    },
    {
      title: "Technician workflows",
      body: "Installation records for assigned technicians, tracker details, SIM assignment, work notes, and customer signoff.",
    },
  ];
</script>

<MarketingShell
  currentPath="/platform"
  title="A service platform for fleet tracking operations."
  kicker="Portal architecture"
  intro="Omni connects the customer portal, internal admin tools, technician workflows, and tracking access so the service is easier to manage."
  image="/landing/omni-devices.png"
  imageAlt="Omni Eye portal screen preview"
>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="grid gap-6 lg:grid-cols-[1fr_1.15fr]">
      <article class="marketing-card">
        <span class="marketing-pill">Core flow</span>
        <h2 class="mt-4 text-3xl font-black tracking-tight">From enquiry to active tracking.</h2>
        <div class="mt-6 space-y-3">
          {#each workflows as step, index}
            <div class="flex items-start gap-4 rounded-[1.5rem] border border-slate-200/80 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
              <span class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cyan-600 text-sm font-bold text-white dark:bg-cyan-400 dark:text-slate-950">
                {index + 1}
              </span>
              <p class="pt-2 text-sm leading-6 text-slate-700 dark:text-slate-300">{step}</p>
            </div>
          {/each}
        </div>
      </article>

      <div class="space-y-5">
        {#each features as feature}
          <article class="marketing-card">
            <h3 class="text-2xl font-bold">{feature.title}</h3>
            <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{feature.body}</p>
          </article>
        {/each}
      </div>
    </div>
  </section>

  <section class="mx-auto mt-10 max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="marketing-card overflow-hidden">
      <div class="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div class="space-y-4">
          <span class="marketing-pill">Customer experience</span>
          <h2 class="text-3xl font-black tracking-tight">Clear fleet records, billing visibility, and direct support access.</h2>
          <p class="text-base leading-7 text-slate-600 dark:text-slate-300">
            Customers should not need to understand internal admin screens. They should be able to see their vehicles,
            documents, invoices, subscription status, and support requests in one place.
          </p>
          <a href="/login" class="inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-700 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300">
            Open Omni Eye Portal
          </a>
        </div>
        <div class="overflow-hidden rounded-[1.6rem] border border-slate-200/80 dark:border-slate-800">
          <img src="/landing/omni-dashboard.png" alt="Operations dashboard" class="h-full w-full object-cover" />
        </div>
      </div>
    </div>
  </section>
</MarketingShell>
