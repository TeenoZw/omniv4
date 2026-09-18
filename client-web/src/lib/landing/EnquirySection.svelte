<script lang="ts">
  import { onMount } from "svelte";
  import { submitEnquiry } from "$lib/api/enquiries";
  import { getPublicQuoteAddOns, type PublicQuoteAddOn } from "$lib/api/quote-add-ons";

  type VehicleTypeOption = {
    value: string;
    label: string;
    fuelMonitoringEligible: boolean;
    summary: string;
    recommendedHardware: string[];
    suitableAddOns: string[];
  };

  type FleetSegment = {
    id: number;
    vehicleType: string;
    count: string;
  };

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
      recommended: true,
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
    price?: number;
    priceType?: "one_time" | "monthly";
    description: string;
    requiresHardware?: string[];
    requiresAddOns?: string[];
    incompatibleHardware?: string[];
    eligibleVehicleTypes?: string[];
    unavailable?: boolean;
    unavailableReason?: string;
  };

  const monthlySubscriptionPerVehicle = 10;

  const vehicleTypes: VehicleTypeOption[] = [
    {
      value: "light_car",
      label: "Light vehicle / private car",
      fuelMonitoringEligible: false,
      summary: "Good fit for standard GPS tracking, route history, driver behaviour review, and lightweight fleet visibility.",
      recommendedHardware: ["basic_4g", "obd2_tracker"],
      suitableAddOns: [],
    },
    {
      value: "pickup",
      label: "Pickup / bakkie",
      fuelMonitoringEligible: false,
      summary: "Works well with 4G tracking for sales teams, service teams, and mixed urban or regional operations.",
      recommendedHardware: ["basic_4g", "professional_tracker"],
      suitableAddOns: ["driver_ibuttons"],
    },
    {
      value: "minibus",
      label: "Minibus / commuter vehicle",
      fuelMonitoringEligible: false,
      summary: "Best quoted with reliable 4G tracking; driver identification is useful where multiple drivers rotate vehicles.",
      recommendedHardware: ["basic_4g", "professional_tracker"],
      suitableAddOns: ["driver_ibuttons"],
    },
    {
      value: "truck",
      label: "Truck with external tank",
      fuelMonitoringEligible: true,
      summary: "Best suited to professional tracking, driver identification, and fuel monitoring after a tank assessment.",
      recommendedHardware: ["professional_tracker"],
      suitableAddOns: ["driver_ibuttons", "fuel_monitoring_solutions"],
    },
    {
      value: "earthmoving",
      label: "Earthmoving equipment",
      fuelMonitoringEligible: true,
      summary: "Usually needs professional tracking because installations may involve harsh sites, long idle time, and specialist sensors.",
      recommendedHardware: ["professional_tracker"],
      suitableAddOns: ["fuel_monitoring_solutions"],
    },
    {
      value: "bus",
      label: "Bus / coach with accessible tank",
      fuelMonitoringEligible: true,
      summary: "Good candidate for professional tracking, driver identification, route accountability, and fuel monitoring where tanks are accessible.",
      recommendedHardware: ["professional_tracker"],
      suitableAddOns: ["driver_ibuttons", "fuel_monitoring_solutions"],
    },
    {
      value: "generator",
      label: "Generator / stationary equipment",
      fuelMonitoringEligible: true,
      summary: "Better handled as an asset-monitoring install, often with professional tracking and fuel monitoring after site inspection.",
      recommendedHardware: ["professional_tracker"],
      suitableAddOns: ["fuel_monitoring_solutions"],
    },
    {
      value: "other_external_tank",
      label: "Other asset with visible external tank",
      fuelMonitoringEligible: true,
      summary: "Requires assessment, but professional tracking gives room for sensors, fuel monitoring, and specialist integrations.",
      recommendedHardware: ["professional_tracker"],
      suitableAddOns: ["fuel_monitoring_solutions"],
    },
  ];

  const addOns: AddOn[] = [
    {
      id: "teltonika_dash_cam",
      name: "Dash Cams",
      description: "Road and cabin video capture. Planned for a later service phase.",
      unavailable: true,
      unavailableReason: "Out of stock. Dash cam installations are not available in the current quote workflow.",
    },
    {
      id: "fuel_monitoring_solutions",
      name: "Fuel monitoring solutions",
      description:
        "For trucks, earthmoving equipment, buses, generators, and other assets with visible external tanks. Requires a site/vehicle assessment before pricing.",
      incompatibleHardware: ["obd2_tracker"],
      eligibleVehicleTypes: vehicleTypes.filter((type) => type.fuelMonitoringEligible).map((type) => type.value),
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
      description: "Managed data and remote access for future dash cam deployments.",
      requiresAddOns: ["teltonika_dash_cam"],
      unavailable: true,
      unavailableReason: "Out of stock. Remote dash cam monitoring will be enabled when dash cam support is available.",
    },
  ];

  let fullName = "";
  let email = "";
  let phone = "";
  let companyName = "";
  let fleetSegments: FleetSegment[] = [{ id: 1, vehicleType: "", count: "1" }];
  let nextFleetSegmentId = 2;
  let operatingArea = "";
  let preferredContactMethod = "email";
  let expectedGoLiveDate = "";
  let message = "";
  let selectedHardware: string[] = [];
  let selectedAddOns: string[] = [];
  let termsAccepted = false;
  let privacyAccepted = false;
  let loading = false;
  let quoteAddOnSettings: Record<string, PublicQuoteAddOn> = {};
  let errorMessage = "";
  let successMessage = "";
  let fieldErrors: Record<string, string> = {};

  onMount(async () => {
    try {
      const settings = await getPublicQuoteAddOns();
      quoteAddOnSettings = Object.fromEntries(settings.add_ons.map((item) => [item.add_on_id, item]));
    } catch (error) {
      console.warn("Unable to load quote add-on settings; using default availability.", error);
    }
  });

  $: completedFleetSegments = fleetSegments.filter(
    (segment) => segment.vehicleType && Math.max(Number.parseInt(segment.count, 10) || 0, 0) > 0
  );
  $: vehicleCount = Math.max(
    completedFleetSegments.reduce((total, segment) => total + Math.max(Number.parseInt(segment.count, 10) || 0, 0), 0),
    1
  );
  $: selectedVehicleTypeValues = completedFleetSegments.map((segment) => segment.vehicleType);
  $: fleetHasFuelMonitoringEligibleVehicles = completedFleetSegments.some((segment) => {
    const match = vehicleTypes.find((type) => type.value === segment.vehicleType);
    return Boolean(match?.fuelMonitoringEligible);
  });
  $: if (!fleetHasFuelMonitoringEligibleVehicles && selectedAddOns.includes("fuel_monitoring_solutions")) {
    selectedAddOns = selectedAddOns.filter((id) => id !== "fuel_monitoring_solutions");
  }
  $: addOnMonthly = selectedAddOns.reduce((total, id) => {
    const match = addOns.find((item) => item.id === id);
    if (!match || match.priceType !== "monthly" || !match.price) return total;
    return total + (match.price ?? 0);
  }, 0);
  $: addOnOneTime = selectedAddOns.reduce((total, id) => {
    const match = addOns.find((item) => item.id === id);
    if (!match || match.priceType !== "one_time" || !match.price) return total;
    return total + (match.price ?? 0);
  }, 0);
  $: selectedQuoteOnlyAddOns = selectedAddOns.filter((id) => {
    const match = addOns.find((item) => item.id === id);
    return match && (!match.price || !match.priceType);
  }).length;
  $: estimatedMonthly = vehicleCount * monthlySubscriptionPerVehicle + addOnMonthly;
  $: smartInsights = buildSmartInsights();

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
    if (completedFleetSegments.length === 0) errors.fleetSegments = "Add at least one vehicle or asset group.";
    fleetSegments.forEach((segment) => {
      if (!segment.vehicleType) {
        errors.fleetSegments = "Every fleet group needs a vehicle or asset type.";
      }
      if ((Number.parseInt(segment.count, 10) || 0) < 1) {
        errors.fleetSegments = "Every fleet group needs at least one vehicle or asset.";
      }
    });
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

  function addFleetSegment() {
    fleetSegments = [
      ...fleetSegments,
      { id: nextFleetSegmentId, vehicleType: "", count: "1" },
    ];
    nextFleetSegmentId += 1;
  }

  function removeFleetSegment(id: number) {
    fleetSegments = fleetSegments.length === 1 ? fleetSegments : fleetSegments.filter((segment) => segment.id !== id);
  }

  function updateFleetSegment(id: number, field: keyof Omit<FleetSegment, "id">, value: string) {
    fleetSegments = fleetSegments.map((segment) => (segment.id === id ? { ...segment, [field]: value } : segment));
  }

  function getVehicleTypeLabel(value: string) {
    return vehicleTypes.find((type) => type.value === value)?.label ?? value;
  }

  function buildSmartInsights() {
    const insights: string[] = [];
    const selectedTypeConfigs = completedFleetSegments
      .map((segment) => vehicleTypes.find((type) => type.value === segment.vehicleType))
      .filter((type): type is VehicleTypeOption => Boolean(type));

    if (completedFleetSegments.length === 0) {
      return [
        "Choose the vehicle or asset groups in your fleet and the form will suggest suitable tracker types and add-ons.",
      ];
    }

    const uniqueTypes = Array.from(new Set(selectedTypeConfigs.map((type) => type.value)));
    if (uniqueTypes.length > 1) {
      insights.push("Mixed fleets are best quoted in groups, because light vehicles, trucks, equipment, and generators may need different hardware.");
    }

    selectedTypeConfigs.forEach((type) => {
      insights.push(`${type.label}: ${type.summary}`);
      if (type.recommendedHardware.length) {
        insights.push(
          `${type.label} tracker fit: ${type.recommendedHardware
            .map((id) => hardwareOptions.find((hardware) => hardware.id === id)?.name ?? id)
            .join(", ")}.`
        );
      }
      if (type.suitableAddOns.length) {
        insights.push(
          `${type.label} add-ons to consider: ${type.suitableAddOns
            .map((id) => addOns.find((addon) => addon.id === id)?.name ?? id)
            .join(", ")}.`
        );
      }
    });

    if (fleetHasFuelMonitoringEligibleVehicles) {
      insights.push("Fuel monitoring is practical only after confirming tank access, tank shape, mounting position, and expected site conditions.");
    }

    if (selectedTypeConfigs.some((type) => type.suitableAddOns.includes("driver_ibuttons"))) {
      insights.push("If these vehicles are shared by multiple drivers, Professional trackers can support 1-Wire iButton readers for driver identification.");
    }

    if (selectedHardware.includes("obd2_tracker") && fleetHasFuelMonitoringEligibleVehicles) {
      insights.push("OBD2 trackers are convenient for light vehicles, but heavy-duty fuel monitoring normally needs a Professional tracker.");
    }

    return Array.from(new Set(insights)).slice(0, 6);
  }

  function getQuoteAddOnSetting(id: string) {
    return quoteAddOnSettings[id];
  }

  function isAddOnOutOfStock(addon: AddOn) {
    const setting = getQuoteAddOnSetting(addon.id);
    if (setting) {
      return !setting.is_enabled || setting.status !== "Available";
    }
    return Boolean(addon.unavailable);
  }

  function getAddOnStockReason(addon: AddOn) {
    const setting = getQuoteAddOnSetting(addon.id);
    if (setting?.public_note) return setting.public_note;
    if (setting?.status === "Coming Soon") return "Coming soon. This add-on is not available for quoting yet.";
    if (setting?.status === "Inactive") return "Currently unavailable.";
    if (setting && (!setting.is_enabled || setting.status === "Out of Stock")) return "Out of stock.";
    return addon.unavailableReason ?? "Out of stock.";
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
      if (target?.eligibleVehicleTypes && !selectedVehicleTypeValues.some((type) => target.eligibleVehicleTypes?.includes(type))) {
        return;
      }
      if (!target || isAddOnOutOfStock(target)) {
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
      item.price && item.priceType
        ? item.priceType === "monthly"
          ? `${item.name} (+$${item.price}/mo)`
          : `${item.name} (+$${item.price} one-time)`
        : `${item.name} (quote after assessment)`,
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
        full_name: fullName,
        email,
        phone,
        company_name: companyName || null,
        fleet_size: String(vehicleCount),
        operating_area: operatingArea || null,
        preferred_contact_method: preferredContactMethod || null,
        expected_go_live_date: expectedGoLiveDate || null,
        tracking_use_case:
          [
            completedFleetSegments.length
              ? `Fleet mix:\n${completedFleetSegments
                  .map(
                    (segment) =>
                      `- ${segment.count} x ${getVehicleTypeLabel(segment.vehicleType)}`
                  )
                  .join("\n")}`
              : "",
            smartInsights.length ? `Smart recommendations:\n${smartInsights.map((item) => `- ${item}`).join("\n")}` : "",
          ]
            .filter(Boolean)
            .join("\n") || null,
        hardware_choices: hardwareSelection,
        add_ons: addOnSelection,
        fleet_segments: completedFleetSegments.map((segment) => ({
          vehicle_type: segment.vehicleType,
          label: getVehicleTypeLabel(segment.vehicleType),
          count: Number.parseInt(segment.count, 10) || 0,
        })),
        message,
        terms_accepted: termsAccepted,
        privacy_accepted: privacyAccepted,
      });
      successMessage = "Thank you. Your enquiry has been received and our team will respond with a quotation shortly.";
      fullName = "";
      email = "";
      phone = "";
      companyName = "";
      fleetSegments = [{ id: 1, vehicleType: "", count: "1" }];
      nextFleetSegmentId = 2;
      operatingArea = "";
      preferredContactMethod = "email";
      expectedGoLiveDate = "";
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
          <span class="font-semibold text-slate-900 dark:text-white">$10 / vehicle / month</span>
          for portal access, tracking visibility, account support, and standard subscription management.
        </p>
        <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Hardware, installation, and specialist add-ons are quoted after we review your vehicle type and requirements.
        </p>
        <p class="mt-3 text-xs text-slate-500 dark:text-slate-400">
          The monthly estimate below is based on the number of vehicles you enter.
        </p>
      </div>
      <div class="rounded-3xl border border-slate-800 bg-slate-900/95 p-5 text-sm text-white sm:p-6">
        <p class="text-xs uppercase tracking-[0.3em] text-cyan-200">Need a faster response?</p>
        <p class="mt-2 text-base font-semibold">Reach Omni Logistics</p>
        <p class="mt-2 text-white/70">
          Send your request to our team and we will respond with the appropriate next steps.
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
      <div class="grid gap-4">
        <label class="block text-sm font-medium text-slate-700">
          Company / hub name (optional)
          <input
            type="text"
            class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            placeholder="e.g., H2O Hub"
            bind:value={companyName}
          />
        </label>
      </div>

      <div class="space-y-4 rounded-3xl border border-slate-200 bg-white/80 p-4 dark:border-slate-800 dark:bg-slate-950/60 sm:p-5">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-sm font-semibold text-slate-900 dark:text-white">Fleet mix</p>
            <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Add each vehicle or asset group so we can recommend suitable trackers and add-ons.
            </p>
          </div>
          <button
            type="button"
            class="inline-flex items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 dark:border-slate-700 dark:text-slate-200"
            on:click={addFleetSegment}
          >
            Add another group
          </button>
        </div>

        <div class="space-y-3">
          {#each fleetSegments as segment, index (segment.id)}
            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <div class="mb-3 flex items-center justify-between gap-3">
                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Group {index + 1}</p>
                {#if fleetSegments.length > 1}
                  <button
                    type="button"
                    class="text-xs font-semibold text-slate-500 underline-offset-4 hover:text-red-600 hover:underline"
                    on:click={() => removeFleetSegment(segment.id)}
                  >
                    Remove
                  </button>
                {/if}
              </div>
              <div class="grid gap-3 sm:grid-cols-[1.4fr_0.7fr]">
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-200">
                  Vehicle / asset type
                  <select
                    class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                    value={segment.vehicleType}
                    on:change={(event) => updateFleetSegment(segment.id, "vehicleType", event.currentTarget.value)}
                  >
                    <option value="">Select type</option>
                    {#each vehicleTypes as type}
                      <option value={type.value}>{type.label}</option>
                    {/each}
                  </select>
                </label>
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-200">
                  Quantity
                  <input
                    type="number"
                    min="1"
                    class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                    value={segment.count}
                    on:input={(event) => updateFleetSegment(segment.id, "count", event.currentTarget.value)}
                  />
                </label>
              </div>
              {#if segment.vehicleType}
                <p class="mt-3 text-xs text-slate-500 dark:text-slate-400">
                  {vehicleTypes.find((type) => type.value === segment.vehicleType)?.summary}
                </p>
              {/if}
            </div>
          {/each}
        </div>

        {#if fieldErrors.fleetSegments}<p class="text-xs text-red-600">{fieldErrors.fleetSegments}</p>{/if}

        <div class="rounded-2xl border border-cyan-100 bg-cyan-50/70 p-4 dark:border-cyan-900/60 dark:bg-cyan-950/20">
          <p class="text-sm font-semibold text-slate-900 dark:text-white">Smart guidance based on your fleet</p>
          <ul class="mt-3 space-y-2 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
            {#each smartInsights as insight}
              <li class="flex gap-2">
                <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-500"></span>
                <span>{insight}</span>
              </li>
            {/each}
          </ul>
        </div>
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
          Operating area
          <input
            type="text"
            class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm focus:border-slate-900 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            placeholder="Harare, Bulawayo, SADC region"
            bind:value={operatingArea}
          />
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
      </div>

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
              <div class="flex items-start justify-between gap-3">
                <div>
                  <h3 class="text-base font-semibold text-slate-900 dark:text-white">{item.name}</h3>
                  {#if item.recommended}
                    <span class="mt-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-widest text-amber-800 dark:bg-amber-300/15 dark:text-amber-200">
                      <span aria-hidden="true">★</span>
                      Most recommended
                    </span>
                  {/if}
                </div>
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
            {@const eligibleVehicleTypes = addon.eligibleVehicleTypes ?? []}
            {@const hasRequiredHardware = requiresHardware.length === 0 || selectedHardware.some((id) => requiresHardware.includes(id))}
            {@const hasRequiredAddOns = requiresAddOns.length === 0 || requiresAddOns.every((id) => selectedAddOns.includes(id))}
            {@const hasEligibleVehicleType = eligibleVehicleTypes.length === 0 || selectedVehicleTypeValues.some((type) => eligibleVehicleTypes.includes(type))}
            {@const allSelectedIncompatible =
              incompatibleHardware.length > 0 && selectedHardware.length > 0 && selectedHardware.every((id) => incompatibleHardware.includes(id))}
            {@const isOutOfStock = isAddOnOutOfStock(addon)}
            {@const isDisabled = isOutOfStock || !hasRequiredHardware || !hasRequiredAddOns || !hasEligibleVehicleType || allSelectedIncompatible}
            {@const disabledReason = isOutOfStock
              ? getAddOnStockReason(addon)
              : !hasRequiredHardware
                ? "Requires Professional tracker (1-Wire)."
                : !hasRequiredAddOns
                  ? "Requires Dash Cams add-on."
                  : !hasEligibleVehicleType
                    ? "Available for trucks, earthmoving equipment, buses, generators, or assets with visible external tanks."
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
                {#if isOutOfStock}
                  <span class="ml-2 text-xs font-semibold uppercase tracking-widest text-red-500 dark:text-red-300">Out of stock</span>
                {/if}
                {#if addon.price && addon.priceType}
                  <span class="ml-2 text-xs font-semibold uppercase tracking-widest text-slate-400">
                    {addon.priceType === "monthly" ? `+$${addon.price} / mo` : `+$${addon.price} one-time`}
                  </span>
                {:else if !isOutOfStock}
                  <span class="ml-2 text-xs font-semibold uppercase tracking-widest text-slate-400">Quoted after assessment</span>
                {/if}
                <span class="block text-xs text-slate-500">{addon.description}</span>
                {#if isDisabled && disabledReason}
                  <span class="block text-xs text-slate-500">{disabledReason}</span>
                {/if}
              </span>
            </label>
          {/each}
        </div>
        <div class="mt-4 flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3 text-sm dark:bg-slate-900/80">
          <span class="text-slate-600 dark:text-slate-300">Estimated monthly subscription</span>
          <span class="font-semibold text-slate-900 dark:text-white">${estimatedMonthly} / month</span>
        </div>
        <div class="flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3 text-sm dark:bg-slate-900/80">
          <span class="text-slate-600 dark:text-slate-300">Specialist add-ons</span>
          <span class="font-semibold text-slate-900 dark:text-white">
            {addOnOneTime ? `$${addOnOneTime} one-time` : selectedQuoteOnlyAddOns ? "Quoted after assessment" : "None selected"}
          </span>
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
          <span>
            I have read and agree to the
            <a class="font-semibold text-slate-900 underline transition hover:text-slate-700 dark:text-white dark:hover:text-slate-200" href="/terms" target="_blank" rel="noreferrer">
              Omni Logistics Terms & Conditions
            </a>
            that apply to enquiries, quotations, hardware, installation, and tracking services.
          </span>
        </label>
        {#if fieldErrors.termsAccepted}<p class="text-xs text-red-600">{fieldErrors.termsAccepted}</p>{/if}
        <label class="flex items-start gap-2">
          <input type="checkbox" class="mt-1 rounded border-slate-300" bind:checked={privacyAccepted} />
          <span>
            I have read and agree to the
            <a class="font-semibold text-slate-900 underline transition hover:text-slate-700 dark:text-white dark:hover:text-slate-200" href="/privacy" target="_blank" rel="noreferrer">
              Privacy Policy
            </a>
            and consent to Omni processing my enquiry details to respond and prepare the requested quotation.
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
        disabled={loading || !termsAccepted || !privacyAccepted}
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
