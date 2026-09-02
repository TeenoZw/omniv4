<section id="comparison" class="relative overflow-hidden rounded-3xl border border-sky-100 bg-gradient-to-br from-sky-50 via-cyan-50 to-blue-100 p-6 shadow-xl dark:border-slate-800 dark:bg-gradient-to-br dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 sm:p-8">
  <div class="space-y-4">
    <p class="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-600">Corporate Backbone</p>
    <h2 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">
      Structured fleet intelligence infrastructure for control, compliance, and performance optimization
    </h2>
    <p class="max-w-3xl text-base text-slate-700 dark:text-slate-300">
      Global-grade telematics technology, locally managed for Zimbabwean operations.
    </p>
  </div>

  <div class="mt-6 grid gap-5 md:grid-cols-2">
    {#each [
      {
        title: "Operational Visibility",
        body: "Real-time tracking, historical trip data, route optimization, centralized monitoring, and multi-level account structures powered by enterprise backend infrastructure.",
      },
      {
        title: "Asset Protection & Risk Reduction",
        body: "Industrial-grade hardware with tamper alerts, ignition monitoring, geofence breach alerts, panic workflows, and fuel monitoring capability.",
      },
      {
        title: "Governance & Compliance",
        body: "Role-based access, audit-ready reporting, data protection compliance alignment, local accountability, structured billing, and defined SLA-based service ownership.",
      },
      {
        title: "Performance Intelligence",
        body: "Idling analysis, overspeed analytics, driver scoring, maintenance scheduling, executive KPI dashboards, and exportable management reporting.",
      },
    ] as pillar}
      <article class="rounded-3xl border border-slate-200 bg-white/80 p-5 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 sm:p-6">
        <h3 class="text-lg font-semibold text-slate-900 dark:text-white">{pillar.title}</h3>
        <p class="mt-2 text-sm text-slate-700 dark:text-slate-300">{pillar.body}</p>
      </article>
    {/each}
  </div>

  <div class="mt-8 rounded-3xl border border-slate-200 bg-white/80 p-5 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 sm:p-6">
    <p class="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-600">Industries We Support</p>
    <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {#each [
        { title: "Mining & Heavy Industry", copy: "High-value asset monitoring and operational risk control." },
        { title: "Transport & Logistics", copy: "Route efficiency, driver performance, and fuel oversight." },
        { title: "Utilities & Field Services", copy: "Dispatch visibility and field team accountability." },
        { title: "Construction & Heavy Equipment", copy: "Mobile asset protection and equipment utilization." },
        { title: "Government & Public Sector", copy: "Structured governance and transparent reporting." },
        { title: "Public Transport Operators", copy: "Passenger safety monitoring and route compliance." },
      ] as sector}
        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-950">
          <p class="font-semibold text-slate-900 dark:text-white">{sector.title}</p>
          <p class="mt-1 text-slate-600 dark:text-slate-300">{sector.copy}</p>
        </div>
      {/each}
    </div>
  </div>
</section>
