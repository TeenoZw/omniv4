<script lang="ts">
  import { onMount } from "svelte";
  import {
    createPortalSupportTicket,
    fetchPortalCurrentCustomer,
    fetchPortalDashboardSummary,
    fetchPortalDocuments,
    fetchPortalInvoices,
    fetchPortalSupportTickets,
    fetchPortalVehicles,
    type PortalCurrentCustomer,
    type PortalDashboardSummary,
    type PortalDocument,
    type PortalInvoice,
    type PortalTicket,
    type PortalVehicle,
  } from "$lib/api/portal";
  import { frappeLogin } from "$lib/api/frappe";

  const adminUrl = import.meta.env.VITE_ADMIN_URL || "http://development.localhost:8000";

  let loading = true;
  let signingIn = false;
  let submittingTicket = false;
  let errorMessage = "";
  let loginMessage = "";
  let ticketMessage = "";
  let loginEmail = "";
  let loginPassword = "";
  let currentCustomer: PortalCurrentCustomer | null = null;
  let summary: PortalDashboardSummary | null = null;
  let vehicles: PortalVehicle[] = [];
  let invoices: PortalInvoice[] = [];
  let documents: PortalDocument[] = [];
  let tickets: PortalTicket[] = [];
  let supportSubject = "";
  let supportDescription = "";
  let supportPriority: "Low" | "Medium" | "High" | "Urgent" = "Medium";

  $: signInUrl = `${adminUrl.replace(/\/$/, "")}/login`;
  $: isSignedOut =
    errorMessage.toLowerCase().includes("log in") ||
    errorMessage.toLowerCase().includes("login") ||
    errorMessage.toLowerCase().includes("not whitelisted") ||
    errorMessage.toLowerCase().includes("permission");
  $: isUnlinkedAccount =
    errorMessage.toLowerCase().includes("no customer account is linked") ||
    errorMessage.toLowerCase().includes("do not have access");

  const statCards = () => [
    {
      label: "Vehicles",
      value: summary?.vehicles.total ?? 0,
      detail: `${summary?.vehicles.online ?? 0} online, ${summary?.vehicles.offline ?? 0} offline`,
    },
    {
      label: "Outstanding",
      value: money(summary?.invoices.outstanding_total ?? 0),
      detail: `${summary?.invoices.open_count ?? 0} open invoices`,
    },
    {
      label: "Support",
      value: summary?.support.open_tickets ?? 0,
      detail: "open tickets",
    },
    {
      label: "Documents",
      value: summary?.documents.total ?? 0,
      detail: `${summary?.documents.expiring_soon ?? 0} expiring soon`,
    },
  ];

  onMount(() => {
    void loadPortal();
  });

  async function loadPortal() {
    loading = true;
    errorMessage = "";
    try {
      const customerResponse = await fetchPortalCurrentCustomer();
      const [summaryResponse, vehicleResponse, invoiceResponse, documentResponse, ticketResponse] = await Promise.all([
        fetchPortalDashboardSummary(),
        fetchPortalVehicles(),
        fetchPortalInvoices(),
        fetchPortalDocuments(),
        fetchPortalSupportTickets(),
      ]);

      currentCustomer = customerResponse;
      summary = summaryResponse;
      vehicles = vehicleResponse.vehicles;
      invoices = invoiceResponse.invoices;
      documents = documentResponse.documents;
      tickets = ticketResponse.tickets;
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "Unable to load the customer portal.";
    } finally {
      loading = false;
    }
  }

  async function submitTicket() {
    if (submittingTicket || !supportSubject.trim()) return;
    submittingTicket = true;
    ticketMessage = "";
    try {
      const ticket = await createPortalSupportTicket({
        subject: supportSubject.trim(),
        description: supportDescription.trim(),
        priority: supportPriority,
      });
      ticketMessage = `Support ticket ${ticket.name} was created.`;
      supportSubject = "";
      supportDescription = "";
      supportPriority = "Medium";
      tickets = (await fetchPortalSupportTickets()).tickets;
      summary = await fetchPortalDashboardSummary();
    } catch (error) {
      ticketMessage = error instanceof Error ? error.message : "Unable to create support ticket.";
    } finally {
      submittingTicket = false;
    }
  }

  async function submitLogin() {
    if (signingIn || !loginEmail.trim() || !loginPassword) return;
    signingIn = true;
    loginMessage = "";
    errorMessage = "";
    try {
      await frappeLogin(loginEmail.trim(), loginPassword);
      loginPassword = "";
      await loadPortal();
    } catch (error) {
      loginMessage = cleanError(error instanceof Error ? error.message : "Unable to sign in.");
    } finally {
      signingIn = false;
    }
  }

  function cleanError(value: string) {
    if (!value) return "Unable to complete the request.";
    if (value.includes("not whitelisted") || value.includes("Login to access")) {
      return "Please sign in with your Omni customer account to continue.";
    }
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        const messages = parsed
          .map((item) => {
            try {
              return JSON.parse(item)?.message;
            } catch {
              return item;
            }
          })
          .filter(Boolean);
        if (messages.length) return stripHtml(messages.join(" "));
      }
    } catch {
      // Fall through and strip any server HTML below.
    }
    return stripHtml(value);
  }

  function stripHtml(value: string) {
    return value.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  }

  function money(value: number) {
    return new Intl.NumberFormat("en-ZW", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(value || 0);
  }

  function vehicleLabel(vehicle: PortalVehicle) {
    return vehicle.display_name || vehicle.registration_number || vehicle.name;
  }

  function formatDate(value?: string | null) {
    if (!value) return "Not set";
    const parsed = new Date(value.replace(" ", "T"));
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat("en-ZW", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(parsed);
  }
</script>

<svelte:head>
  <title>Omni Logistics · Customer Portal</title>
</svelte:head>

<section class="min-h-screen bg-[#f5f8fb] text-slate-950">
  <header class="border-b border-slate-200 bg-white">
    <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
      <a href="/" aria-label="Omni Logistics home">
        <img src="/brand/omni-logo-horizontal.svg" alt="Omni Industrial Solutions" class="h-14 w-auto sm:h-16" />
      </a>
      <nav class="flex flex-wrap items-center gap-2 text-sm font-semibold">
        <a href="/" class="rounded-full px-4 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950">Website</a>
        <a href="/tracking" class="rounded-full px-4 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950">Tracking</a>
        <a href="mailto:support@omnilogistics.co.zw" class="rounded-full bg-slate-950 px-5 py-2.5 text-white transition hover:bg-cyan-700">Support</a>
      </nav>
    </div>
  </header>

  <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
    {#if loading}
      <div class="grid min-h-[60vh] place-items-center">
        <div class="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
          <p class="text-sm font-semibold text-cyan-700">Loading Omni Eye Portal</p>
          <p class="mt-2 text-sm text-slate-600">Checking your customer account and fleet records.</p>
        </div>
      </div>
    {:else if errorMessage}
      <div class="grid min-h-[60vh] place-items-center">
        <div class="w-full max-w-xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-700">Omni Eye Portal</p>
          <h1 class="mt-3 text-2xl font-bold text-slate-950">
            {isSignedOut ? "Sign in to continue" : "Portal could not load"}
          </h1>
          {#if isSignedOut}
            <p class="mt-3 text-sm leading-6 text-slate-600">
              Use the email and password issued for your Omni customer account. This portal is separate from the
              public website and only shows records linked to your customer profile.
            </p>
            <form class="mt-5 space-y-4" on:submit|preventDefault={submitLogin}>
              <label class="block text-sm font-medium text-slate-700">
                Email address
                <input bind:value={loginEmail} type="email" autocomplete="username" required class="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600" placeholder="name@example.com" />
              </label>
              <label class="block text-sm font-medium text-slate-700">
                Password
                <input bind:value={loginPassword} type="password" autocomplete="current-password" required class="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600" placeholder="Your password" />
              </label>
              {#if loginMessage}
                <p class="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{loginMessage}</p>
              {/if}
              <div class="flex flex-wrap gap-3">
                <button type="submit" disabled={signingIn} class="rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700 disabled:opacity-50">
                  {signingIn ? "Signing in..." : "Sign In"}
                </button>
                <a href={signInUrl} class="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-500">
                  Admin Sign In
                </a>
              </div>
            </form>
          {:else if isUnlinkedAccount}
            <p class="mt-3 text-sm leading-6 text-slate-600">
              Your sign-in works, but this user is not linked to a customer fleet profile yet. Ask Omni Support to link
              the user to the correct hub or customer account.
            </p>
            <div class="mt-5 flex flex-wrap gap-3">
              <a href="mailto:support@omnilogistics.co.zw" class="rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700">
                Contact Support
              </a>
              <button type="button" class="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-500" on:click={loadPortal}>
                Retry
              </button>
            </div>
          {:else}
            <p class="mt-3 text-sm leading-6 text-slate-600">{cleanError(errorMessage)}</p>
            <div class="mt-5 flex flex-wrap gap-3">
              <button type="button" class="rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700" on:click={loadPortal}>
                Retry
              </button>
              <a href="mailto:support@omnilogistics.co.zw" class="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-500">
                Contact Support
              </a>
            </div>
          {/if}
        </div>
      </div>
    {:else}
      <div class="space-y-6">
        <section class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-700">Customer Portal</p>
              <h1 class="mt-2 text-2xl font-bold text-slate-950 sm:text-3xl">
                {currentCustomer?.customer.display_name}
              </h1>
              <p class="mt-2 text-sm text-slate-600">
                {currentCustomer?.user.full_name || currentCustomer?.user.email} · Omni Eye Portal
              </p>
            </div>
            <button type="button" class="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-500" on:click={loadPortal}>
              Refresh
            </button>
          </div>
        </section>

        <section class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {#each statCards() as stat}
            <article class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <p class="text-sm font-medium text-slate-500">{stat.label}</p>
              <p class="mt-2 text-2xl font-bold text-slate-950">{stat.value}</p>
              <p class="mt-1 text-xs text-slate-500">{stat.detail}</p>
            </article>
          {/each}
        </section>

        <section class="grid gap-6 xl:grid-cols-[1.45fr_0.9fr]">
          <div class="space-y-6">
            <article class="rounded-lg border border-slate-200 bg-white shadow-sm">
              <div class="border-b border-slate-200 px-5 py-4">
                <h2 class="text-lg font-bold text-slate-950">Vehicles</h2>
              </div>
              <div class="divide-y divide-slate-100">
                {#if vehicles.length}
                  {#each vehicles as vehicle}
                    <div class="grid gap-4 px-5 py-4 md:grid-cols-[1fr_auto]">
                      <div>
                        <p class="font-semibold text-slate-950">{vehicleLabel(vehicle)}</p>
                        <p class="mt-1 text-sm text-slate-500">
                          {vehicle.registration_number} · {[vehicle.make, vehicle.model].filter(Boolean).join(" ") || vehicle.vehicle_type || "Vehicle"}
                        </p>
                      </div>
                      <div class="flex flex-wrap items-center gap-2 md:justify-end">
                        <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{vehicle.status || "Unknown"}</span>
                        {#if vehicle.latest_telematics}
                          <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                            {vehicle.latest_telematics.last_sync_status || "Linked"}
                          </span>
                          <span class="text-xs text-slate-500">
                            {vehicle.latest_telematics.speed ?? 0} km/h · {formatDate(vehicle.latest_telematics.last_seen)}
                          </span>
                        {:else}
                          <span class="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">Not linked</span>
                        {/if}
                      </div>
                    </div>
                  {/each}
                {:else}
                  <p class="px-5 py-8 text-sm text-slate-500">No vehicles are linked to this customer account yet.</p>
                {/if}
              </div>
            </article>

            <article class="rounded-lg border border-slate-200 bg-white shadow-sm">
              <div class="border-b border-slate-200 px-5 py-4">
                <h2 class="text-lg font-bold text-slate-950">Invoices</h2>
              </div>
              <div class="divide-y divide-slate-100">
                {#if invoices.length}
                  {#each invoices as invoice}
                    <div class="grid gap-3 px-5 py-4 sm:grid-cols-[1fr_auto]">
                      <div>
                        <p class="font-semibold text-slate-950">{invoice.name}</p>
                        <p class="mt-1 text-sm text-slate-500">Due {formatDate(invoice.due_date)} · {invoice.status || "Status pending"}</p>
                      </div>
                      <div class="text-left sm:text-right">
                        <p class="font-semibold text-slate-950">{money(invoice.grand_total ?? 0)}</p>
                        <p class="text-xs text-slate-500">Outstanding {money(invoice.outstanding_amount ?? 0)}</p>
                      </div>
                    </div>
                  {/each}
                {:else}
                  <p class="px-5 py-8 text-sm text-slate-500">No submitted invoices are available for this account.</p>
                {/if}
              </div>
            </article>
          </div>

          <aside class="space-y-6">
            <article class="rounded-lg border border-slate-200 bg-white shadow-sm">
              <div class="border-b border-slate-200 px-5 py-4">
                <h2 class="text-lg font-bold text-slate-950">Support</h2>
              </div>
              <form class="space-y-4 p-5" on:submit|preventDefault={submitTicket}>
                <label class="block text-sm font-medium text-slate-700">
                  Subject
                  <input bind:value={supportSubject} required class="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600" placeholder="What do you need help with?" />
                </label>
                <label class="block text-sm font-medium text-slate-700">
                  Priority
                  <select bind:value={supportPriority} class="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600">
                    <option>Low</option>
                    <option>Medium</option>
                    <option>High</option>
                    <option>Urgent</option>
                  </select>
                </label>
                <label class="block text-sm font-medium text-slate-700">
                  Details
                  <textarea bind:value={supportDescription} rows="4" class="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600" placeholder="Add vehicle, tracker, or invoice context if relevant."></textarea>
                </label>
                {#if ticketMessage}
                  <p class="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">{ticketMessage}</p>
                {/if}
                <button type="submit" disabled={submittingTicket} class="w-full rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700 disabled:opacity-50">
                  {submittingTicket ? "Creating ticket..." : "Create Support Ticket"}
                </button>
              </form>
              <div class="border-t border-slate-200 px-5 py-4">
                {#if tickets.length}
                  <div class="space-y-3">
                    {#each tickets.slice(0, 4) as ticket}
                      <div>
                        <p class="text-sm font-semibold text-slate-950">{ticket.subject}</p>
                        <p class="text-xs text-slate-500">{ticket.status || "Open"} · {ticket.priority || "Medium"}</p>
                      </div>
                    {/each}
                  </div>
                {:else}
                  <p class="text-sm text-slate-500">No support tickets are open for this account.</p>
                {/if}
              </div>
            </article>

            <article class="rounded-lg border border-slate-200 bg-white shadow-sm">
              <div class="border-b border-slate-200 px-5 py-4">
                <h2 class="text-lg font-bold text-slate-950">Documents</h2>
              </div>
              <div class="divide-y divide-slate-100">
                {#if documents.length}
                  {#each documents.slice(0, 6) as document}
                    <div class="px-5 py-4">
                      <p class="text-sm font-semibold text-slate-950">{document.title || document.name}</p>
                      <p class="mt-1 text-xs text-slate-500">{document.document_type || "Document"} · Expires {formatDate(document.expires_on)}</p>
                      {#if document.file_url}
                        <a href={document.file_url} class="mt-2 inline-flex text-xs font-semibold text-cyan-700 hover:text-cyan-900">Open document</a>
                      {/if}
                    </div>
                  {/each}
                {:else}
                  <p class="px-5 py-8 text-sm text-slate-500">No portal-visible documents are available yet.</p>
                {/if}
              </div>
            </article>
          </aside>
        </section>
      </div>
    {/if}
  </main>
</section>
