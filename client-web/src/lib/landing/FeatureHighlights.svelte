<section id="features" class="relative space-y-8 rounded-3xl border border-emerald-100 bg-gradient-to-br from-emerald-50 via-teal-100 to-sky-100 p-6 dark:border-slate-800 dark:bg-gradient-to-br dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 sm:p-8">
  <div
    class="absolute inset-0 -z-10 opacity-15"
    style="background-image: url('/landing/omni-truck-yard.jpg'); background-size: cover; background-position: center;"
  ></div>
  <div class="grid gap-6 lg:grid-cols-[2fr_3fr]">
    <div class="rounded-3xl border border-emerald-100 bg-emerald-50/70 p-5 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 sm:p-6">
      <p class="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-600">Everything You Need</p>
      <h3 class="text-xl font-bold text-slate-900 dark:text-white sm:text-2xl">What you are actually buying</h3>
      <p class="mt-3 text-base text-slate-600 dark:text-slate-300">
        This is a managed fleet intelligence service designed to reduce risk, not a DIY hardware transaction.
      </p>
      <dl class="mt-6 grid gap-4 text-sm text-slate-700">
        <div class="flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3 dark:bg-slate-800/80 dark:text-slate-200">
          <dt>Service model</dt>
          <dd class="font-semibold text-slate-900 dark:text-white">Managed</dd>
        </div>
        <div class="flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3 dark:bg-slate-800/80 dark:text-slate-200">
          <dt>Compliance posture</dt>
          <dd class="font-semibold text-slate-900 dark:text-white">Defined</dd>
        </div>
        <div class="flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3 dark:bg-slate-800/80 dark:text-slate-200">
          <dt>Support ownership</dt>
          <dd class="font-semibold text-slate-900 dark:text-white">Local</dd>
        </div>
      </dl>
    </div>
    <div class="grid gap-5 md:grid-cols-2">
      {#each [
        {
          title: 'Professional installation',
          copy: 'Proper wiring, clean installs, and hidden placement reduce tampering and downtime.',
        },
        {
          title: 'Managed SIM operations',
          copy: 'Connectivity, data top-ups, and network continuity are handled by Omni.',
        },
        {
          title: 'Platform intelligence',
          copy: 'Live operations, geofencing, playback, and reporting for growing fleets.',
        },
        {
          title: 'After-sales accountability',
          copy: 'Support, onboarding, subscription handling, and escalation stay with one local team.',
        },
      ] as item}
        <article class="rounded-3xl border border-emerald-100 bg-emerald-50/70 p-5 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 sm:p-6">
          <h4 class="text-lg font-semibold text-slate-900 dark:text-white">{item.title}</h4>
          <p class="mt-2 text-slate-600 dark:text-slate-300">{item.copy}</p>
        </article>
      {/each}
    </div>
  </div>
</section>
