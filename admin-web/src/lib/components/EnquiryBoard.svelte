<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { fetchEnquiries, updateEnquiry } from "$lib/api/enquiries";
  import type { Enquiry, EnquiryStatus } from "$lib/types/enquiry";
  import { Button } from "$lib/components/ui/button";
  import { RefreshCw, CheckCircle, AlertTriangle } from "lucide-svelte";
  import { confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  let enquiries: Enquiry[] = [];
  let selectedId: string | null = null;
  let selected: Enquiry | null = null;
  let loading = false;
  let saving = false;
  let errorMessage: string | null = null;
  let statusFilter: EnquiryStatus | "all" = "all";
  let searchTerm = "";
  let statusMessage: { type: "success" | "error"; text: string } | null = null;
  let enquiryWindowOpen = false;

  let editStatus: EnquiryStatus = "new";
  let quotedMonthly = "";
  let quotedHardwareTotal = "";
  let adminNotes = "";

  onMount(() => {
    void loadEnquiries();
  });

  onDestroy(() => {});

  async function loadEnquiries() {
    loading = true;
    errorMessage = null;
    statusMessage = null;
    try {
      enquiries = await fetchEnquiries({ status: statusFilter });
      if (selectedId) {
        const match = enquiries.find((item) => item.id === selectedId);
        if (match) {
          selectEnquiry(match);
        }
      }
    } catch (error) {
      console.error("Failed to load enquiries", error);
      errorMessage = "Unable to load enquiries right now.";
    } finally {
      loading = false;
    }
  }

  function selectEnquiry(enquiry: Enquiry) {
    selectedId = enquiry.id;
    selected = enquiry;
    editStatus = enquiry.status;
    quotedMonthly = enquiry.quoted_monthly ? String(enquiry.quoted_monthly) : "";
    quotedHardwareTotal = enquiry.quoted_hardware_total ? String(enquiry.quoted_hardware_total) : "";
    adminNotes = enquiry.admin_notes ?? "";
    statusMessage = null;
  }


  function openEnquiry(enquiry: Enquiry) {
    selectEnquiry(enquiry);
    enquiryWindowOpen = true;
  }

  function closeEnquiryWindow() {
    enquiryWindowOpen = false;
  }

  function matchesSearch(enquiry: Enquiry) {
    if (!searchTerm.trim()) return true;
    const needle = searchTerm.toLowerCase();
    return (
      enquiry.full_name.toLowerCase().includes(needle) ||
      enquiry.email.toLowerCase().includes(needle) ||
      (enquiry.company_name ?? "").toLowerCase().includes(needle)
    );
  }

  function filteredEnquiries() {
    return enquiries.filter(matchesSearch);
  }

  async function saveChanges() {
    if (!selected) return;
    if (!(await confirmSave({ title: "Save enquiry", message: "Save these enquiry changes?" }))) {
      return;
    }
    saving = true;
    statusMessage = null;
    try {
      const payload = {
        status: editStatus,
        quoted_monthly: quotedMonthly ? Number(quotedMonthly) : null,
        quoted_hardware_total: quotedHardwareTotal ? Number(quotedHardwareTotal) : null,
        admin_notes: adminNotes,
        quote_sent_at: editStatus === "quoted" ? new Date().toISOString() : null,
        responded_at: editStatus === "quoted" ? new Date().toISOString() : null,
        closed_at: editStatus === "closed_lost" ? new Date().toISOString() : null,
      };
      const updated = await updateEnquiry(selected.id, payload);
      enquiries = enquiries.map((item) => (item.id === updated.id ? updated : item));
      selectEnquiry(updated);
      statusMessage = { type: "success", text: "Enquiry updated." };
      toastStore.push({
        title: "Enquiry updated",
        message: `Saved changes for ${updated.full_name}.`,
        tone: "success",
      });
    } catch (error) {
      console.error("Failed to update enquiry", error);
      statusMessage = { type: "error", text: "Unable to save changes." };
    } finally {
      saving = false;
      resetFocusAfterSave();
    }
  }
</script>

<div class="space-y-6 marketing-reveal">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Operations</p>
      <h2 class="omni-page-title">Enquiries</h2>
    </div>
    <div class="flex items-center gap-2">
      <Button variant="outline" size="sm" onclick={loadEnquiries} disabled={loading}>
        <RefreshCw class="h-4 w-4" />
        Refresh
      </Button>
    </div>
  </header>

  <div class={enquiryWindowOpen ? "space-y-6" : "omni-page-grid"}>
    {#if !enquiryWindowOpen}
    <div class="omni-list-stage">
      <div class="omni-panel border-0 shadow-none p-5">
        <div class="omni-toolbar-strip">
          <input
            type="text"
            class="omni-input min-w-[16rem] flex-1"
            placeholder="Search by name, email, or company"
            bind:value={searchTerm}
          />
          <select
            class="omni-select min-w-[12rem]"
            bind:value={statusFilter}
            on:change={loadEnquiries}
          >
            <option value="all">All statuses</option>
            <option value="new">New</option>
            <option value="quoted">Quoted</option>
            <option value="awaiting_payment">Awaiting payment</option>
            <option value="onboarded">Onboarded</option>
            <option value="closed_lost">Closed - lost</option>
          </select>
        </div>
      </div>

      {#if loading}
        <div class="omni-loading-state">
          <span class="omni-loading-spinner" aria-hidden="true"></span>
          <span>Loading enquiries…</span>
        </div>
      {:else if errorMessage}
        <div class="rounded-[1.35rem] border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          {errorMessage}
        </div>
      {:else if filteredEnquiries().length === 0}
        <div class="omni-empty-state py-8">
          No enquiries match the current filter.
        </div>
      {:else}
        <div class="omni-table-shell overflow-auto">
          <table class="omni-table min-w-[760px]">
            <thead>
              <tr>
                <th>Contact</th>
                <th>Company</th>
                <th>Type</th>
                <th>Status</th>
                <th>Submitted</th>
                <th class="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredEnquiries() as enquiry (enquiry.id)}
                <tr class={selectedId === enquiry.id ? "omni-row-active" : ""}>
                  <td>
                    <div class="font-medium">{enquiry.full_name}</div>
                    <div class="text-xs text-muted-foreground">{enquiry.email}</div>
                  </td>
                  <td>{enquiry.company_name || "—"}</td>
                  <td class="capitalize">{enquiry.customer_type}</td>
                  <td>
                    <span class="rounded-full bg-slate-100 px-2 py-1 text-xs uppercase tracking-widest text-slate-600 dark:bg-white/5 dark:text-slate-300">
                      {enquiry.status.replace("_", " ")}
                    </span>
                  </td>
                  <td class="text-xs text-muted-foreground">{new Date(enquiry.created_at).toLocaleDateString()}</td>
                  <td class="text-right">
                    <Button size="sm" variant="outline" onclick={() => openEnquiry(enquiry)}>Open</Button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
    {/if}

    <div class={enquiryWindowOpen ? "" : "omni-inspector-stage"} id="enquiry-detail-panel">
    <div class="omni-panel border-0 shadow-none p-6">
      {#if selected}
        <div class="space-y-5 omni-animate-fade">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-cyan-300/70">Enquiry profile</p>
              <h3 class="mt-2 text-2xl font-semibold">{selected.full_name}</h3>
              <p class="text-sm text-muted-foreground">{selected.email} · {selected.phone}</p>
            </div>
            <span class="rounded-full border border-white/70 bg-white/70 px-3 py-1 text-xs uppercase tracking-widest text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300">
              {selected.customer_type}
            </span>
            <Button size="sm" variant="outline" onclick={closeEnquiryWindow}>Back</Button>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs uppercase tracking-widest text-slate-500">Hardware</p>
              <ul class="mt-3 space-y-1 text-sm text-slate-700">
                {#each selected.hardware_choices as item}
                  <li>• {item}</li>
                {/each}
              </ul>
            </div>
            <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 dark:border-slate-800 dark:bg-slate-950/45">
              <p class="text-xs uppercase tracking-widest text-slate-500">Add-ons</p>
              {#if selected.add_ons.length === 0}
                <p class="mt-3 text-sm text-slate-500">None selected</p>
              {:else}
                <ul class="mt-3 space-y-1 text-sm text-slate-700">
                  {#each selected.add_ons as item}
                    <li>• {item}</li>
                  {/each}
                </ul>
              {/if}
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
              <p class="text-xs uppercase tracking-widest text-slate-500">Fleet size</p>
              <p class="mt-2">{selected.fleet_size || "—"}</p>
            </div>
            <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
              <p class="text-xs uppercase tracking-widest text-slate-500">Operating area</p>
              <p class="mt-2">{selected.operating_area || "—"}</p>
            </div>
            <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
              <p class="text-xs uppercase tracking-widest text-slate-500">Preferred contact</p>
              <p class="mt-2">{selected.preferred_contact_method || "—"}</p>
            </div>
            <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
              <p class="text-xs uppercase tracking-widest text-slate-500">Expected go-live</p>
              <p class="mt-2">{selected.expected_go_live_date ? new Date(selected.expected_go_live_date).toLocaleDateString() : "—"}</p>
            </div>
          </div>

          <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
            <p class="text-xs uppercase tracking-widest text-slate-500">Tracking use case</p>
            <p class="mt-2">{selected.tracking_use_case || "—"}</p>
          </div>

          {#if selected.message}
            <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/45 dark:text-slate-300">
              <p class="text-xs uppercase tracking-widest text-slate-500">Message</p>
              <p class="mt-2">{selected.message}</p>
            </div>
          {/if}

          <div class="omni-detail-section">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p class="omni-kicker">Commercial response</p>
                <h4 class="mt-2 text-lg font-semibold">Quotation and follow-up</h4>
              </div>
              <span class="rounded-full border border-white/70 bg-white/70 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-600 dark:border-white/10 dark:bg-slate-950/45 dark:text-slate-300">{selected.status.replace("_", " ")}</span>
            </div>

            <div class="omni-form-grid mt-5">
              <div class="omni-field">
                <label for="enquiry-status">Status</label>
                <select id="enquiry-status" class="omni-select" bind:value={editStatus}>
                  <option value="new">New</option>
                  <option value="quoted">Quoted</option>
                  <option value="awaiting_payment">Awaiting payment</option>
                  <option value="onboarded">Onboarded</option>
                  <option value="closed_lost">Closed - lost</option>
                </select>
              </div>
              <div class="omni-field">
                <label for="quoted-monthly">Quoted monthly ($)</label>
                <input
                  id="quoted-monthly"
                  type="number"
                  min="0"
                  step="0.01"
                  class="omni-input"
                  bind:value={quotedMonthly}
                />
              </div>
              <div class="omni-field md:col-span-2">
                <label for="quoted-hardware-total">Quoted hardware total ($)</label>
                <input
                  id="quoted-hardware-total"
                  type="number"
                  min="0"
                  step="0.01"
                  class="omni-input"
                  bind:value={quotedHardwareTotal}
                />
              </div>
              <div class="omni-field md:col-span-2">
                <label for="enquiry-admin-notes">Admin notes</label>
                <textarea
                  id="enquiry-admin-notes"
                  rows="4"
                  class="omni-textarea"
                  bind:value={adminNotes}
                ></textarea>
              </div>
            </div>
          </div>

          {#if statusMessage}
            <div
              class={`rounded-[1.25rem] border px-4 py-3 text-sm ${
                statusMessage.type === "success"
                  ? "border-emerald-100 bg-emerald-50 text-emerald-700"
                  : "border-red-100 bg-red-50 text-red-700"
              }`}
            >
              {#if statusMessage.type === "success"}
                <CheckCircle class="mr-2 inline h-4 w-4" />
              {:else}
                <AlertTriangle class="mr-2 inline h-4 w-4" />
              {/if}
              {statusMessage.text}
            </div>
          {/if}

          <div class="flex items-center justify-between">
            <p class="text-xs text-muted-foreground">
              Submitted {new Date(selected.created_at).toLocaleString()}
            </p>
            <Button onclick={saveChanges} disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </div>
      {:else}
        <div class="omni-empty-state py-10">
          Select an enquiry to review details and prepare a quotation.
        </div>
      {/if}
    </div>
    </div>
  </div>
</div>
