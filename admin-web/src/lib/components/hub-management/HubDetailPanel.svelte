<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { updateHub, createHubUser } from "$lib/api/hubs";
  import type { Hub } from "$lib/types/hub";
  import { hubChangeLogStore, type HubChangeLogEntry } from "$lib/stores/hub-change-log";
  import TerminalLogPanel from "$lib/components/TerminalLogPanel.svelte";
  import { confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";

  export let selectedHub: Hub | null = null;
  export let loading = false;
  export let changeLog: HubChangeLogEntry[] = [];

  const dispatcher = createEventDispatcher();
  const roleOptions = [
    { value: "client", label: "Client" },
    { value: "company", label: "Company Manager" },
  ];

  let statusMessage: { type: "success" | "error"; text: string } | null = null;
  let isSaving = false;
  let isInviting = false;
  let previousHubId: string | null = null;

  const profileFieldIds = {
    tier: "hub-detail-tier",
    status: "hub-detail-status",
    billingCycle: "hub-detail-billing-cycle",
    paymentMethod: "hub-detail-payment-method",
    primaryContactName: "hub-detail-primary-name",
    primaryContactEmail: "hub-detail-primary-email",
    billingContactName: "hub-detail-billing-name",
    billingContactEmail: "hub-detail-billing-email",
    notes: "hub-detail-notes",
    userName: "hub-detail-user-name",
    userEmail: "hub-detail-user-email",
    userRole: "hub-detail-user-role",
  } as const;

  let editForm = {
    tier: "",
    billingCycle: "monthly",
    paymentMethod: "manual_invoice",
    status: "active",
    primaryContact: { name: "", email: "", phone: "" },
    billingContact: { name: "", email: "" },
    notes: "",
  };

  let userForm = { name: "", email: "", role: roleOptions[0].value, password: "" };

  $: if (selectedHub?.id && selectedHub.id !== previousHubId) {
    editForm = {
      tier: selectedHub.tier,
      billingCycle: selectedHub.billingCycle ?? "monthly",
      paymentMethod: selectedHub.paymentMethod ?? "manual_invoice",
      status: selectedHub.status ?? "active",
      primaryContact: { ...selectedHub.primaryContact },
      billingContact: { ...selectedHub.billingContact },
      notes: selectedHub.notes ?? "",
    };
    previousHubId = selectedHub.id;
    statusMessage = null;
  }

  function formatDate(value?: string | null) {
    if (!value) return "TBD";
    try {
      return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
    } catch (error) {
      return value;
    }
  }

  function appendLog(action: HubChangeLogEntry["action"], details: string) {
    if (!selectedHub) return;
    hubChangeLogStore.append({
      id: globalThis.crypto?.randomUUID?.() ?? `hub-log-${Date.now()}`,
      timestamp: new Date().toISOString(),
      actor: "Console operator",
      action,
      hubId: selectedHub.id,
      summary: `${selectedHub.name} (${selectedHub.code})`,
      details,
    });
  }

  async function saveHub() {
    if (!selectedHub) {
      return;
    }
    if (!(await confirmSave({ title: "Save hub profile", message: "Save these hub profile changes?" }))) {
      return;
    }
    isSaving = true;
    statusMessage = null;
    try {
      const payload = {
        ...selectedHub,
        tier: editForm.tier,
        billingCycle: editForm.billingCycle,
        paymentMethod: editForm.paymentMethod,
        status: editForm.status,
        primaryContact: { ...editForm.primaryContact },
        billingContact: { ...editForm.billingContact },
        notes: editForm.notes,
      };
      const hub = await updateHub(selectedHub.id, payload);
      appendLog("update", `Updated plan ${hub.tier} · Billing ${hub.billingCycle}`);
      dispatcher("updated", { hub, message: "Hub profile saved" });
      statusMessage = { type: "success", text: "Hub profile updated." };
    } catch (error) {
      console.error("Failed to update hub", error);
      statusMessage = { type: "error", text: "Unable to save hub changes." };
    } finally {
      isSaving = false;
      resetFocusAfterSave();
    }
  }

  async function inviteUser() {
    if (!selectedHub) {
      return;
    }
    if (!userForm.name.trim() || !userForm.email.trim()) {
      statusMessage = { type: "error", text: "Operator name and email are required." };
      return;
    }
    isInviting = true;
    statusMessage = null;
    try {
      const user = await createHubUser(selectedHub.id, userForm);
      const updatedHub = {
        ...selectedHub,
        users: [...(selectedHub.users ?? []), user],
      };
      dispatcher("updated", { hub: updatedHub, message: `Added operator ${user.name}` });
      appendLog("user-create", `Invited ${user.name} (${user.role})`);
      userForm = { name: "", email: "", role: roleOptions[0].value, password: "" };
      statusMessage = { type: "success", text: "Operator invitation queued." };
    } catch (error) {
      console.error("Failed to invite user", error);
      statusMessage = { type: "error", text: "Unable to invite operator." };
    } finally {
      isInviting = false;
    }
  }

  function requestClose() {
    dispatcher("close");
  }
</script>

<div class="mt-6 space-y-6">
  <div class="flex flex-wrap items-center gap-3">
    <div>
      <p class="text-sm font-medium text-primary">Hub workspace</p>
      <h4 class="text-2xl font-semibold">{selectedHub?.name}</h4>
      <p class="text-xs text-muted-foreground">{selectedHub?.code} · {selectedHub?.country}</p>
    </div>
    <span class="rounded-full border border-border/60 px-3 py-1 text-xs uppercase tracking-wide text-muted-foreground">
      {selectedHub?.status}
    </span>
    <button type="button" class="ml-auto text-sm text-muted-foreground underline" on:click={requestClose}>Back to list</button>
  </div>

  {#if loading}
    <div class="omni-loading-state">
      <span class="omni-loading-spinner" aria-hidden="true"></span>
      <span>Loading hub profile…</span>
    </div>
  {:else if selectedHub}
    <div class="space-y-6">
      <div class="grid gap-4 md:grid-cols-3">
        <div class="rounded-lg border p-4">
          <p class="text-xs text-muted-foreground">Plan</p>
          <p class="text-lg font-semibold">{selectedHub.tier}</p>
        </div>
        <div class="rounded-lg border p-4">
          <p class="text-xs text-muted-foreground">Devices deployed</p>
          <p class="text-lg font-semibold">{selectedHub.deviceCount}</p>
        </div>
        <div class="rounded-lg border p-4">
          <p class="text-xs text-muted-foreground">Go-live target</p>
          <p class="text-lg font-semibold">{formatDate(selectedHub.goLiveDate)}</p>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <section class="space-y-4 rounded-lg border p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-primary">Profile</p>
              <h5 class="text-lg font-semibold">Operational settings</h5>
            </div>
            <button
              type="button"
              class="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-60"
              on:click={saveHub}
              disabled={isSaving}
            >
              {isSaving ? "Saving..." : "Save changes"}
            </button>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="text-xs font-medium" for={profileFieldIds.tier}>Plan type</label>
              <select
                id={profileFieldIds.tier}
                class="mt-1 w-full rounded-md border px-3 py-2"
                bind:value={editForm.tier}
              >
                <option value="Individual">Individual</option>
                <option value="Business">Business</option>
              </select>
            </div>
            <div>
              <label class="text-xs font-medium" for={profileFieldIds.status}>Status</label>
              <select
                id={profileFieldIds.status}
                class="mt-1 w-full rounded-md border px-3 py-2"
                bind:value={editForm.status}
              >
                <option value="active">Active</option>
                <option value="provisioning">Provisioning</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="text-xs font-medium" for={profileFieldIds.billingCycle}>Billing cycle</label>
              <select
                id={profileFieldIds.billingCycle}
                class="mt-1 w-full rounded-md border px-3 py-2"
                bind:value={editForm.billingCycle}
              >
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <div>
              <label class="text-xs font-medium" for={profileFieldIds.paymentMethod}>Payment method</label>
              <select
                id={profileFieldIds.paymentMethod}
                class="mt-1 w-full rounded-md border px-3 py-2"
                bind:value={editForm.paymentMethod}
              >
                <option value="manual_invoice">Manual invoice</option>
                <option value="card_on_file">Card on file</option>
                <option value="bank_transfer">Wire / EFT</option>
              </select>
            </div>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="text-xs font-medium" for={profileFieldIds.primaryContactName}>Primary contact</label>
              <input
                id={profileFieldIds.primaryContactName}
                class="mt-1 w-full rounded-md border px-3 py-2"
                bind:value={editForm.primaryContact.name}
              />
              <label class="sr-only" for={profileFieldIds.primaryContactEmail}>Primary contact email</label>
              <input
                id={profileFieldIds.primaryContactEmail}
                class="mt-2 w-full rounded-md border px-3 py-2"
                type="email"
                bind:value={editForm.primaryContact.email}
              />
            </div>
            <div>
              <label class="text-xs font-medium" for={profileFieldIds.billingContactName}>Billing contact</label>
              <input
                id={profileFieldIds.billingContactName}
                class="mt-1 w-full rounded-md border px-3 py-2"
                bind:value={editForm.billingContact.name}
              />
              <label class="sr-only" for={profileFieldIds.billingContactEmail}>Billing contact email</label>
              <input
                id={profileFieldIds.billingContactEmail}
                class="mt-2 w-full rounded-md border px-3 py-2"
                type="email"
                bind:value={editForm.billingContact.email}
              />
            </div>
          </div>
          <div>
            <label class="text-xs font-medium" for={profileFieldIds.notes}>Notes</label>
            <textarea
              id={profileFieldIds.notes}
              class="mt-1 w-full rounded-md border px-3 py-2"
              rows="3"
              bind:value={editForm.notes}
            ></textarea>
          </div>
        </section>

        <section class="space-y-3 rounded-lg border p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-primary">Operators</p>
              <h5 class="text-lg font-semibold">Assign hub users</h5>
            </div>
          </div>

                  <div class="grid gap-3">
                    {#each selectedHub.users ?? [] as user}
                      <div class="rounded-md border px-3 py-2" aria-label="Hub user" role="listitem">
                        <p class="text-sm font-semibold">{user.name}</p>
                        <p class="text-xs text-muted-foreground">{user.email} · {user.role}</p>
                      </div>
                    {/each}
                  </div>

          <div class="mt-4 space-y-3 rounded-md border border-dashed p-3">
            <div class="grid gap-3 md:grid-cols-2">
              <div>
                <label class="text-xs font-medium" for={profileFieldIds.userName}>Name</label>
                <input
                  id={profileFieldIds.userName}
                  class="mt-1 w-full rounded-md border px-3 py-2"
                  bind:value={userForm.name}
                  placeholder="Operator name"
                />
              </div>
              <div>
                <label class="text-xs font-medium" for={profileFieldIds.userEmail}>Email</label>
                <input
                  id={profileFieldIds.userEmail}
                  class="mt-1 w-full rounded-md border px-3 py-2"
                  type="email"
                  bind:value={userForm.email}
                  placeholder="operator@hub.dev"
                />
              </div>
            </div>
            <div>
              <label class="text-xs font-medium" for={profileFieldIds.userRole}>Role</label>
              <select
                id={profileFieldIds.userRole}
                class="mt-1 w-full rounded-md border px-3 py-2"
                bind:value={userForm.role}
              >
                {#each roleOptions as roleOption}
                  <option value={roleOption.value}>{roleOption.label}</option>
                {/each}
              </select>
            </div>
            <div>
              <label class="text-xs font-medium" for="hub-detail-user-password">Password</label>
              <input
                id="hub-detail-user-password"
                class="mt-1 w-full rounded-md border px-3 py-2"
                type="password"
                minlength="8"
                bind:value={userForm.password}
                placeholder="Minimum 8 characters"
              />
            </div>
            <button
              type="button"
              class="w-full rounded-md bg-secondary px-3 py-2 text-sm font-semibold text-secondary-foreground disabled:opacity-60"
              on:click={inviteUser}
              disabled={isInviting || !userForm.password || userForm.password.length < 8}
            >
              {isInviting ? "Inviting..." : "Invite operator"}
            </button>
          </div>
        </section>
      </div>

      <section class="rounded-lg border p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-primary">Immutable change log</p>
            <h5 class="text-lg font-semibold">Last {Math.min(changeLog.length, 6)} events</h5>
          </div>
          <button type="button" class="text-sm text-muted-foreground underline" on:click={requestClose}>
            Close detail
          </button>
        </div>
        {#if changeLog.length === 0}
          <p class="mt-4 text-sm text-muted-foreground">No recorded actions yet for this hub.</p>
        {:else}
          <div class="mt-4">
            <TerminalLogPanel
              panelTitle="hub-change-log"
              panelCountLabel="entries"
              tone="amber"
              maxHeight="16rem"
              entries={changeLog.slice(0, 6)}
              columns={[
                { key: "timestamp", label: "Timestamp", render: (entry) => new Date(String(entry.timestamp ?? "")).toLocaleString() },
                { key: "action", label: "Action", render: (entry) => String(entry.action ?? "") },
                { key: "details", label: "Details", render: (entry) => String(entry.details ?? "") },
                { key: "actor", label: "User", render: (entry) => String(entry.actor ?? "") },
              ]}
            />
          </div>
        {/if}
      </section>
    </div>
  {/if}

  {#if statusMessage}
    <div class={`rounded-md border px-3 py-2 text-sm ${
      statusMessage.type === "success" ? "border-emerald-300 bg-emerald-50 text-emerald-700" : "border-destructive/60 bg-destructive/10 text-destructive"
    }`}>
      {statusMessage.text}
    </div>
  {/if}
</div>
