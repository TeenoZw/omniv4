<script>
  import { createEventDispatcher } from "svelte";
  import { sessionStore } from "$lib/stores/session";

  const ADMIN_ROLE_ALIASES = ["admin", "omni-admin", "system_admin"];
  const planCapabilities = {
    Individual: [
      "Single-operator onboarding support",
      "Standard billing + support access",
      "Wialon tracking handoff"
    ],
    Business: [
      "Multi-operator onboarding support",
      "Priority billing + support routing",
      "Wialon tracking handoff"
    ]
  };

  const dispatch = createEventDispatcher();
  let selectedHubId = null;

  $: session = $sessionStore;
  $: normalizedRoles = (session?.roles ?? [])
    .map((role) => (role ?? "").toString().trim().toLowerCase())
    .filter(Boolean);
  $: isOmniAdmin = normalizedRoles.some((role) => ADMIN_ROLE_ALIASES.includes(role));
  $: hubs = session?.hubs ?? [];
  $: if (!selectedHubId && hubs.length > 0) {
    selectedHubId = session?.currentHubId ?? hubs[0]?.id ?? null;
  }

  $: if (selectedHubId && hubs.length > 0 && !hubs.some((hub) => hub.id === selectedHubId)) {
    selectedHubId = hubs[0]?.id ?? null;
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (!selectedHubId) {
      return;
    }
    sessionStore.selectHub(selectedHubId);
    dispatch("selected", { hubId: selectedHubId });
  }

  function formatPlan(plan) {
    if (!plan) return "Individual";
    const normalized = plan.toString().trim();
    if (!normalized) return "Individual";
    const lowered = normalized.toLowerCase();
    if (["basic", "free", "individual"].includes(lowered)) return "Individual";
    if (["pro", "enterprise", "business"].includes(lowered)) return "Business";
    const capitalized = normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
    return capitalized;
  }
</script>

<div class="fixed inset-0 z-40 bg-black/80 backdrop-blur">
  <div class="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-6 py-10 text-white">
    <header class="text-center">
      <p class="text-xs uppercase tracking-[0.5em] text-primary">Workflow · Authentication & Hub Selection</p>
      <h2 class="mt-4 text-4xl font-semibold">Choose a Hub Context</h2>
      <p class="mt-3 text-sm text-white/70">
        Client hub operators must select a provisioned hub before the dashboard unlocks (Onboarding Workflow Step #3).
        Each tile mirrors the plan, role, and capabilities assigned by the system admin.
        {#if isOmniAdmin}
          <span class="mt-2 block text-xs text-white/60">
            You are signed in as the Omni Admin, so hub selection is optional—use this picker when validating client hubs.
          </span>
        {/if}
      </p>
    </header>

    <form class="grid gap-4 md:grid-cols-2" on:submit|preventDefault={handleSubmit}>
      {#each hubs as hub (hub.id)}
        {@const plan = formatPlan(hub?.tier)}
        <label class={`relative flex cursor-pointer flex-col gap-4 rounded-3xl border ${hub.id === selectedHubId ? "border-primary bg-primary/10" : "border-white/10 bg-black/50"} p-6 shadow-lg shadow-black/20 transition focus-within:border-primary`}>
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-lg font-semibold">{hub?.name ?? "Hub"}</p>
              <p class="text-xs uppercase tracking-widest text-white/60">{hub?.id}</p>
            </div>
            <span class="rounded-full border border-white/20 px-3 py-1 text-xs text-white/80">{hub?.role ?? "viewer"}</span>
          </div>

          <div class="flex flex-wrap gap-2 text-xs">
            <span class="rounded-full bg-white/10 px-3 py-1 uppercase tracking-widest">{plan}</span>
            <span class="rounded-full bg-white/5 px-3 py-1 text-white/70">Disposition: {hub?.disposition ?? "Active"}</span>
          </div>

          <ul class="text-sm text-white/80">
            {#each planCapabilities[plan] ?? planCapabilities.Individual as capability (capability)}
              <li class="flex items-start gap-2 py-1">
                <span class="mt-1 h-1.5 w-1.5 rounded-full bg-primary"></span>
                <span>{capability}</span>
              </li>
            {/each}
          </ul>

          <input
            class="sr-only"
            type="radio"
            name="hub"
            value={hub.id}
            bind:group={selectedHubId}
            aria-label={`Activate ${hub?.name ?? "hub"}`}
          />
        </label>
      {/each}

      {#if hubs.length === 0}
        <p class="rounded-3xl border border-dashed border-white/10 bg-black/50 p-6 text-sm text-white/70">
          No hubs assigned yet. Return to Onboarding Stage 1 to create hub records.
        </p>
      {/if}

      <div class="md:col-span-2">
        <button
          type="submit"
          class="w-full rounded-3xl bg-primary py-4 text-base font-semibold text-primary-foreground shadow-xl shadow-primary/30 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!selectedHubId}
        >
          Proceed to Hub Dashboard
        </button>
      </div>
    </form>
  </div>
</div>
