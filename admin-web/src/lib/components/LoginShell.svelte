<script>
  import { createEventDispatcher } from "svelte";
  import { login as loginApi } from "$lib/api/auth";
  import { sessionStore } from "$lib/stores/session";

  export let allowClose = true;

  const dispatch = createEventDispatcher();
  let email = "";
  let password = "";
  let loading = false;
  let errorMessage = "";

  async function handleSubmit(event) {
    event.preventDefault();
    loading = true;
    errorMessage = "";

    try {
      const data = await loginApi({ email, password });
      const normalizedRoles = (data?.roles ?? []).map((role) => `${role ?? ""}`.toLowerCase());
      const isInternalUser = normalizedRoles.includes("admin") || normalizedRoles.includes("technician");
      if (!isInternalUser) {
        errorMessage = "This account does not have access to the admin console. Please use the client portal instead.";
        return;
      }
      sessionStore.login(data);
      dispatch("success");
    } catch (error) {
      const apiMessage = error?.response?.data?.detail ?? error?.response?.data?.message;
      errorMessage = apiMessage ?? "Unable to sign in with the provided credentials.";
    } finally {
      loading = false;
    }
  }

  function handleClose() {
    if (!allowClose) {
      return;
    }
    dispatch("close");
  }
</script>

<div class="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur">
  <div
    class="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.2),_transparent_45%)] px-4 py-10"
    role="dialog"
    aria-modal="true"
    aria-label="Admin login"
  >
    <div class="relative grid w-full max-w-5xl gap-8 rounded-[40px] border border-white/10 bg-white/5 p-10 text-white shadow-[0_40px_80px_rgba(2,6,23,0.6)] lg:grid-cols-[1.1fr_0.9fr]">
      {#if allowClose}
        <button
          class="absolute right-6 top-6 rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs text-white/70 hover:bg-white/10"
          type="button"
          on:click={handleClose}
          aria-label="Close login"
        >
          Close
        </button>
      {/if}

      <section class="flex flex-col items-center text-center">
      <img src="/brand/omni-logo-full.svg" alt="Omni Industrial Solutions" class="h-64 w-auto object-contain md:h-80" />
      <h1 class="mt-4 text-4xl font-semibold">Admin Panel</h1>
    </section>

      <section class="rounded-3xl border border-white/10 bg-black/50 p-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-semibold">Sign in</h2>
        </div>
      </div>

      <form class="mt-6 space-y-5" on:submit|preventDefault={handleSubmit}>
        <label class="block text-sm text-white/80">
          <span class="text-xs uppercase tracking-widest text-white/60">Work Email</span>
          <input
            class="mt-1 w-full rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-base focus:border-primary focus:outline-none"
            type="email"
            name="email"
            autocomplete="email"
            bind:value={email}
            required
          />
        </label>

        <label class="block text-sm text-white/80">
          <span class="text-xs uppercase tracking-widest text-white/60">Password</span>
          <input
            class="mt-1 w-full rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-base focus:border-primary focus:outline-none"
            type="password"
            name="password"
            autocomplete="current-password"
            bind:value={password}
            required
            minlength="8"
          />
        </label>

        {#if errorMessage}
          <p class="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {errorMessage}
          </p>
        {/if}

        <button
          type="submit"
          class="w-full rounded-2xl bg-primary py-3 text-center text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/40 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={loading}
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
      </section>
    </div>
  </div>
</div>
