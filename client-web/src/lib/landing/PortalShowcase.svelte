<script lang="ts">
  import Icon from "$lib/components/ui/Icon.svelte";
  import { faCheck } from "@fortawesome/free-solid-svg-icons";
</script>

<section
  id="portal"
  class="relative grid gap-6 rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-sky-100 to-cyan-50 p-6 shadow-lg dark:border-slate-800 dark:bg-gradient-to-br dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 sm:gap-8 sm:p-8 lg:grid-cols-[3fr_2fr]"
>
  <div
    class="absolute inset-0 -z-10 opacity-15"
    style="background-image: url('/landing/omni-devices.png'); background-size: cover; background-position: center;"
  ></div>
  <div class="space-y-4">
    <p class="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-500">Omni Eye Portal</p>
    <h2 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">Onboarding, billing, and support in one place</h2>
    <p class="text-base text-slate-600 dark:text-slate-300 sm:text-lg">
      The Omni Eye Portal keeps your subscription, invoices, and support requests organized.
      Jump into the tracking portal for live tracking while Omni keeps onboarding and billing aligned.
    </p>
    <ul class="space-y-3 text-slate-600 dark:text-slate-300">
      <li class="flex items-start gap-3">
        <span class="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-cyan-100 text-cyan-600">
          <Icon icon={faCheck} className="h-3.5 w-3.5" />
        </span>
        Subscription status, invoices, and account contacts in one place.
      </li>
      <li class="flex items-start gap-3">
        <span class="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-cyan-100 text-cyan-600">
          <Icon icon={faCheck} className="h-3.5 w-3.5" />
        </span>
        Support requests and hardware notes tracked by Omni support.
      </li>
      <li class="flex items-start gap-3">
        <span class="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-cyan-100 text-cyan-600">
          <Icon icon={faCheck} className="h-3.5 w-3.5" />
        </span>
        Secure logins with a direct handoff to the tracking portal.
      </li>
    </ul>
    <div class="flex flex-wrap gap-3">
      <a
        href="/login"
        class="inline-flex items-center gap-2 rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-900"
      >
        Launch Omni Eye portal
        <span aria-hidden="true">→</span>
      </a>
      <a
        href="/tracking"
        target="_blank"
        rel="noreferrer"
        class="inline-flex items-center gap-2 rounded-full border px-5 py-2.5 text-sm font-semibold text-slate-900 dark:border-slate-700 dark:text-slate-100"
      >
        Open tracking portal
        <span aria-hidden="true">↗</span>
      </a>
    </div>
  </div>
  <div class="space-y-4">
    <div class="overflow-hidden rounded-3xl border border-slate-100 bg-white/80 shadow-xl">
      <img
        src="/landing/omni-devices.png"
        alt="Omni Eye portal preview on desktop and tablet"
        class="h-52 w-full object-cover sm:h-64"
        loading="lazy"
      />
    </div>
    <div class="rounded-3xl border border-slate-100 bg-slate-950/90 p-5 text-white shadow-2xl sm:p-6">
      <div class="flex items-center justify-between text-sm text-white/70">
        <p class="text-base font-semibold">What Omni Handles</p>
        <span class="rounded-full border border-white/20 px-3 py-1">Secure</span>
      </div>
      <div class="mt-5 grid gap-3 sm:grid-cols-2">
        {#each [
          { label: 'Onboarding & setup', tone: 'bg-cyan-500/20 text-cyan-200' },
          { label: 'Billing & subscriptions', tone: 'bg-emerald-500/20 text-emerald-200' },
          { label: 'Hardware & installs', tone: 'bg-amber-500/20 text-amber-200' },
          { label: 'Support & escalation', tone: 'bg-fuchsia-500/20 text-fuchsia-200' },
        ] as item}
          <div class={`rounded-2xl border border-white/10 px-4 py-3 text-sm ${item.tone}`}>
            {item.label}
          </div>
        {/each}
      </div>
      <div class="mt-6 rounded-2xl border border-white/20 bg-gradient-to-br from-cyan-500/30 to-fuchsia-500/30 p-4 text-sm">
        <p>"Monitor, secure, and optimize your fleet with Omni Eye."</p>
        <p class="mt-2 font-semibold">— Omni Logistics</p>
      </div>
    </div>
  </div>
</section>
