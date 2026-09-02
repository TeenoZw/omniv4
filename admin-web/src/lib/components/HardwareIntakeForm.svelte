<script>
  import { intakeHardware } from "$lib/api/devices";
  import { sessionStore } from "$lib/stores/session";
  import { confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  const DEVICE_TYPES = [
    "2G Tracker",
    "4G Tracker",
    "Liquid Level Sensor",
    "OBD Tracker",
    "CAN Adapter",
    "ID Device (iButtons)",
  ];

  const EMPTY_FORM = {
    manufacturer: "",
    model: "",
    imei: "",
    serialNumber: "",
    hardwareType: DEVICE_TYPES[0],
    description: "",
    firmwareVersion: "",
    purchaseDate: "",
    notes: "",
  };

  let form = { ...EMPTY_FORM };
  let submitting = false;
  let message = null;
  let variant = null;

  $: session = $sessionStore;
  $: isAuthenticated = Boolean(session?.token);
  $: activeHubId = session?.currentHubId ?? session?.hubs?.[0]?.id ?? null;

  function resetForm() {
    form = { ...EMPTY_FORM };
  }

  async function handleSubmit(event) {
    event?.preventDefault();
    if (!isAuthenticated) {
      message = "Authenticate before capturing intake.";
      variant = "error";
      return;
    }
    if (!form.serialNumber.trim()) {
      message = "Serial number is mandatory.";
      variant = "error";
      return;
    }
    if (!form.manufacturer.trim() || !form.model.trim() || !form.imei.trim()) {
      message = "Manufacturer, model, and IMEI are required.";
      variant = "error";
      return;
    }
    if (!(await confirmSave({ title: "Save hardware", message: "Save this hardware intake record?" }))) {
      return;
    }

    submitting = true;
    message = null;
    variant = null;

    try {
      const payload = {
        manufacturer: form.manufacturer.trim(),
        model: form.model.trim(),
        imei: form.imei.trim(),
        serialNumber: form.serialNumber.trim(),
        hardwareType: form.hardwareType.trim(),
        description: form.description.trim() || undefined,
        firmwareVersion: form.firmwareVersion.trim() || undefined,
        notes: form.notes.trim() || undefined,
        purchaseDate: form.purchaseDate || undefined,
      };

      await intakeHardware(payload, {
        token: session?.token ?? undefined,
        hubId: activeHubId ?? undefined,
      });
      message = "Hardware captured and ready for assignment.";
      variant = "success";
      toastStore.push({
        title: "Hardware saved",
        message: `${payload.imei} is now ready for assignment.`,
        tone: "success",
      });
      resetForm();
    } catch (error) {
      const statusCode = error?.response?.status;
      if (statusCode === 401) {
        message = "Session expired. Sign in again to intake hardware.";
      } else if (statusCode === 400 && error?.response?.data?.detail?.includes("X-Hub-ID")) {
        message = "Select a hub to scope intake or contact an admin for global intake access.";
      } else {
        const detail = error?.response?.data?.detail ?? error?.message ?? "Failed to save hardware.";
        message = detail;
      }
      variant = "error";
    } finally {
      submitting = false;
      resetFocusAfterSave();
    }
  }
</script>

<section
  id="hardware-intake"
  class="rounded-3xl border border-slate-200 bg-white p-6 text-slate-900 dark:border-white/10 dark:bg-black/20 dark:text-white"
>
  <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.4em] text-primary">Hardware Intake</p>
      <h2 class="text-2xl font-semibold">Capture new trackers and sensors</h2>
    </div>
    <span
      class="rounded-full border border-slate-300 px-4 py-1 text-xs uppercase tracking-[0.3em] text-slate-600 dark:border-white/20 dark:text-white/70"
    >
      Stage 1 · Intake
    </span>
  </div>

  <form class="mt-6 grid gap-4 md:grid-cols-2" on:submit|preventDefault={handleSubmit}>
    <div>
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-manufacturer">Manufacturer *</label>
      <input
        id="intake-manufacturer"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        bind:value={form.manufacturer}
        required
        placeholder="e.g., Teltonika"
      />
    </div>
    <div>
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-model">Model *</label>
      <input
        id="intake-model"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        bind:value={form.model}
        required
        placeholder="e.g., FMB920"
      />
    </div>
    <div>
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-imei">IMEI *</label>
      <input
        id="intake-imei"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        bind:value={form.imei}
        required
        autocomplete="off"
      />
    </div>
    <div>
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-serial">Serial Number *</label>
      <input
        id="intake-serial"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        bind:value={form.serialNumber}
        required
        placeholder="Device serial"
      />
    </div>
    <div>
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-type">Device Type</label>
      <select
        id="intake-type"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-white/15 dark:bg-black/40 dark:text-white"
        bind:value={form.hardwareType}
      >
        {#each DEVICE_TYPES as t}
          <option value={t}>{t}</option>
        {/each}
      </select>
    </div>
    <div class="md:col-span-2">
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-description">Description</label>
      <textarea
        id="intake-description"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        rows="3"
        bind:value={form.description}
        placeholder="Notes about tracker/sensor"
      ></textarea>
    </div>
    <div>
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-firmware">Firmware</label>
      <input
        id="intake-firmware"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        bind:value={form.firmwareVersion}
        placeholder="e.g., 3.4.1"
      />
    </div>
    <div>
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-purchase">Purchase Date</label>
      <input
        id="intake-purchase"
        type="date"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        bind:value={form.purchaseDate}
      />
    </div>
    <div class="md:col-span-2">
      <label class="text-xs uppercase tracking-[0.3em] text-slate-600 dark:text-white/70" for="intake-notes">Notes</label>
      <textarea
        id="intake-notes"
        class="mt-1 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 dark:border-white/15 dark:bg-black/40 dark:text-white dark:placeholder:text-white/40"
        rows="3"
        bind:value={form.notes}
        placeholder="Receiving notes, condition, kit contents"
      ></textarea>
    </div>
    <div class="md:col-span-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div></div>
      <div class="flex gap-2">
        <button
          type="button"
          class="rounded-2xl border border-slate-300 bg-slate-50 px-4 py-2 text-sm text-slate-900 hover:border-slate-400 dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:border-white/40"
          on:click={resetForm}
          disabled={submitting}
        >
          Clear
        </button>
        <button
          type="submit"
          class="rounded-2xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-primary/40 disabled:opacity-50"
          disabled={submitting}
        >
          {submitting ? "Saving..." : "Save hardware"}
        </button>
      </div>
    </div>
  </form>

  {#if message}
    <p class={`mt-3 text-sm ${variant === "error" ? "text-rose-700 dark:text-rose-200" : "text-emerald-700 dark:text-emerald-200"}`}>
      {message}
    </p>
  {/if}
</section>
