<svelte:head>
  <title>Omni Logistics · Solutions</title>
</svelte:head>

<script lang="ts">
  import MarketingShell from "$lib/marketing/MarketingShell.svelte";

  const pillars = [
    {
      title: "Managed connectivity",
      body: "Omni helps manage tracker connectivity, SIM records, subscriptions, and service follow-up.",
    },
    {
      title: "Compliance-aligned operations",
      body: "Customer access, billing, support, and data handling are managed through a clear service process.",
    },
    {
      title: "Professional deployment",
      body: "Tracker stock, technician work, SIM assignment, and installation details are recorded from the start.",
    },
    {
      title: "Executive visibility",
      body: "Customers can see key fleet, support, document, and billing information without relying on scattered updates.",
    },
  ];

  const comparison = [
    ["Setup model", "DIY configuration", "Managed rollout and onboarding"],
    ["Support", "Usually self-service", "Locally accountable support"],
    ["Data handling", "Often unclear", "Defined operational accountability"],
    ["SIM and data operations", "Customer-managed", "Omni-managed"],
    ["Reporting depth", "Basic map view", "Structured operational insight"],
    ["Installation quality", "Varies widely", "Professional installation workflow"],
  ];
</script>

<MarketingShell
  currentPath="/solutions"
  title="Fleet tracking backed by accountable service."
  kicker="Managed fleet intelligence"
  intro="Omni supplies more than GPS hardware. We help customers set up, manage, and support their fleet tracking service properly."
  image="/landing/omni-mobile.jpg"
  imageAlt="Mobile field tracking and digital fleet visibility"
>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
      {#each pillars as item}
        <article class="marketing-card marketing-reveal">
          <h2 class="text-xl font-bold">{item.title}</h2>
          <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p>
        </article>
      {/each}
    </div>
  </section>

  <section class="mx-auto mt-10 max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="grid gap-6 lg:grid-cols-[1fr_1.15fr]">
      <article class="marketing-card">
        <span class="marketing-pill">Positioning</span>
        <h2 class="mt-4 text-3xl font-black tracking-tight">Omni is a managed fleet tracking service.</h2>
        <p class="mt-4 text-base leading-7 text-slate-600 dark:text-slate-300">
          We are not trying to be the cheapest tracker supplier. We focus on reliable setup, clear customer support,
          proper installation records, managed subscriptions, and long-term accountability.
        </p>
        <div class="mt-6 rounded-[1.5rem] bg-slate-950 p-6 text-white dark:bg-slate-900">
          <p class="text-sm leading-7 text-slate-200">
            Customers need confidence that the tracker is installed correctly, the account is active, support is available,
            and billing is handled by one accountable provider.
          </p>
        </div>
      </article>

      <article class="marketing-card overflow-hidden">
        <span class="marketing-pill">Comparison</span>
        <div class="mt-4 overflow-auto rounded-[1.5rem] border border-slate-200/80 dark:border-slate-800">
          <table class="w-full min-w-[560px] text-left text-sm">
            <thead class="bg-slate-100 dark:bg-slate-900">
              <tr>
                <th class="px-4 py-3 font-semibold">Category</th>
                <th class="px-4 py-3 font-semibold">Generic tracker</th>
                <th class="px-4 py-3 font-semibold">Omni Logistics</th>
              </tr>
            </thead>
            <tbody>
              {#each comparison as row}
                <tr class="border-t border-slate-200/80 dark:border-slate-800">
                  <td class="px-4 py-3 font-medium">{row[0]}</td>
                  <td class="px-4 py-3 text-slate-600 dark:text-slate-300">{row[1]}</td>
                  <td class="px-4 py-3 font-medium text-cyan-700 dark:text-cyan-300">{row[2]}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </article>
    </div>
  </section>
</MarketingShell>
