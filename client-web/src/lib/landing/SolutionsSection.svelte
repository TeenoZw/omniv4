<script lang="ts">
  import Icon from "$lib/components/ui/Icon.svelte";
  import {
    faMapLocationDot,
    faShieldHalved,
    faChartLine,
  } from "@fortawesome/free-solid-svg-icons";

  const solutions = [
    {
      icon: faMapLocationDot,
      title: "Managed Connectivity",
      body: "SIM registration, data usage, and network reliability are managed for you end-to-end.",
    },
    {
      icon: faShieldHalved,
      title: "Data Protection Compliance",
      body: "Clear privacy policy, accountable local operations, and defined data handling processes.",
    },
    {
      icon: faChartLine,
      title: "Enterprise Fleet Insights",
      body: "Live tracking, geofencing, and operational reporting through the dedicated tracking portal.",
    },
  ];

  const gallery = [
    {
      src: "/landing/omni-mobile.jpg",
      alt: "Mobile tracking in the field",
    },
    {
      src: "/landing/omni-excavators.jpg",
      alt: "Construction fleet with excavators",
    },
    {
      src: "/landing/omni-loader.jpg",
      alt: "Heavy equipment loader on site",
    },
    {
      src: "/landing/omni-quarry.jpg",
      alt: "Quarry site with dump trucks and loader",
    },
  ];
  let galleryIndex = 0;

  const nextGallery = () => {
    galleryIndex = (galleryIndex + 1) % gallery.length;
  };

  const prevGallery = () => {
    galleryIndex = (galleryIndex - 1 + gallery.length) % gallery.length;
  };
</script>

<section id="solutions" class="relative space-y-10 rounded-3xl border border-cyan-100 bg-gradient-to-br from-cyan-50 via-sky-100 to-amber-50 p-6 dark:border-slate-800 dark:bg-gradient-to-br dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 sm:p-8">
  <div
    class="absolute inset-0 -z-10 opacity-15"
    style="background-image: url('/landing/omni-fleet-yard.jpg'); background-size: cover; background-position: center;"
  ></div>
  <div class="space-y-4 text-center">
    <p class="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-500">Solutions</p>
    <h2 class="text-2xl font-bold leading-tight text-slate-900 dark:text-white sm:text-3xl">
      Why managed service beats DIY tracking
    </h2>
    <p class="mx-auto max-w-3xl text-base text-slate-600 dark:text-slate-300 sm:text-lg">
      Generic online trackers focus on purchase price. Omni focuses on uptime, accountability, and long-term reliability.
    </p>
  </div>

  <div class="grid gap-5 md:grid-cols-3">
    {#each solutions as item (item.title)}
      <article class="group rounded-3xl border border-cyan-100 bg-white/70 p-5 shadow-sm transition hover:-translate-y-1 hover:border-cyan-200 hover:shadow-2xl backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 sm:p-6">
        <div class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700 dark:bg-slate-800 dark:text-cyan-200">
          <Icon icon={item.icon} className="h-5 w-5" />
        </div>
        <h3 class="mt-4 text-xl font-semibold text-slate-900 dark:text-white">{item.title}</h3>
        <p class="mt-2 text-base text-slate-600 dark:text-slate-300">{item.body}</p>
      </article>
    {/each}
  </div>

  <div class="rounded-3xl border border-cyan-100 bg-gradient-to-br from-white/70 via-cyan-50/70 to-sky-100/70 p-5 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/60 sm:p-6">
    <div class="overflow-hidden rounded-2xl border border-cyan-100 bg-white/80 dark:border-slate-800 dark:bg-slate-900/80">
      <div
        class="flex transition-transform duration-500"
        style={`transform: translateX(-${galleryIndex * 100}%);`}
      >
        {#each gallery as image (image.src)}
          <div class="w-full shrink-0">
            <img src={image.src} alt={image.alt} class="h-48 w-full object-cover sm:h-56" loading="lazy" />
          </div>
        {/each}
      </div>
    </div>
    <div class="mt-4 flex items-center justify-between">
      <button
        type="button"
        class="rounded-full border border-cyan-200 bg-white/80 px-3 py-1 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-200"
        on:click={prevGallery}
      >
        Prev
      </button>
      <div class="flex items-center gap-2">
        {#each gallery as _image, index (index)}
          <button
            type="button"
            class={`h-2 w-2 rounded-full ${
              index === galleryIndex
                ? "bg-cyan-500 dark:bg-cyan-300"
                : "bg-cyan-200 dark:bg-slate-600"
            }`}
            on:click={() => (galleryIndex = index)}
            aria-label={`Go to image ${index + 1}`}
          ></button>
        {/each}
      </div>
      <button
        type="button"
        class="rounded-full border border-cyan-200 bg-white/80 px-3 py-1 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-200"
        on:click={nextGallery}
      >
        Next
      </button>
    </div>
  </div>
</section>
