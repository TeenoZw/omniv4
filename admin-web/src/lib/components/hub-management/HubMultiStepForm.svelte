<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { createHub } from "$lib/api/hubs";

  type Operator = {
    name: string;
    email: string;
    role: string;
    password: string;
  };

  const dispatcher = createEventDispatcher();

  const steps = [
    { id: 1, label: "Hub profile" },
    { id: 2, label: "Plan & payment" },
    { id: 3, label: "Users & roles" },
  ];

  const tierOptions = ["Individual", "Business"];
  const billingCycles = ["monthly"];
  const paymentMethods = [
    { value: "manual_invoice", label: "Manual invoice" },
    { value: "card_on_file", label: "Card on file" },
    { value: "bank_transfer", label: "Wire / EFT" },
  ];
  const roleOptions = [
    { value: "client", label: "Client" },
    { value: "company", label: "Company Manager" },
  ];
  const countryOptions = [
    "United States",
    "United Kingdom",
    "Canada",
    "Kenya",
    "Rwanda",
    "Zimbabwe",
    "South Africa",
    "Nigeria",
    "Germany",
    "France",
    "India",
    "United Arab Emirates",
    "Australia",
    "Brazil",
    "Mexico",
  ];

  const timezoneOptions = [
    "UTC",
    "Africa/Harare",
    "Africa/Kigali",
    "Africa/Nairobi",
    "Africa/Lagos",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Asia/Dubai",
    "Asia/Kolkata",
    "Asia/Tokyo",
    "Australia/Sydney",
  ];

  const fieldIds = {
    name: "hub-name",
    code: "hub-code",
    type: "hub-type",
    country: "hub-country",
    city: "hub-city",
    address: "hub-address",
    timezone: "hub-timezone",
    goLiveDate: "hub-go-live",
    primaryContactName: "hub-primary-name",
    primaryContactEmail: "hub-primary-email",
    primaryContactPhone: "hub-primary-phone",
    notes: "hub-notes",
    tier: "hub-tier",
    billingCycle: "hub-billing-cycle",
    paymentMethod: "hub-payment-method",
    purchaseOrder: "hub-purchase-order",
    billingContactName: "hub-billing-name",
    billingContactEmail: "hub-billing-email",
  } as const;

  const operatorFieldId = (index: number, field: "name" | "email" | "role" | "password") =>
    `hub-operator-${index}-${field}`;

  const buildCodeFromName = (name: string) => {
    const letters = (name || "")
      .replace(/[^a-zA-Z]/g, "")
      .toUpperCase();
    const prefix = (letters + "HUB").slice(0, 3).padEnd(3, "X");
    const digits = Array.from({ length: 4 }, () => Math.floor(Math.random() * 10)).join("");
    return `${prefix}-${digits}`;
  };

  const defaultForm = () => ({
    name: "",
    code: "",
    type: "company",
    address: "",
    city: "",
    country: "",
    timezone: "",
    goLiveDate: "",
    tier: tierOptions[0],
    billingCycle: billingCycles[0],
    paymentMethod: paymentMethods[0].value,
    purchaseOrder: "",
    notes: "",
    currency: "",
    primaryContact: { name: "", email: "", phone: "" },
    billingContact: { name: "", email: "", phone: "" },
    operators: [{ name: "", email: "", role: roleOptions[0].value, password: "" } as Operator],
  });

  let currentStep = 1;
  let isSubmitting = false;
  let serverMessage: { type: "success" | "error"; text: string } | null = null;
  let errors: Record<string, string> = {};
  let formData = defaultForm();
  $: isIndividual = formData.type === "individual";
  let autoCode = true;

  const resetForm = () => {
    formData = defaultForm();
    currentStep = 1;
    errors = {};
  };

  function collectStepErrors(step: number) {
    const stepErrors: Record<string, string> = {};
    const assign = (field: string, message: string) => {
      stepErrors[field] = message;
    };

    if (step === 1) {
      if (!formData.name.trim()) {
        assign("name", "Hub name is required");
      }
      if (!formData.code.trim()) {
        assign("code", "Hub code is required");
      }
      if (!formData.country.trim()) {
        assign("country", "Country is required");
      }
      if (!formData.primaryContact.name.trim()) {
        assign("primaryContact.name", "Primary contact name is required");
      }
      if (!formData.primaryContact.email.trim()) {
        assign("primaryContact.email", "Primary contact email is required");
      }
      if (formData.primaryContact.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.primaryContact.email)) {
        assign("primaryContact.email", "Enter a valid email address");
      }
    } else if (step === 2) {
      if (!formData.billingContact.email.trim()) {
        assign("billingContact.email", "Billing email is required");
      }
      if (formData.billingContact.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.billingContact.email)) {
        assign("billingContact.email", "Enter a valid email address");
      }
    } else if (step === 3) {
      formData.operators.forEach((operator, index) => {
        if (!operator.name.trim()) {
          assign(`operators.${index}.name`, "Required");
        }
        if (!operator.email.trim()) {
          assign(`operators.${index}.email`, "Required");
        }
        if (operator.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(operator.email)) {
          assign(`operators.${index}.email`, "Invalid email");
        }
        if (!operator.password.trim()) {
          assign(`operators.${index}.password`, "Required");
        } else if (operator.password.length < 8) {
          assign(`operators.${index}.password`, "Minimum 8 characters");
        }
      });
    }

    return stepErrors;
  }

  function validateCurrentStep() {
    const stepErrors = collectStepErrors(currentStep);
    errors = stepErrors;
    return Object.keys(stepErrors).length === 0;
  }

  function nextStep() {
    if (validateCurrentStep() && currentStep < steps.length) {
      currentStep += 1;
      serverMessage = null;
    }
  }

  function previousStep() {
    if (currentStep > 1) {
      currentStep -= 1;
    }
  }

  function addOperator() {
    formData = {
      ...formData,
      operators: [...formData.operators, { name: "", email: "", role: roleOptions[0].value, password: "" }],
    };
  }

  function handleNameInput(value: string) {
    formData = { ...formData, name: value };
    if (autoCode) {
      formData = { ...formData, code: buildCodeFromName(value) };
    }
  }

  function handleCodeInput(value: string) {
    autoCode = false;
    formData = { ...formData, code: value.toUpperCase() };
  }

  function removeOperator(index: number) {
    if (formData.operators.length === 1) {
      return;
    }
    formData = {
      ...formData,
      operators: formData.operators.filter((_, idx) => idx !== index),
    };
  }

  async function handleSubmit() {
    const stepErrorEntries = steps.map((step) => ({
      id: step.id,
      errors: collectStepErrors(step.id),
    }));
    const aggregateErrors = stepErrorEntries.reduce<Record<string, string>>(
      (result, entry) => ({ ...result, ...entry.errors }),
      {}
    );
    const firstInvalidStep = stepErrorEntries.find((entry) => Object.keys(entry.errors).length > 0)?.id;

    if (firstInvalidStep) {
      errors = aggregateErrors;
      currentStep = firstInvalidStep;
      return;
    }

    errors = {};

    isSubmitting = true;
    serverMessage = null;

    try {
      const payload = {
        ...formData,
        primaryContact: { ...formData.primaryContact },
        billingContact: { ...formData.billingContact },
        users: formData.operators.map((operator) => ({
          name: operator.name,
          email: operator.email,
          role: operator.role,
          password: operator.password,
        })),
        notes: [
          formData.notes,
          formData.purchaseOrder ? `PO Reference: ${formData.purchaseOrder}` : "",
        ]
          .filter(Boolean)
          .join(" | "),
      };

      const hub = await createHub(payload);
      serverMessage = {
        type: "success",
        text: "Hub registered and queued for provisioning.",
      };
      dispatcher("created", { hub });
      resetForm();
    } catch (error) {
      console.error("Failed to create hub", error);
      serverMessage = {
        type: "error",
        text: "Hub creation failed. Please review the form and try again.",
      };
    } finally {
      isSubmitting = false;
    }
  }
</script>

<section class="rounded-lg border bg-card p-5 shadow-sm">
  <header class="flex items-start gap-3">
    <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/15 text-xl text-primary">+</div>
    <div>
      <p class="text-sm font-medium uppercase tracking-wide text-primary">Add new hub</p>
      <h3 class="text-2xl font-semibold leading-tight">Provision workflow</h3>
    </div>
  </header>

  <div class="mt-5">
    <div class="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
      {#each steps as step}
        <div class="flex items-center gap-2">
          <span class={`inline-flex h-6 w-6 items-center justify-center rounded-full text-[0.7rem] ${
            currentStep === step.id
              ? "bg-primary text-primary-foreground"
              : currentStep > step.id
                ? "bg-primary/20 text-primary"
                : "bg-muted text-muted-foreground"
          }`}>
            {step.id}
          </span>
          <span class={currentStep === step.id ? "text-primary" : "text-muted-foreground"}>{step.label}</span>
        </div>
        {#if step.id !== steps.length}
          <div class="h-px flex-1 bg-border"></div>
        {/if}
      {/each}
    </div>
  </div>

  <form class="mt-6 space-y-6" on:submit|preventDefault={handleSubmit}>
    {#if currentStep === 1}
      <div class="space-y-4">
        <div>
          <label class="text-sm font-medium" for={fieldIds.name}>{isIndividual ? "Individual name *" : "Hub name *"}</label>
          <input
            id={fieldIds.name}
            class="mt-1 w-full rounded-md border px-3 py-2"
            value={formData.name}
            on:input={(event) => handleNameInput((event.target as HTMLInputElement).value)}
          />
          {#if errors["name"]}
            <p class="mt-1 text-xs text-destructive">{errors["name"]}</p>
          {/if}
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium" for={fieldIds.code}>{isIndividual ? "Identifier / Code *" : "Hub code *"}</label>
            <input
              id={fieldIds.code}
              class="mt-1 w-full rounded-md border px-3 py-2"
              value={formData.code}
              on:input={(event) => handleCodeInput((event.target as HTMLInputElement).value)}
            />
            {#if errors["code"]}
              <p class="mt-1 text-xs text-destructive">{errors["code"]}</p>
            {/if}
          </div>
          <div>
            <label class="text-sm font-medium" for={fieldIds.type}>Type</label>
            <select id={fieldIds.type} class="mt-1 w-full rounded-md border px-3 py-2" bind:value={formData.type}>
              <option value="company">Company</option>
              <option value="individual">Individual</option>
            </select>
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium" for={fieldIds.country}>Country *</label>
            <select
              id={fieldIds.country}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.country}
            >
              <option value="" disabled>Select country</option>
              {#each countryOptions as country}
                <option value={country}>{country}</option>
              {/each}
            </select>
            {#if errors["country"]}
              <p class="mt-1 text-xs text-destructive">{errors["country"]}</p>
            {/if}
          </div>
          <div>
            <label class="text-sm font-medium" for={fieldIds.city}>City</label>
            <input
              id={fieldIds.city}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.city}
            />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium" for={fieldIds.address}>{isIndividual ? "Address" : "Facility address"}</label>
          <input
            id={fieldIds.address}
            class="mt-1 w-full rounded-md border px-3 py-2"
            bind:value={formData.address}
          />
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium" for={fieldIds.timezone}>Timezone</label>
            <select
              id={fieldIds.timezone}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.timezone}
            >
              <option value="" disabled>Select timezone</option>
              {#each timezoneOptions as tz}
                <option value={tz}>{tz}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="text-sm font-medium" for={fieldIds.goLiveDate}>Go-live date</label>
            <input
              id={fieldIds.goLiveDate}
              class="mt-1 w-full rounded-md border px-3 py-2"
              type="date"
              bind:value={formData.goLiveDate}
            />
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-3">
          <div>
            <label class="text-sm font-medium" for={fieldIds.primaryContactName}>{isIndividual ? "Owner name *" : "Primary contact *"}</label>
            <input
              id={fieldIds.primaryContactName}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.primaryContact.name}
            />
            {#if errors["primaryContact.name"]}
              <p class="mt-1 text-xs text-destructive">{errors["primaryContact.name"]}</p>
            {/if}
          </div>
          <div>
            <label class="text-sm font-medium" for={fieldIds.primaryContactEmail}>Email *</label>
            <input
              id={fieldIds.primaryContactEmail}
              class="mt-1 w-full rounded-md border px-3 py-2"
              type="email"
              bind:value={formData.primaryContact.email}
            />
            {#if errors["primaryContact.email"]}
              <p class="mt-1 text-xs text-destructive">{errors["primaryContact.email"]}</p>
            {/if}
          </div>
          <div>
            <label class="text-sm font-medium" for={fieldIds.primaryContactPhone}>Phone</label>
            <input
              id={fieldIds.primaryContactPhone}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.primaryContact.phone}
            />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium" for={fieldIds.notes}>Notes</label>
          <textarea
            id={fieldIds.notes}
            class="mt-1 w-full rounded-md border px-3 py-2"
            rows="3"
            bind:value={formData.notes}
          ></textarea>
        </div>
      </div>
    {:else if currentStep === 2}
      <div class="space-y-4">
        <div>
          <label class="text-sm font-medium" for={fieldIds.tier}>Plan type</label>
          <select id={fieldIds.tier} class="mt-1 w-full rounded-md border px-3 py-2" bind:value={formData.tier}>
            {#each tierOptions as tier}
              <option value={tier}>{tier}</option>
            {/each}
          </select>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="text-sm font-medium" for={fieldIds.billingCycle}>Billing cycle</label>
            <select
              id={fieldIds.billingCycle}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.billingCycle}
            >
              {#each billingCycles as cycle}
                <option value={cycle}>{cycle}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="text-sm font-medium" for={fieldIds.paymentMethod}>Payment method</label>
            <select
              id={fieldIds.paymentMethod}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.paymentMethod}
            >
              {#each paymentMethods as method}
                <option value={method.value}>{method.label}</option>
              {/each}
            </select>
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-3">
          <div>
            <label class="text-sm font-medium" for={fieldIds.purchaseOrder}>Purchase order / reference</label>
            <input
              id={fieldIds.purchaseOrder}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.purchaseOrder}
            />
          </div>
          <div>
            <label class="text-sm font-medium" for={fieldIds.billingContactName}>Billing contact name</label>
            <input
              id={fieldIds.billingContactName}
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.billingContact.name}
            />
          </div>
          <div>
            <label class="text-sm font-medium" for="hub-currency">Currency</label>
            <input
              id="hub-currency"
              class="mt-1 w-full rounded-md border px-3 py-2"
              bind:value={formData.currency}
            />
          </div>
        </div>
        <div>
          <label class="text-sm font-medium" for={fieldIds.billingContactEmail}>Billing contact email *</label>
          <input
            id={fieldIds.billingContactEmail}
            class="mt-1 w-full rounded-md border px-3 py-2"
            type="email"
            bind:value={formData.billingContact.email}
          />
          {#if errors["billingContact.email"]}
            <p class="mt-1 text-xs text-destructive">{errors["billingContact.email"]}</p>
          {/if}
        </div>
        <div>
          <label class="text-sm font-medium" for="hub-billing-phone">Billing contact phone</label>
          <input
            id="hub-billing-phone"
            class="mt-1 w-full rounded-md border px-3 py-2"
            bind:value={formData.billingContact.phone}
          />
        </div>
      </div>
    {:else}
      <div class="space-y-4">
        {#each formData.operators as operator, index}
          <div class="rounded-lg border p-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold uppercase tracking-wide">Operator {index + 1}</p>
              {#if formData.operators.length > 1}
                <button type="button" class="text-xs text-muted-foreground underline" on:click={() => removeOperator(index)}>
                  Remove
                </button>
              {/if}
            </div>
            <div class="mt-3 grid gap-3 md:grid-cols-4">
              <div>
                <label class="text-xs font-medium" for={operatorFieldId(index, "name")}>Full name *</label>
                <input
                  id={operatorFieldId(index, "name")}
                  class="mt-1 w-full rounded-md border px-3 py-2"
                  bind:value={operator.name}
                />
                {#if errors[`operators.${index}.name`]}
                  <p class="mt-1 text-[0.65rem] text-destructive">{errors[`operators.${index}.name`]}</p>
                {/if}
              </div>
              <div>
                <label class="text-xs font-medium" for={operatorFieldId(index, "email")}>Email *</label>
                <input
                  id={operatorFieldId(index, "email")}
                  class="mt-1 w-full rounded-md border px-3 py-2"
                  type="email"
                  bind:value={operator.email}
                />
                {#if errors[`operators.${index}.email`]}
                  <p class="mt-1 text-[0.65rem] text-destructive">{errors[`operators.${index}.email`]}</p>
                {/if}
              </div>
              <div>
                <label class="text-xs font-medium" for={operatorFieldId(index, "role")}>Role</label>
                <select
                  id={operatorFieldId(index, "role")}
                  class="mt-1 w-full rounded-md border px-3 py-2"
                  bind:value={operator.role}
                >
                  {#each roleOptions as roleOption}
                    <option value={roleOption.value}>{roleOption.label}</option>
                  {/each}
                </select>
              </div>
              <div>
                <label class="text-xs font-medium" for={operatorFieldId(index, "password")}>Password *</label>
                <input
                  id={operatorFieldId(index, "password")}
                  class="mt-1 w-full rounded-md border px-3 py-2"
                  type="password"
                  minlength="8"
                  bind:value={operator.password}
                />
                {#if errors[`operators.${index}.password`]}
                  <p class="mt-1 text-[0.65rem] text-destructive">{errors[`operators.${index}.password`]}</p>
                {/if}
              </div>
            </div>
          </div>
        {/each}
        <button type="button" class="w-full rounded-md border border-dashed border-primary/50 py-2 text-sm font-medium text-primary" on:click={addOperator}>
          + Add another operator
        </button>
      </div>
    {/if}

    <div class="flex flex-wrap items-center gap-3 border-t pt-4">
      {#if serverMessage}
        <p class={`text-sm ${serverMessage.type === "success" ? "text-emerald-600" : "text-destructive"}`}>
          {serverMessage.text}
        </p>
      {/if}
      <div class="ml-auto flex gap-2">
        {#if currentStep > 1}
          <button type="button" class="rounded-md border px-4 py-2 text-sm" on:click={previousStep} disabled={isSubmitting}>
            Back
          </button>
        {/if}
        {#if currentStep < steps.length}
          <button type="button" class="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground" on:click={nextStep} disabled={isSubmitting}>
            Continue
          </button>
        {:else}
          <button
            type="submit"
            class="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-60"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Registering..." : "Create hub"}
          </button>
        {/if}
      </div>
    </div>
  </form>
</section>
