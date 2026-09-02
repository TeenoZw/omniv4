<script lang="ts">
  import { onMount } from "svelte";
  import { marketingFooterGroups, marketingNav } from "$lib/marketing/site";

  export let title = "Omni Logistics";
  export let kicker = "Global-grade telematics, locally managed.";
  export let intro = "";
  export let image = "/landing/omni-fleet-yard.jpg";
  export let imageAlt = "Omni Logistics fleet operations";
  export let primaryAction = { href: "/enquiry", label: "Request a Quote" };
  export let secondaryAction = { href: "/portal", label: "Omni Eye Portal" };
  export let currentPath = "/";

  let mobileOpen = false;
  let scrolled = false;
  let factIndex = 0;

  const didYouKnowFacts = [
    {
      title: "A few minutes of idling every day can quietly turn into weeks of wasted engine time each year.",
      body:
        "Fleet owners often look for big events first, but small patterns such as harsh braking, long stops, late starts, and route drift are usually where the easiest savings are hiding.",
      label: "Small habits compound",
      value: "Visibility helps",
    },
    {
      title: "A vehicle does not need to be stolen for tracking to protect its value.",
      body:
        "Late recoveries, unauthorised trips, route changes, and after-hours movement can all cost money long before a vehicle is officially reported missing.",
      label: "Risk starts early",
      value: "Alerts matter",
    },
    {
      title: "The best fleet reports are usually boring, and that is the point.",
      body:
        "Consistent routes, predictable stop times, steady fuel use, and clean driver behaviour are signs that operations are under control.",
      label: "Predictability pays",
      value: "Control wins",
    },
    {
      title: "Speeding is only one part of driver behaviour.",
      body:
        "Harsh acceleration, harsh braking, cornering, idle time, and stop duration often tell a clearer story about vehicle wear and driver discipline.",
      label: "Behaviour has signals",
      value: "Patterns reveal it",
    },
    {
      title: "A tracker is most useful when someone is responsible for acting on the information.",
      body:
        "GPS data becomes valuable when alerts, reports, maintenance follow-ups, and customer support are part of the same operating routine.",
      label: "Data needs action",
      value: "Service closes the loop",
    },
    {
      title: "Geofences can protect more than a parking yard.",
      body:
        "They can show when a vehicle enters a customer site, leaves a delivery zone, reaches a workshop, or spends too long at a loading point.",
      label: "Places become events",
      value: "Geofences help",
    },
    {
      title: "Maintenance planning gets easier when mileage and movement are visible.",
      body:
        "Instead of waiting for breakdowns, fleets can use distance, usage, and operating patterns to plan service work before problems become expensive.",
      label: "Usage guides service",
      value: "Downtime drops",
    },
    {
      title: "A parked vehicle can still create cost.",
      body:
        "Idle fuel burn, unauthorised movement, battery issues, delayed dispatch, and missed service dates can all happen while a vehicle looks inactive.",
      label: "Inactive is not always safe",
      value: "Monitoring helps",
    },
    {
      title: "Good fleet visibility improves customer service, not just security.",
      body:
        "When teams know where vehicles are and what happened on a route, they can answer delivery, pickup, and support questions with more confidence.",
      label: "Better answers",
      value: "Better service",
    },
    {
      title: "The real benefit of tracking is often decision speed.",
      body:
        "When location, status, documents, support history, and billing context are easy to find, teams spend less time chasing updates.",
      label: "Less chasing",
      value: "Faster decisions",
    },
  ];

  $: currentFact = didYouKnowFacts[factIndex];

  onMount(() => {
    const handleScroll = () => {
      scrolled = window.scrollY > 12;
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });

    const factTimer = window.setInterval(() => {
      factIndex = (factIndex + 1) % didYouKnowFacts.length;
    }, 15000);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.clearInterval(factTimer);
    };
  });
</script>

<div class="min-h-screen bg-[#f6f8fb] text-slate-950 dark:bg-slate-950 dark:text-slate-50">
  <header class={`fixed left-0 right-0 top-0 z-40 transition-all duration-300 ${scrolled ? "border-b border-white/55 bg-white/86 shadow-sm backdrop-blur-2xl dark:border-white/10 dark:bg-slate-950/78" : "bg-transparent"}`}>
    <div class="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
      <a href="/" class="flex items-center gap-3" aria-label="Omni Logistics home">
        <img
          src="/brand/omni-industrial-solutions-logo.png"
          alt="Omni Industrial Solutions"
          class="h-[7.5rem] w-auto rounded-xl object-contain shadow-sm sm:h-[8.75rem]"
        />
      </a>

      <nav class="hidden items-center gap-6 text-sm font-medium lg:flex">
        {#each marketingNav as item}
          <a
            href={item.href}
            class={`transition ${currentPath === item.href ? "text-cyan-700 dark:text-cyan-300" : scrolled ? "text-slate-600 hover:text-slate-950 dark:text-slate-300 dark:hover:text-white" : "text-white/82 hover:text-white"}`}
          >
            {item.label}
          </a>
        {/each}
      </nav>

      <div class="hidden items-center gap-3 lg:flex">
        <a href={secondaryAction.href} class={`rounded-full border px-4 py-2 text-sm font-medium transition ${scrolled ? "border-slate-300/70 text-slate-700 hover:border-slate-500 hover:text-slate-950 dark:border-slate-700 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:text-white" : "border-white/35 bg-white/8 text-white backdrop-blur hover:bg-white/14"}`}>
          {secondaryAction.label}
        </a>
        <a href={primaryAction.href} class="rounded-full bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-sm transition hover:bg-white">
          {primaryAction.label}
        </a>
      </div>

      <button
        type="button"
        class={`inline-flex h-11 w-11 items-center justify-center rounded-full border backdrop-blur lg:hidden ${scrolled ? "border-slate-300/70 bg-white/70 text-slate-900 dark:border-slate-700 dark:bg-slate-900/70 dark:text-white" : "border-white/35 bg-white/10 text-white"}`}
        onclick={() => (mobileOpen = !mobileOpen)}
        aria-label="Toggle menu"
      >
        <span class="text-lg leading-none">{mobileOpen ? "×" : "☰"}</span>
      </button>
    </div>

    {#if mobileOpen}
      <div class="border-t border-white/60 bg-white/95 px-4 py-4 shadow-lg backdrop-blur-xl lg:hidden dark:border-slate-800 dark:bg-slate-950/95">
        <div class="flex flex-col gap-3">
          {#each marketingNav as item}
            <a
              href={item.href}
              class={`rounded-full px-4 py-2 text-sm font-medium ${currentPath === item.href ? "bg-cyan-100 text-cyan-800 dark:bg-cyan-500/15 dark:text-cyan-300" : "text-slate-700 dark:text-slate-200"}`}
              onclick={() => (mobileOpen = false)}
            >
              {item.label}
            </a>
          {/each}
          <div class="mt-2 flex flex-col gap-3">
            <a href={secondaryAction.href} class="rounded-full border border-slate-300/70 px-4 py-2 text-center text-sm font-medium text-slate-700 dark:border-slate-700 dark:text-slate-200">
              {secondaryAction.label}
            </a>
            <a href={primaryAction.href} class="rounded-full bg-slate-950 px-4 py-2 text-center text-sm font-semibold text-white dark:bg-cyan-400 dark:text-slate-950">
              {primaryAction.label}
            </a>
          </div>
        </div>
      </div>
    {/if}
  </header>

  <main class="relative">
    <section class="marketing-hero relative flex min-h-[92svh] items-end overflow-hidden pb-10 pt-28 sm:pb-12 lg:min-h-[88vh]">
      <img src={image} alt={imageAlt} class="absolute inset-0 h-full w-full object-cover" />
      <div class="absolute inset-0 bg-[linear-gradient(90deg,rgba(2,6,23,0.88),rgba(15,23,42,0.56)_45%,rgba(15,23,42,0.18)),linear-gradient(180deg,rgba(2,6,23,0.35),rgba(2,6,23,0.3)_55%,rgba(246,248,251,1))] dark:bg-[linear-gradient(90deg,rgba(2,6,23,0.92),rgba(15,23,42,0.62)_46%,rgba(15,23,42,0.24)),linear-gradient(180deg,rgba(2,6,23,0.45),rgba(2,6,23,0.36)_55%,rgba(2,6,23,1))]"></div>
      <div class="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-[#f6f8fb] to-transparent dark:from-slate-950"></div>

      <div class="relative mx-auto grid w-full max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-[minmax(0,0.92fr)_minmax(320px,0.5fr)] lg:items-end lg:px-8">
        <div class="marketing-reveal space-y-6 text-white">
          <p class="inline-flex rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-100 shadow-sm backdrop-blur">
          {kicker}
          </p>
          <div class="space-y-5">
            <h1 class="max-w-4xl text-4xl font-semibold leading-[1.04] sm:text-6xl lg:text-7xl">
              {title}
            </h1>
            {#if intro}
              <p class="max-w-2xl text-base leading-7 text-white/78 sm:text-lg">
                {intro}
              </p>
            {/if}
          </div>
          <div class="flex flex-wrap gap-3">
            <a href={primaryAction.href} class="rounded-full bg-cyan-300 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-950/20 transition hover:-translate-y-0.5 hover:bg-white">
              {primaryAction.label}
            </a>
            <a href={secondaryAction.href} class="rounded-full border border-white/30 bg-white/8 px-6 py-3 text-sm font-semibold text-white backdrop-blur transition hover:-translate-y-0.5 hover:bg-white/14">
              {secondaryAction.label}
            </a>
          </div>
        </div>

        <div class="marketing-reveal hidden rounded-[1.25rem] border border-white/18 bg-white/10 p-5 text-white shadow-2xl shadow-slate-950/20 backdrop-blur-2xl lg:block">
          <p class="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-100">Did you know?</p>
          <p class="mt-4 text-3xl font-semibold leading-tight" aria-live="polite">
            {currentFact.title}
          </p>
          <p class="mt-4 text-sm leading-6 text-white/72">
            {currentFact.body}
          </p>
          <div class="mt-5 overflow-hidden rounded-2xl border border-cyan-200/20 bg-slate-950/25 px-4 py-3">
            <div class="flex items-center justify-between text-sm">
              <span class="text-white/72">{currentFact.label}</span>
              <span class="font-semibold text-cyan-200">{currentFact.value}</span>
            </div>
            <div class="marketing-flow mt-4 h-1.5 rounded-full bg-white/15"></div>
          </div>
        </div>
      </div>
    </section>

    <slot />
  </main>

  <footer class="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
    <div class="rounded-[1.25rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/70 sm:p-8">
      <div class="grid gap-8 lg:grid-cols-[1.2fr_0.8fr_0.8fr]">
        <div>
          <img
            src="/brand/omni-industrial-solutions-logo.png"
            alt="Omni Industrial Solutions"
            class="h-40 w-auto rounded-xl object-contain shadow-sm"
          />
          <p class="mt-4 max-w-md text-sm leading-6 text-slate-600 dark:text-slate-300">
            Omni Logistics provides fleet tracking, installation coordination, customer support, and account management
            for businesses and organisations in Zimbabwe.
          </p>
        </div>
        {#each marketingFooterGroups as group}
          <div>
            <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">{group.title}</p>
            <div class="mt-4 flex flex-col gap-3 text-sm">
              {#each group.links as link}
                <a href={link.href} target={link.external ? "_blank" : undefined} rel={link.external ? "noreferrer" : undefined} class="text-slate-700 transition hover:text-slate-950 dark:text-slate-300 dark:hover:text-white">
                  {link.label}
                </a>
              {/each}
            </div>
          </div>
        {/each}
      </div>
      <div class="mt-8 flex flex-col gap-2 border-t border-slate-200/80 pt-6 text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400 sm:flex-row sm:items-center sm:justify-between">
        <span>info@omnilogistics.co.zw · +263 777 233 814</span>
        <span>© {new Date().getFullYear()} Omni Logistics. All rights reserved.</span>
      </div>
    </div>
  </footer>
</div>
