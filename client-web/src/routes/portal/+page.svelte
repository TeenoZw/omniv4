<script lang="ts">
  import { onMount } from "svelte";
  import {
    acceptPortalLegalTerms,
    createPortalSupportTicket,
    fetchPortalCurrentCustomer,
    fetchPortalDashboardSummary,
    fetchPortalDocuments,
    fetchPortalInvoices,
    fetchPortalSupportTicketDetail,
    fetchPortalSupportTickets,
    fetchPortalVehicleDetail,
    fetchPortalVehicles,
    type PortalCurrentCustomer,
    type PortalDashboardSummary,
    type PortalDocument,
    type PortalInvoice,
    type PortalTicket,
    type PortalTicketDetail,
    type PortalVehicle,
    type PortalVehicleDetail,
  } from "$lib/api/portal";
  import { frappeLogin, frappeLogout, isFrappeAuthenticationError } from "$lib/api/frappe";

  const adminUrl = import.meta.env.VITE_ADMIN_URL || "http://development.localhost:8000";

  let loading = true;
  let signingIn = false;
  let acceptingLegal = false;
  let submittingTicket = false;
  let errorMessage = "";
  let loginMessage = "";
  let legalMessage = "";
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
  let selectedVehicle: PortalVehicleDetail | null = null;
  let selectedTicket: PortalTicketDetail | null = null;
  let detailLoading = "";
  let termsAccepted = false;
  let privacyAccepted = false;
  let idleWarning = false;
  let idleSecondsRemaining = 60;
  let idleTimeout: ReturnType<typeof setTimeout> | null = null;
  let idleCountdown: ReturnType<typeof setInterval> | null = null;
  const idleLimitMs = 15 * 60 * 1000;
  const idleWarningMs = 60 * 1000;

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
    const activityEvents = ["pointerdown", "keydown", "scroll", "touchstart"];
    const recordActivity = () => {
      if (!idleWarning) resetIdleTimer();
    };
    activityEvents.forEach((event) => window.addEventListener(event, recordActivity, { passive: true }));
    resetIdleTimer();
    return () => {
      activityEvents.forEach((event) => window.removeEventListener(event, recordActivity));
      clearIdleTimers();
    };
  });

  function clearIdleTimers() {
    if (idleTimeout) clearTimeout(idleTimeout);
    if (idleCountdown) clearInterval(idleCountdown);
    idleTimeout = null;
    idleCountdown = null;
  }

  function resetIdleTimer() {
    if (!currentCustomer) return;
    clearIdleTimers();
    idleWarning = false;
    idleSecondsRemaining = Math.floor(idleWarningMs / 1000);
    idleTimeout = setTimeout(beginIdleWarning, idleLimitMs - idleWarningMs);
  }

  function beginIdleWarning() {
    idleWarning = true;
    idleSecondsRemaining = Math.floor(idleWarningMs / 1000);
    idleCountdown = setInterval(() => {
      idleSecondsRemaining -= 1;
      if (idleSecondsRemaining <= 0) void signOutForInactivity();
    }, 1000);
  }

  async function signOutForInactivity() {
    clearIdleTimers();
    idleWarning = false;
    await frappeLogout();
    setSignedOut("Your session ended after 15 minutes of inactivity. Please sign in again.");
  }

  async function signOut() {
    clearIdleTimers();
    await frappeLogout();
    setSignedOut("You have signed out. Sign in again to access your fleet.");
  }

  function setSignedOut(message = "Your session has expired. Please sign in again.") {
    currentCustomer = null;
    summary = null;
    vehicles = [];
    invoices = [];
    documents = [];
    tickets = [];
    errorMessage = message;
    clearIdleTimers();
  }

  async function loadPortal() {
    loading = true;
    errorMessage = "";
    try {
      const customerResponse = await fetchPortalCurrentCustomer();
      currentCustomer = customerResponse;
      resetIdleTimer();

      if (!customerResponse.legal.accepted) {
        summary = null;
        vehicles = [];
        invoices = [];
        documents = [];
        tickets = [];
        selectedVehicle = null;
        selectedTicket = null;
        return;
      }

      const [summaryResponse, vehicleResponse, invoiceResponse, documentResponse, ticketResponse] = await Promise.all([
        fetchPortalDashboardSummary(),
        fetchPortalVehicles(),
        fetchPortalInvoices(),
        fetchPortalDocuments(),
        fetchPortalSupportTickets(),
      ]);

      summary = summaryResponse;
      vehicles = vehicleResponse.vehicles;
      invoices = invoiceResponse.invoices;
      documents = documentResponse.documents;
      tickets = ticketResponse.tickets;
      selectedVehicle = null;
      selectedTicket = null;
    } catch (error) {
      if (isFrappeAuthenticationError(error)) {
        setSignedOut();
      } else {
        errorMessage = error instanceof Error ? error.message : "Unable to load the customer portal.";
      }
    } finally {
      loading = false;
    }
  }

  async function acceptLegalTerms() {
    if (acceptingLegal || !termsAccepted || !privacyAccepted) return;
    acceptingLegal = true;
    legalMessage = "";
    try {
      const legal = await acceptPortalLegalTerms({
        accepted_terms: termsAccepted,
        accepted_privacy_policy: privacyAccepted,
      });
      if (currentCustomer) {
        currentCustomer = { ...currentCustomer, legal };
      }
      await loadPortal();
    } catch (error) {
      legalMessage = cleanError(error instanceof Error ? error.message : "Unable to record legal acceptance.");
    } finally {
      acceptingLegal = false;
    }
  }

  async function openVehicleDetail(vehicle: PortalVehicle) {
    detailLoading = `vehicle:${vehicle.name}`;
    selectedTicket = null;
    try {
      selectedVehicle = await fetchPortalVehicleDetail(vehicle.name);
    } catch (error) {
      ticketMessage = error instanceof Error ? cleanError(error.message) : "Unable to load vehicle details.";
    } finally {
      detailLoading = "";
    }
  }

  async function openTicketDetail(ticket: PortalTicket) {
    detailLoading = `ticket:${ticket.name}`;
    selectedVehicle = null;
    try {
      selectedTicket = await fetchPortalSupportTicketDetail(ticket.name);
    } catch (error) {
      ticketMessage = error instanceof Error ? cleanError(error.message) : "Unable to load support ticket.";
    } finally {
      detailLoading = "";
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

  function detailVehicleLabel(vehicle?: PortalVehicleDetail["vehicle"] | null) {
    if (!vehicle) return "Vehicle";
    return vehicle.vehicle_name || vehicle.registration_number || vehicle.name;
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

  function customerAddress() {
    const address = currentCustomer?.customer.address;
    if (!address) return "No address recorded";
    return [address.line1, address.line2, address.city, address.state, address.country, address.postal_code]
      .filter(Boolean)
      .join(", ") || "No address recorded";
  }
</script>

<svelte:head>
  <title>Omni Logistics · Customer Portal</title>
</svelte:head>

<section class="min-h-screen bg-[#f5f8fb] text-slate-950">
  {#if idleWarning}
    <div class="fixed inset-0 z-50 grid place-items-center bg-slate-950/65 p-4" role="dialog" aria-modal="true" aria-labelledby="idle-title">
      <div class="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-xl">
        <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-700">Session security</p>
        <h2 id="idle-title" class="mt-3 text-2xl font-bold text-slate-950">Still working?</h2>
        <p class="mt-3 text-sm leading-6 text-slate-600">
          You will be signed out in {idleSecondsRemaining} seconds because the portal has been inactive.
        </p>
        <div class="mt-6 flex flex-wrap gap-3">
          <button type="button" class="rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white hover:bg-cyan-700" on:click={resetIdleTimer}>Stay signed in</button>
          <button type="button" class="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700" on:click={signOutForInactivity}>Sign out now</button>
        </div>
      </div>
    </div>
  {/if}
  <header class="border-b border-slate-200 bg-white">
    <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
      <a href="/" aria-label="Omni Logistics home">
        <img src="/brand/omni-industrial-solutions-logo.png" alt="Omni Industrial Solutions" class="h-20 w-auto rounded-xl object-contain shadow-sm sm:h-24" />
      </a>
      <nav class="flex flex-wrap items-center gap-2 text-sm font-semibold">
        <a href="/" class="rounded-full px-4 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950">Website</a>
        <a href="/tracking" class="rounded-full px-4 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950">Tracking</a>
        <a href="mailto:support@omnilogistics.co.zw" class="rounded-full bg-slate-950 px-5 py-2.5 text-white transition hover:bg-cyan-700">Support</a>
        {#if currentCustomer}
          <button type="button" class="rounded-full border border-slate-300 px-4 py-2 text-slate-700 transition hover:border-slate-500 hover:bg-slate-100" on:click={signOut}>
            Sign out
          </button>
        {/if}
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
    {:else if currentCustomer && !currentCustomer.legal.accepted}
      <div class="grid min-h-[60vh] place-items-center">
        <section class="w-full max-w-2xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-700">Before you continue</p>
          <h1 class="mt-3 text-2xl font-bold text-slate-950">Accept Omni portal terms</h1>
          <p class="mt-3 text-sm leading-6 text-slate-600">
            To protect your account and fleet information, please confirm that you have read and accepted the current
            Omni Logistics Terms & Conditions and Privacy Policy before accessing the customer portal.
          </p>

          <div class="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            <p class="font-semibold text-slate-950">{currentCustomer.customer.display_name}</p>
            <p class="mt-1">{currentCustomer.user.full_name || currentCustomer.user.email}</p>
            <div class="mt-4 grid gap-3 sm:grid-cols-2">
              <a href={currentCustomer.legal.terms_url} target="_blank" rel="noreferrer" class="rounded-md border border-slate-300 bg-white px-4 py-3 font-semibold text-slate-800 transition hover:border-cyan-500 hover:text-cyan-700">
                Read Terms v{currentCustomer.legal.terms_version}
              </a>
              <a href={currentCustomer.legal.privacy_policy_url} target="_blank" rel="noreferrer" class="rounded-md border border-slate-300 bg-white px-4 py-3 font-semibold text-slate-800 transition hover:border-cyan-500 hover:text-cyan-700">
                Read Privacy Policy v{currentCustomer.legal.privacy_policy_version}
              </a>
            </div>
          </div>

          <div class="mt-5 space-y-3 text-sm text-slate-600">
            <label class="flex items-start gap-3">
              <input bind:checked={termsAccepted} type="checkbox" class="mt-1 rounded border-slate-300" />
              <span>
                I have read and agree to the Omni Logistics Terms & Conditions, including the rules for customer accounts,
                tracking services, hardware, installation, support, billing, and authorised use.
              </span>
            </label>
            <label class="flex items-start gap-3">
              <input bind:checked={privacyAccepted} type="checkbox" class="mt-1 rounded border-slate-300" />
              <span>
                I have read and agree to the Privacy Policy, including how Omni processes customer, user, vehicle,
                telematics, billing, support, and portal activity information.
              </span>
            </label>
          </div>

          {#if legalMessage}
            <p class="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{legalMessage}</p>
          {/if}

          <div class="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              disabled={acceptingLegal || !termsAccepted || !privacyAccepted}
              class="rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700 disabled:opacity-50"
              on:click={acceptLegalTerms}
            >
              {acceptingLegal ? "Recording acceptance..." : "Accept and Continue"}
            </button>
            <a href="/" class="rounded-full border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-500">
              Back to Website
            </a>
          </div>
        </section>
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

		<section class="rounded-lg border border-slate-200 bg-white shadow-sm">
			<div class="border-b border-slate-200 px-5 py-4">
				<h2 class="text-lg font-bold text-slate-950">Account information</h2>
				<p class="mt-1 text-sm text-slate-500">Details stored against your Omni customer account.</p>
			</div>
			<div class="grid gap-5 px-5 py-5 sm:grid-cols-2 lg:grid-cols-4">
				<div>
					<p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Customer</p>
					<p class="mt-2 text-sm font-semibold text-slate-950">{currentCustomer?.customer.display_name}</p>
					<p class="mt-1 text-xs text-slate-500">{currentCustomer?.customer.customer_group || "Customer group not set"}</p>
				</div>
				<div>
					<p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Contact</p>
					<p class="mt-2 text-sm font-semibold text-slate-950">{currentCustomer?.customer.contact_email || currentCustomer?.user.email}</p>
					<p class="mt-1 text-xs text-slate-500">{currentCustomer?.customer.contact_phone || "Phone number not recorded"}</p>
				</div>
				<div>
					<p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Location</p>
					<p class="mt-2 text-sm font-semibold text-slate-950">{currentCustomer?.customer.territory || "Territory not set"}</p>
					<p class="mt-1 text-xs leading-5 text-slate-500">{customerAddress()}</p>
				</div>
				<div>
					<p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Tax ID</p>
					<p class="mt-2 text-sm font-semibold text-slate-950">{currentCustomer?.customer.tax_id || "Not recorded"}</p>
					<p class="mt-1 text-xs text-slate-500">Customer reference: {currentCustomer?.customer.name}</p>
				</div>
			</div>
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
                        <button
                          type="button"
                          class="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-cyan-600 hover:text-cyan-700"
                          on:click={() => openVehicleDetail(vehicle)}
                        >
                          {detailLoading === `vehicle:${vehicle.name}` ? "Loading..." : "View details"}
                        </button>
                      </div>
                    </div>
                  {/each}
                {:else}
                  <p class="px-5 py-8 text-sm text-slate-500">No vehicles are linked to this customer account yet.</p>
                {/if}
              </div>
            </article>

            {#if selectedVehicle}
              <article class="rounded-lg border border-cyan-200 bg-white shadow-sm">
                <div class="flex flex-wrap items-start justify-between gap-3 border-b border-cyan-100 px-5 py-4">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700">Vehicle Detail</p>
                    <h2 class="mt-1 text-lg font-bold text-slate-950">{detailVehicleLabel(selectedVehicle.vehicle)}</h2>
                    <p class="mt-1 text-sm text-slate-500">
                      {selectedVehicle.vehicle.registration_number || "Registration not set"} · {selectedVehicle.vehicle.status || "Status pending"}
                    </p>
                  </div>
                  <button type="button" class="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-slate-500" on:click={() => (selectedVehicle = null)}>
                    Close
                  </button>
                </div>
                <div class="grid gap-4 p-5 md:grid-cols-3">
                  <div class="rounded-md bg-slate-50 p-4">
                    <p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Tracker</p>
                    <p class="mt-2 text-sm font-semibold text-slate-950">{selectedVehicle.tracker?.tracker_name || selectedVehicle.tracker?.name || "Not assigned"}</p>
                    <p class="mt-1 text-xs text-slate-500">{selectedVehicle.tracker?.status || "No tracker status"}</p>
                  </div>
                  <div class="rounded-md bg-slate-50 p-4">
                    <p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">SIM</p>
                    <p class="mt-2 text-sm font-semibold text-slate-950">{selectedVehicle.sim?.carrier || selectedVehicle.sim?.name || "Not assigned"}</p>
                    <p class="mt-1 text-xs text-slate-500">{selectedVehicle.sim?.status || "No SIM status"}</p>
                  </div>
                  <div class="rounded-md bg-slate-50 p-4">
                    <p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Latest Invoice</p>
                    <p class="mt-2 text-sm font-semibold text-slate-950">{selectedVehicle.latest_invoice?.name || "No invoice"}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {selectedVehicle.latest_invoice ? `${money(selectedVehicle.latest_invoice.outstanding_amount ?? 0)} outstanding` : "Nothing due"}
                    </p>
                  </div>
                </div>
                <div class="grid gap-4 border-t border-slate-100 p-5 md:grid-cols-2">
                  <div>
                    <h3 class="text-sm font-bold text-slate-950">Telematics</h3>
                    {#if selectedVehicle.telematics?.links?.length}
                      <div class="mt-3 space-y-2">
                        {#each selectedVehicle.telematics.links as link}
                          <div class="rounded-md border border-slate-200 p-3">
                            <p class="text-sm font-semibold text-slate-950">{link.external_unit_name || link.name}</p>
                            <p class="mt-1 text-xs text-slate-500">{link.provider || "Provider"} · {link.last_sync_status || "Not synced"} · {formatDate(link.last_sync_datetime)}</p>
                          </div>
                        {/each}
                      </div>
                    {:else}
                      <p class="mt-2 text-sm text-slate-500">No telematics link is visible for this vehicle yet.</p>
                    {/if}
                  </div>
                  <div>
                    <h3 class="text-sm font-bold text-slate-950">Installation History</h3>
                    {#if selectedVehicle.installations?.length}
                      <div class="mt-3 space-y-2">
                        {#each selectedVehicle.installations as installation}
                          <div class="rounded-md border border-slate-200 p-3">
                            <p class="text-sm font-semibold text-slate-950">{installation.name}</p>
                            <p class="mt-1 text-xs text-slate-500">{installation.status || "Status pending"} · {formatDate(installation.completed_date)}</p>
                          </div>
                        {/each}
                      </div>
                    {:else}
                      <p class="mt-2 text-sm text-slate-500">No installation history is visible yet.</p>
                    {/if}
                  </div>
                </div>
              </article>
            {/if}

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
                      <button type="button" class="block w-full rounded-md p-2 text-left transition hover:bg-slate-50" on:click={() => openTicketDetail(ticket)}>
                        <p class="text-sm font-semibold text-slate-950">{ticket.subject}</p>
                        <p class="text-xs text-slate-500">
                          {ticket.status || "Open"} · {ticket.priority || "Medium"} · {detailLoading === `ticket:${ticket.name}` ? "Loading..." : "View history"}
                        </p>
                      </button>
                    {/each}
                  </div>
                {:else}
                  <p class="text-sm text-slate-500">No support tickets are open for this account.</p>
                {/if}
              </div>
            </article>

            {#if selectedTicket}
              <article class="rounded-lg border border-cyan-200 bg-white shadow-sm">
                <div class="flex flex-wrap items-start justify-between gap-3 border-b border-cyan-100 px-5 py-4">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700">Support Ticket</p>
                    <h2 class="mt-1 text-lg font-bold text-slate-950">{selectedTicket.subject}</h2>
                    <p class="mt-1 text-sm text-slate-500">{selectedTicket.status || "Open"} · {selectedTicket.priority || "Medium"} · {formatDate(selectedTicket.modified)}</p>
                  </div>
                  <button type="button" class="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-slate-500" on:click={() => (selectedTicket = null)}>
                    Close
                  </button>
                </div>
                <div class="space-y-4 p-5">
                  <div>
                    <h3 class="text-sm font-bold text-slate-950">Request</h3>
                    <p class="mt-2 whitespace-pre-line text-sm leading-6 text-slate-600">{stripHtml(selectedTicket.description || selectedTicket.content || "No description was captured.")}</p>
                  </div>
                  {#if selectedTicket.resolution_details}
                    <div class="rounded-md bg-emerald-50 p-4">
                      <h3 class="text-sm font-bold text-emerald-950">Resolution</h3>
                      <p class="mt-2 whitespace-pre-line text-sm leading-6 text-emerald-800">{stripHtml(selectedTicket.resolution_details)}</p>
                    </div>
                  {:else}
                    <p class="rounded-md bg-slate-50 p-4 text-sm text-slate-600">Omni Support will update this ticket as work progresses.</p>
                  {/if}
                </div>
              </article>
            {/if}

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
