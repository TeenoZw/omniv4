<script lang="ts">
  import { submitEnquiry } from "$lib/api/enquiries";

  type CustomerType = "individual" | "business";

  const hardwareOptions = [
    {
      id: "basic_2g",
      name: "Basic (2G) · $60",
      features: [
        "Entry-level GPS tracking for budget fleets",
        "Basic location pings and route history",
        "Best for low-usage assets where cost matters most",
      ],
    },
    {
      id: "basic_4g",
      name: "Basic (4G) · $70",
      features: [
        "Faster, more reliable connectivity than 2G",
        "Improved coverage and uptime for live tracking",
        "Recommended for most fleets as a safe baseline",
      ],
    },
    {
      id: "obd2_tracker",
      name: "OBD2 Tracker · $118",
      features: [
        "Plug-and-play install with OBD2 port",
        "Pulls OEM data like odometer and fuel level",
        "Best suited for performance vehicles (sports & racing) and light-duty cars",
      ],
    },
    {
      id: "professional_tracker",
      name: "Professional Tracker (1-Wire ready) · $150",
      features: [
        "Supports 1-Wire, RS232/RS485, and CAN adapters",
        "Best for heavy-duty fleets and multi-sensor setups",
        "Required for driver iButton readers and advanced accessories",
      ],
    },
  ];

  type AddOn = {
    id: string;
    name: string;
    price: number;
    priceType: "one_time" | "monthly";
    description: string;
    requiresHardware?: string[];
    requiresAddOns?: string[];
    incompatibleHardware?: string[];
  };

  const addOns: AddOn[] = [
    {
      id: "teltonika_dash_cam",
      name: "Dash Cams",
      price: 25,
      priceType: "one_time",
      description: "Road + cabin video capture with event-triggered recording.",
    },
    {
      id: "liquid_level_sensors",
      name: "Liquid Level Sensors",
      price: 15,
      priceType: "one_time",
      description: "Fuel level monitoring, theft detection, and volume reporting. Best with Basic trackers.",
      incompatibleHardware: ["obd2_tracker"],
    },
    {
      id: "driver_ibuttons",
      name: "Driver iButtons & Readers",
      price: 10,
      priceType: "one_time",
      description: "Driver identification with shift-level accountability. Requires 1-Wire (Professional).",
      requiresHardware: ["professional_tracker"],
    },
    {
      id: "dash_cam_remote_monitoring",
      name: "Remote dash cam monitoring",
      price: 20,
      priceType: "monthly",
      description: "Managed SIM data and remote access to dash cam footage.",
      requiresAddOns: ["teltonika_dash_cam"],
    },
  ];

  let customerType: CustomerType = "business";
  let fullName = "";
  let email = "";
  let phone = "";
  let companyName = "";
  let fleetSize = "";
  let operatingArea = "";
  let preferredContactMethod = "email";
  let expectedGoLiveDate = "";
  let trackingUseCase = "";
  let message = "";
  let selectedHardware: string[] = [];
  let selectedAddOns: string[] = [];
  let termsAccepted = false;
  let privacyAccepted = false;
  let loading = false;
  let errorMessage = "";
  let successMessage = "";
  let fieldErrors: Record<string, string> = {};

  $: baseMonthly = customerType === "business" ? 15 : 10;
  $: addOnMonthly = selectedAddOns.reduce((total, id) => {
    const match = addOns.find((item) => item.id === id);
    if (!match || match.priceType !== "monthly") return total;
    return total + (match.price ?? 0);
  }, 0);
  $: addOnOneTime = selectedAddOns.reduce((total, id) => {
    const match = addOns.find((item) => item.id === id);
    if (!match || match.priceType !== "one_time") return total;
    return total + (match.price ?? 0);
  }, 0);
  $: estimatedMonthly = baseMonthly + addOnMonthly;

  function validateEmail(value: string) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
  }

  function validatePhone(value: string) {
    return /^[+\d][\d\s()-]{7,}$/.test(value.trim());
  }

  function validateForm() {
    const errors: Record<string, string> = {};

    if (!fullName.trim()) errors.fullName = "Full name is required.";
    if (!email.trim()) {
      errors.email = "Email is required.";
    } else if (!validateEmail(email)) {
      errors.email = "Enter a valid email address.";
    }
    if (!phone.trim()) {
      errors.phone = "Phone number is required.";
    } else if (!validatePhone(phone)) {
      errors.phone = "Enter a valid phone number.";
    }
    if (customerType === "business" && !companyName.trim()) {
      errors.companyName = "Company name is required for business enquiries.";
    }
    if (selectedHardware.length === 0) {
      errors.hardware = "Select at least one tracking hardware option.";
    }
    if (!termsAccepted) {
      errors.termsAccepted = "You must accept the Terms & Conditions.";
    }
    if (!privacyAccepted) {
      errors.privacyAccepted = "You must accept the Privacy Policy.";
    }
    if (expectedGoLiveDate) {
      const chosen = new Date(expectedGoLiveDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (!Number.isNaN(chosen.getTime()) && chosen < today) {
        errors.expectedGoLiveDate = "Expected go-live date cannot be in the past.";
      }
    }

    fieldErrors = errors;
    return Object.keys(errors).length === 0;
  }

  function toggleHardware(id: string) {
    if (selectedHardware.includes(id)) {
      selectedHardware = selectedHardware.filter((item) => item !== id);
      return;
    }
    selectedHardware = [...selectedHardware, id];
  }

  function toggleAddOn(id: string) {
    const next = new Set(selectedAddOns);
    const target = addOns.find((addon) => addon.id === id);

    if (next.has(id)) {
      next.delete(id);
      addOns
        .filter((addon) => addon.requiresAddOns?.includes(id))
        .forEach((addon) => next.delete(addon.id));
    } else {
      if (target?.requiresAddOns && !target.requiresAddOns.every((req) => next.has(req))) {
        return;
      }
      if (target?.requiresHardware && !selectedHardware.some((item) => target.requiresHardware?.includes(item))) {
        return;
      }
      next.add(id);
    }
    selectedAddOns = Array.from(next);
  }

  const hardwareNameById = new Map(hardwareOptions.map((item) => [item.id, item.name]));
  const addOnLabelById = new Map(
    addOns.map((item) => [
      item.id,
      item.priceType === "monthly"
        ? `${item.name} (+$${item.price}/mo)`
        : `${item.name} (+$${item.price} one-time)`,
    ])
  );

  async function handleSubmit() {
    errorMessage = "";
    successMessage = "";

    if (!validateForm()) {
      errorMessage = "Please fix the highlighted fields before submitting your enquiry.";
      return;
    }

    loading = true;
    try {
      const hardwareSelection = selectedHardware
        .map((id) => hardwareNameById.get(id) ?? id)
        .filter(Boolean);
      const addOnSelection = selectedAddOns
        .map((id) => addOnLabelById.get(id) ?? id)
        .filter(Boolean);

      await submitEnquiry({
        customer_type: customerType,
        full_name: fullName,
        email,
        phone,
        company_name: companyName || null,
        fleet_size: fleetSize || null,
        operating_area: operatingArea || null,
        preferred_contact_method: preferredContactMethod || null,
        expected_go_live_date: expectedGoLiveDate || null,
        tracking_use_case: trackingUseCase || null,
        hardware_choices: hardwareSelection,
        add_ons: addOnSelection,
        message,
        terms_accepted: termsAccepted,
        privacy_accepted: privacyAccepted,
      });
      successMessage = "Thank you. Your enquiry has been received and our team will respond with a quotation shortly.";
      fullName = "";
      email = "";
      phone = "";
      companyName = "";
      fleetSize = "";
      operatingArea = "";
      preferredContactMethod = "email";
      expectedGoLiveDate = "";
      trackingUseCase = "";
      message = "";
      selectedHardware = [];
      selectedAddOns = [];
      termsAccepted = false;
      privacyAccepted = false;
      fieldErrors = {};
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "Unable to submit your enquiry right now.";
    } finally {
      loading = false;
    }
  }
</script>

<section id="enquiry" class="relative overflow-hidden rounded-3xl border border-cyan-100 bg-gradient-to-br from-cyan-50 via-sky-100 to-amber-50 p-6 shadow-2xl dark:border-slate-800 dark:bg-gradient-to-br dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 sm:p-8 lg:p-10">
  <div
    class="absolute inset-0 -z-10 opacity-15"
    style="background-image: url('/landing/omni-quarry.jpg'); background-size: cover; background-position: center;"
  ></div>
  <div class="grid gap-8 lg:grid-cols-[1.1fr_1.4fr] lg:gap-10">
    <div class="space-y-4 sm:space-y-5">
      <p class="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-500">Request a quote</p>
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">Tell us what you need and we will prepare a quote.</h2>
      <p class="text-base text-slate-600 dark:text-slate-300">
        Omni Logistics helps with tracker selection, installation planning, subscriptions, billing, and support.
        Share your requirements and we will respond with pricing and the next steps.
      </p>
      <div class="rounded-3xl border border-cyan-100 bg-white/70 p-5 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 sm:p-6">
        <p class="text-sm font-semibold text-slate-900 dark:text-white">Monthly subscription (tracking access)</p>
        <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Individuals: <span class="font-semibold text-slate-900">$10 / month</span>
          <span class="mx-2 text-slate-400">•</span>
          Businesses: <span class="font-semibold text-slate-900">$15 / month</span>
        </p>
        <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Add-on pricing below is an estimate. One-time hardware add-ons are billed upfront on the final quote.
        </p>
        <p class="mt-3 text-xs text-slate-500 dark:text-slate-400">
          Hardware costs are quoted separately after we review your request.
        </p>
      </div>
      <div class="rounded-3xl border border-slate-800 bg-slate-900/95 p-5 text-sm text-white sm:p-6">
        <p class="text-xs uppercase tracking-[0.3em] text-cyan-200">Need a faster response?</p>
        <p class="mt-2 text-base font-semibold">Reach Omni Logistics</p>
        <p class="mt-2 text-white/70">
          We use Zoho Mail for enquiries. Send your request to our team and we will respond with the appropriate next steps.
        </p>
        <a
          href="mailto:info@omnilogistics.co.zw"
          class="mt-4 inline-flex items-center gap-2 rounded-full bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300"
        >
          Email info@omnilogistics.co.zw
          <span aria-hidden="true">↗</span>
        </a>
      </div>
    </div>

    <form class="space-y-5 sm:space-y-6" on:submit|preventDefault={handleSubmit}>
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="block text-sm font-medium text-slate-700">
          Customer type
          <select
            class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            bind:value={customerType}
          >
            <option value="individual">Individual ($10 / month)</option>
            <option value="business">Business ($15 / month)</option>
          </select>
        </label>
        <label class="block text-sm font-medium text-slate-700">
          Company name
          <input
            type="text"
            class={`mt-2 w-full rounded-2xl border px-4 py-3 text-sm focus:outline-none dark:bg-slate-900 dark:text-slate-100 ${
              fieldErrors.companyName
                ? "border-red-300 focus:border-red-400 dark:border-red-500/50"
                : "border-slate-200 focus:border-slate-900 dark:border-slate-700"
            }`}
            placeholder="Omni Logistics Ltd"
            bind:value={companyName}
            disabled={customerType !== "business"}
          />
          {#if fieldErrors.companyName}<span class="mt-2 block text-xs text-red-600">{fieldErrors.companyName}</span>{/if}
        </label>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <label class="block text-sm font-medium text-slate-700">
          Full name
          <input
            type="text"
            class={`mt-2 w-full rounded-2xl border px-4 py-3 text-sm focus:outline-none dark:bg-slate-900 dark:text-slate-100 ${
              fieldErrors.fullName
                ? "border-red-300 focus:border-red-400 dark:border-red-500/50"
                : "border-slate-200 focus:border-slate-900 dark:border-slate-700"
            }`}
            placeholder="Tino Mutami"
            bind:value={fullName}
            required
          />
          {#if fieldErrors.fullName}<span class="mt-2 block text-xs text-red-600">{fieldErrors.fullName}</span>{/if}
        </label>
        <label class="block text-sm font-medium text-slate-700">
          Phone
          <input
            type="tel"
            class={`mt-2 w-full rounded-2xl border px-4 py-3 text-sm focus:outline-none dark:bg-slate-900 dark:text-slate-100 ${
              fieldErrors.phone
                ? "border-red-300 focus:border-red-400 dark:border-red-500/50"
                : "border-slate-200 focus:border-slate-900 dark:border-slate-700"
            }`}
            placeholder="+263 7xx xxx xxx"
            bind:value={phone}
            required
          />
          {#if fieldErrors.phone}<span class="mt-2 block text-xs text-red-600">{fieldErrors.phone}</span>{/if}
        </label>
      </div>

      <label class="block text-sm font-medium text-slate-700">
        Email
        <input
          type="email"
          class={`mt-2 w-full rounded-2xl border px-4 py-3 text-sm focus:outline-none dark:bg-slate-900 dark:text-slate-100 ${
            fieldErrors.email
              ? "border-red-300 focus:border-red-400 dark:border-red-500/50"
              : "border-slate-200 focus:border-slate-900 dark:border-slate-700"
          }`}
          placeholder="you@example.com"
          bind:value={email}
          required
        />
        {#if fieldErrors.email}<span class="mt-2 block text-xs text-red-600">{fieldErrors.email}</span>{/if}
      </label>

      <div class="grid gap-4 sm:grid-cols-2">
        <label class="block text-sm font-medium text-slate-700">
          Fleet size
          <input
            type="text"
            class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            placeholder="e.g., 12 vehicles"
            bind:value={fleetSize}
          />
        </label>
        <label class="block text-sm font-medium text-slate-700">
          Operating area
          <input
            type="text"
            class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            placeholder="Harare, Bulawayo, SADC region"
            bind:value={operatingArea}
          />
        </label>
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <label class="block text-sm font-medium text-slate-700">
          Preferred contact
          <select
            class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            bind:value={preferredContactMethod}
          >
            <option value="email">Email</option>
            <option value="phone">Phone call</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
        </label>
        <label class="block text-sm font-medium text-slate-700">
          Expected go-live date (optional)
          <input
            type="date"
            class={`mt-2 w-full rounded-2xl border px-4 py-3 text-sm focus:outline-none dark:bg-slate-900 dark:text-slate-100 ${
              fieldErrors.expectedGoLiveDate
                ? "border-red-300 focus:border-red-400 dark:border-red-500/50"
                : "border-slate-200 focus:border-slate-900 dark:border-slate-700"
            }`}
            bind:value={expectedGoLiveDate}
          />
          {#if fieldErrors.expectedGoLiveDate}<span class="mt-2 block text-xs text-red-600">{fieldErrors.expectedGoLiveDate}</span>{/if}
        </label>
      </div>

      <label class="block text-sm font-medium text-slate-700">
        Tracking use case
        <input
          type="text"
          class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          placeholder="Logistics, school transport, mining, etc."
          bind:value={trackingUseCase}
        />
      </label>

      <div class="space-y-3">
        <p class="text-sm font-semibold text-slate-900 dark:text-white">Select tracking hardware</p>
        <div class="grid gap-4 sm:grid-cols-2">
          {#each hardwareOptions as item (item.id)}
            <button
              type="button"
              class={`rounded-2xl border p-4 text-left transition ${
                selectedHardware.includes(item.id)
                  ? "border-cyan-400 bg-cyan-50/70 shadow-md dark:border-cyan-400 dark:bg-slate-900/70"
                  : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-slate-600"
              }`}
              on:click={() => toggleHardware(item.id)}
            >
              <div class="flex items-center justify-between">
                <h3 class="text-base font-semibold text-slate-900 dark:text-white">{item.name}</h3>
                <span class="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  {selectedHardware.includes(item.id) ? "Selected" : "Select"}
                </span>
              </div>
              <ul class="mt-3 space-y-1 text-xs text-slate-600 dark:text-slate-300">
                {#each item.features as feature}
                  <li>• {feature}</li>
                {/each}
              </ul>
            </button>
          {/each}
        </div>
        {#if fieldErrors.hardware}<p class="text-xs text-red-600">{fieldErrors.hardware}</p>{/if}
      </div>

      <div class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/50">
        <p class="text-sm font-semibold text-slate-900 dark:text-white">Optional add-ons</p>
        <div class="space-y-3">
          {#each addOns as addon (addon.id)}
            {@const requiresHardware = addon.requiresHardware ?? []}
            {@const requiresAddOns = addon.requiresAddOns ?? []}
            {@const incompatibleHardware = addon.incompatibleHardware ?? []}
            {@const hasRequiredHardware = requiresHardware.length === 0 || selectedHardware.some((id) => requiresHardware.includes(id))}
            {@const hasRequiredAddOns = requiresAddOns.length === 0 || requiresAddOns.every((id) => selectedAddOns.includes(id))}
            {@const allSelectedIncompatible =
              incompatibleHardware.length > 0 && selectedHardware.length > 0 && selectedHardware.every((id) => incompatibleHardware.includes(id))}
            {@const isDisabled = !hasRequiredHardware || !hasRequiredAddOns || allSelectedIncompatible}
            {@const disabledReason = !hasRequiredHardware
              ? "Requires Professional tracker (1-Wire)."
              : !hasRequiredAddOns
                ? "Requires Dash Cams add-on."
                : allSelectedIncompatible
                  ? "Not available for OBD2-only selections."
                  : ""}
            <label class={`flex items-start gap-3 text-sm text-slate-600 dark:text-slate-300 ${isDisabled ? "opacity-60" : ""}`}>
              <input
                type="checkbox"
                class="mt-1 rounded border-slate-300"
                checked={selectedAddOns.includes(addon.id)}
                disabled={isDisabled}
                on:change={() => toggleAddOn(addon.id)}
              />
              <span>
                <span class="font-semibold text-slate-900 dark:text-white">{addon.name}</span>
                <span class="ml-2 text-xs font-semibold uppercase tracking-widest text-slate-400">
                  {addon.priceType === "monthly" ? `+$${addon.price} / mo` : `+$${addon.price} one-time`}
                </span>
                <span class="block text-xs text-slate-500">{addon.description}</span>
                {#if isDisabled && disabledReason}
                  <span class="block text-xs text-slate-500">{disabledReason}</span>
                {/if}
              </span>
            </label>
          {/each}
        </div>
        <div class="mt-4 flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3 text-sm dark:bg-slate-900/80">
          <span class="text-slate-600 dark:text-slate-300">Estimated monthly subscription (monthly add-ons only)</span>
          <span class="font-semibold text-slate-900 dark:text-white">${estimatedMonthly} / month</span>
        </div>
        <div class="flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3 text-sm dark:bg-slate-900/80">
          <span class="text-slate-600 dark:text-slate-300">Estimated one-time add-ons</span>
          <span class="font-semibold text-slate-900 dark:text-white">${addOnOneTime} one-time</span>
        </div>
      </div>

      <label class="block text-sm font-medium text-slate-700">
        Additional notes
        <textarea
          rows="4"
          class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          placeholder="Fleet size, regions, or any special requirements"
          bind:value={message}
        ></textarea>
      </label>

      <div class="space-y-2 text-xs text-slate-500 dark:text-slate-400">
        <label class="flex items-start gap-2">
          <input type="checkbox" class="mt-1 rounded border-slate-300" bind:checked={termsAccepted} />
          <span>I agree to the Omni Logistics Terms & Conditions.</span>
        </label>
        {#if fieldErrors.termsAccepted}<p class="text-xs text-red-600">{fieldErrors.termsAccepted}</p>{/if}
        <label class="flex items-start gap-2">
          <input type="checkbox" class="mt-1 rounded border-slate-300" bind:checked={privacyAccepted} />
          <span>
            I agree to the
            <a class="font-semibold text-slate-900 underline transition hover:text-slate-700 dark:text-white dark:hover:text-slate-200" href="/privacy">
              Privacy Policy
            </a>
            and data processing terms.
          </span>
        </label>
        {#if fieldErrors.privacyAccepted}<p class="text-xs text-red-600">{fieldErrors.privacyAccepted}</p>{/if}
      </div>

      {#if errorMessage}
        <p class="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">{errorMessage}</p>
      {/if}
      {#if successMessage}
        <p class="rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {successMessage}
        </p>
      {/if}

      <button
        type="submit"
        class="inline-flex w-full items-center justify-center gap-3 rounded-full bg-slate-900 px-6 py-3 text-base font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
        disabled={loading}
      >
        {#if loading}
          Sending request…
        {:else}
          Submit request
        {/if}
        <span aria-hidden="true">→</span>
      </button>
      <p class="text-xs text-slate-500">
        We will email a quotation, including hardware pricing, after reviewing your request.
      </p>
    </form>
  </div>
</section>
