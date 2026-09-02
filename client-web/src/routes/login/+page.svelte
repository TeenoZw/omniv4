<script lang="ts">
  const adminUrl = import.meta.env.VITE_ADMIN_URL || "http://development.localhost:8000";
  const portalUrl = import.meta.env.VITE_PORTAL_URL || "/portal";

  $: signInUrl = `${adminUrl.replace(/\/$/, "")}/login`;
</script>

<svelte:head>
  <title>Omni Logistics · Customer Sign In</title>
</svelte:head>

<section class="mx-auto grid min-h-[calc(100vh-5rem)] max-w-5xl place-items-center px-4 py-10 sm:px-6 lg:px-8">
  <div class="grid w-full gap-8 rounded-lg border border-slate-200 bg-white p-6 shadow-lg lg:grid-cols-[1.05fr_0.95fr] lg:p-8">
    <div class="space-y-5">
      <a href="/" class="inline-flex text-sm font-semibold text-slate-600 transition hover:text-slate-950">Back to website</a>
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-700">Omni Eye Portal</p>
        <h1 class="mt-3 text-3xl font-bold text-slate-950 sm:text-4xl">Sign in with your Omni account</h1>
        <p class="mt-3 text-sm leading-6 text-slate-600">
          Use your Omni account to access your customer portal. After signing in, you can view your vehicles,
          tracker status, invoices, documents, and support requests.
        </p>
      </div>
      <div class="flex flex-wrap gap-3">
        <a href={signInUrl} class="rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700">
          Continue to Sign In
        </a>
        <a href={portalUrl} class="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-500">
          Open Portal
        </a>
      </div>
    </div>

    <div class="rounded-lg border border-slate-200 bg-slate-50 p-5">
      <img src="/omni-eye-logo.png" alt="Omni Eye Portal" class="mx-auto h-auto w-full max-w-sm" />
      <div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        <div class="rounded-md bg-white p-4 shadow-sm">
          <p class="text-sm font-semibold text-slate-950">Customer-scoped access</p>
          <p class="mt-1 text-xs leading-5 text-slate-500">Your portal shows records linked to your Omni customer account.</p>
        </div>
        <div class="rounded-md bg-white p-4 shadow-sm">
          <p class="text-sm font-semibold text-slate-950">One business record</p>
          <p class="mt-1 text-xs leading-5 text-slate-500">Fleet records, invoices, support, and documents are kept together.</p>
        </div>
      </div>
    </div>
  </div>
</section>
