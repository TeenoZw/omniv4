<script>
  import { onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { createHubUser, fetchHubById, fetchHubs, updateHubUser } from "$lib/api/hubs";
  import { createSystemUser, deactivateSystemUser, fetchUsers, updateSystemUser } from "$lib/api/users";
  import { adminLogStore } from "$lib/stores/admin-log";
  import { confirmAndRun, confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  let hubs = [];
  let selectedHubId = "";
  let selectedHub = null;
  let systemUsers = [];
  let loading = false;
  let saving = false;
  let feedback = "";
  let hubSearch = "";
  let userSearch = "";
  let roleFilter = "all";
  let accessPage = "home";

  let hubUserForm = {
    name: "",
    email: "",
    role: "client",
    password: "",
  };
  let internalUserForm = {
    name: "",
    email: "",
    role: "admin",
    password: "",
  };
  let editingUserId = "";
  let editingContext = "hub";
  let editForm = {
    name: "",
    email: "",
    role: "client",
    password: "",
    isActive: true,
  };

  const hubRoleOptions = [
    { value: "client", label: "Client" },
    { value: "company", label: "Company Manager" },
  ];
  const internalRoleOptions = [
    { value: "admin", label: "Admin" },
    { value: "technician", label: "Technician" },
  ];
  const allRoleOptions = [...internalRoleOptions, ...hubRoleOptions];
  const accessPages = [
    { value: "editor", label: "User editor", hint: "Review and manage one existing account" },
    { value: "internal", label: "Internal Users", hint: "Create Omni admin and technician accounts" },
    { value: "hub", label: "Hub Access", hint: "Create customer-facing accounts for the selected hub" },
    { value: "matrix", label: "Permissions", hint: "Reference the customer role baseline" },
  ];

  const permissions = [
    { role: "client", canView: true, canEdit: false, canManageUsers: false, canBilling: false },
    { role: "company", canView: true, canEdit: true, canManageUsers: true, canBilling: true },
  ];

  function isInternalRole(role) {
    return ["admin", "technician"].includes((role ?? "").toLowerCase());
  }

  function isAssignedToSelectedHub(user) {
    return (selectedHub?.users ?? []).some((hubUser) => hubUser.id === user.id);
  }

  function startEditUser(user) {
    editingUserId = user.id;
    editingContext = isInternalRole(user.role) ? "system" : "hub";
    accessPage = "editor";
    editForm = {
      name: user.name ?? "",
      email: user.email ?? "",
      role: (user.role ?? (editingContext === "system" ? "admin" : "client")).toLowerCase(),
      password: "",
      isActive: Boolean(user.isActive ?? true),
    };
    feedback = "";
  }

  function cancelEditUser() {
    editingUserId = "";
    editingContext = "hub";
    accessPage = "home";
    editForm = {
      name: "",
      email: "",
      role: "client",
      password: "",
      isActive: true,
    };
  }

  $: filteredHubs = (hubs ?? []).filter((hub) =>
    `${hub.name} ${hub.code}`.toLowerCase().includes(hubSearch.trim().toLowerCase()),
  );
  $: if (filteredHubs.length > 0 && !filteredHubs.some((hub) => hub.id === selectedHubId)) {
    selectedHubId = filteredHubs[0].id;
  }
  $: filteredSystemUsers = (systemUsers ?? []).filter((user) => {
    const matchesRole = roleFilter === "all" ? true : (user.role ?? "").toLowerCase() === roleFilter;
    const matchesSearch = `${user.name} ${user.email}`.toLowerCase().includes(userSearch.trim().toLowerCase());
    return matchesRole && matchesSearch;
  });
  $: selectedSystemUser = filteredSystemUsers.find((user) => user.id === editingUserId) ?? null;
  $: internalUserCount = systemUsers.filter((user) => isInternalRole(user.role)).length;
  $: hubAssignedCount = selectedHub?.users?.length ?? 0;
  $: availableAccessPages = accessPages.filter((page) => page.value !== "editor" || editingUserId);

  async function loadHubs() {
    loading = true;
    try {
      hubs = await fetchHubs();
      if (!selectedHubId && hubs.length) {
        selectedHubId = hubs[0].id;
      }
      if (selectedHubId) {
        await loadHubDetail(selectedHubId);
      }
    } catch (error) {
      console.error("Unable to load hubs", error);
      feedback = "Unable to load hub access data.";
    } finally {
      loading = false;
    }
  }

  async function loadHubDetail(hubId) {
    if (!hubId) return;
    selectedHub = await fetchHubById(hubId);
  }

  async function loadSystemUsers() {
    try {
      systemUsers = await fetchUsers();
    } catch (error) {
      console.error("Unable to load system users", error);
      feedback = "Unable to load system users.";
      systemUsers = [];
    }
  }

  async function addHubUser() {
    if (!selectedHubId) return;
    await confirmAndRun(
      {
        title: "Create hub user",
        description: "Hub access",
        message: `Create this ${hubUserForm.role} account for ${selectedHub?.name ?? "the selected hub"}?`,
        confirmLabel: "Create account",
      },
      async () => {
        saving = true;
        feedback = "";
        try {
          await createHubUser(selectedHubId, hubUserForm);
          await Promise.all([loadHubDetail(selectedHubId), loadSystemUsers()]);
          adminLogStore.append({
            action: "hub-user-create",
            scope: "access-control",
            details: `Added ${hubUserForm.email} as ${hubUserForm.role} in hub ${selectedHub?.code ?? selectedHubId}`,
          });
          toastStore.push({
            title: "Hub account created",
            message: `${hubUserForm.email} was added to ${selectedHub?.name ?? "the selected hub"}.`,
            tone: "success",
          });
          feedback = "Hub user account created successfully.";
          hubUserForm = { name: "", email: "", role: "client", password: "" };
        } catch (error) {
          console.error("Unable to add hub user", error);
          feedback = error?.response?.data?.detail ?? "Unable to create the hub user account.";
        } finally {
          saving = false;
        }
      },
    );
  }

  async function addInternalUser() {
    await confirmAndRun(
      {
        title: "Create internal account",
        description: "Internal access",
        message: `Create this ${internalUserForm.role} account outside the hub model?`,
        confirmLabel: "Create account",
      },
      async () => {
        saving = true;
        feedback = "";
        try {
          const created = await createSystemUser(internalUserForm);
          await loadSystemUsers();
          adminLogStore.append({
            action: "system-user-create",
            scope: "access-control",
            details: `Created internal ${created.role} account for ${created.email}`,
          });
          toastStore.push({
            title: "Internal account created",
            message: `${created.email} can now sign in without hub membership.`,
            tone: "success",
          });
          feedback = "Internal account created successfully.";
          internalUserForm = { name: "", email: "", role: "admin", password: "" };
          startEditUser(created);
        } catch (error) {
          console.error("Unable to create internal user", error);
          feedback = error?.response?.data?.detail ?? "Unable to create the internal account.";
        } finally {
          saving = false;
        }
      },
    );
  }

  async function saveUserEdits() {
    if (!editingUserId) return;
    if (editForm.password && editForm.password.length < 8) {
      feedback = "The new password must contain at least 8 characters.";
      return;
    }
    if (!(await confirmSave({ title: "Save user changes", message: "Save these user account changes?" }))) {
      return;
    }

    saving = true;
    feedback = "";
    try {
      let updated;
      if (editingContext === "system") {
        updated = await updateSystemUser(editingUserId, {
          name: editForm.name,
          email: editForm.email,
          role: editForm.role,
          is_active: editForm.isActive,
          password: editForm.password || undefined,
        });
      } else {
        if (!selectedHubId) return;
        updated = await updateHubUser(selectedHubId, editingUserId, {
          name: editForm.name,
          email: editForm.email,
          role: editForm.role,
          password: editForm.password || undefined,
        });
      }
      await Promise.all([selectedHubId ? loadHubDetail(selectedHubId) : Promise.resolve(), loadSystemUsers()]);
      adminLogStore.append({
        action: editingContext === "system" ? "system-user-update" : "hub-user-update",
        scope: "access-control",
        details:
          editingContext === "system"
            ? `Updated internal account ${updated.email}`
            : `Updated ${updated.email} in hub ${selectedHub?.code ?? selectedHubId}`,
      });
      toastStore.push({
        title: "Account updated",
        message: `${updated.email} was updated successfully.`,
        tone: "success",
      });
      feedback = "User account updated successfully.";
      cancelEditUser();
    } catch (error) {
      console.error("Unable to update user", error);
      feedback = error?.response?.data?.detail ?? "Unable to update the user account.";
    } finally {
      saving = false;
      resetFocusAfterSave();
    }
  }

  async function deactivateSelectedSystemUser() {
    if (editingContext !== "system" || !selectedSystemUser) return;
    await confirmAndRun(
      {
        title: "Deactivate internal account",
        description: "Internal access",
        message: `Deactivate ${selectedSystemUser.email}? They will no longer be able to sign in.`,
        confirmLabel: "Deactivate account",
      },
      async () => {
        saving = true;
        feedback = "";
        try {
          await deactivateSystemUser(selectedSystemUser.id);
          await loadSystemUsers();
          adminLogStore.append({
            action: "system-user-deactivate",
            scope: "access-control",
            details: `Deactivated internal account ${selectedSystemUser.email}`,
          });
          toastStore.push({
            title: "Account deactivated",
            message: `${selectedSystemUser.email} can no longer sign in.`,
            tone: "success",
          });
          feedback = "Internal account deactivated successfully.";
          cancelEditUser();
        } catch (error) {
          console.error("Unable to deactivate internal user", error);
          feedback = error?.response?.data?.detail ?? "Unable to deactivate the internal account.";
        } finally {
          saving = false;
        }
      },
    );
  }

  $: if (selectedHubId) {
    void loadHubDetail(selectedHubId);
  } else {
    cancelEditUser();
  }

  onMount(() => {
    void Promise.all([loadHubs(), loadSystemUsers()]);
  });
</script>

<section class="space-y-6 marketing-reveal">
  <div class="omni-toolbar-strip">
    <label class="omni-toolbar-field">
      <span class="text-xs uppercase tracking-[0.22em] text-muted-foreground">Search hubs</span>
      <input
        id="hub-search"
        class="omni-input mt-2"
        type="search"
        placeholder="Search hubs by name or code"
        bind:value={hubSearch}
      />
    </label>
    <label class="omni-toolbar-field-compact">
      <span class="text-xs uppercase tracking-[0.22em] text-muted-foreground">Hub context</span>
      <select class="omni-select mt-2" bind:value={selectedHubId}>
        {#each filteredHubs as hub (hub.id)}
          <option value={hub.id}>{hub.name} ({hub.code})</option>
        {/each}
      </select>
    </label>
    <div class="ml-auto flex flex-wrap items-center gap-2">
      {#if selectedHub}
        <span class="omni-inline-stat">Hub code: {selectedHub.code}</span>
        <span class="omni-inline-stat">Tier: {selectedHub.subscription_tier ?? "—"}</span>
      {/if}
    </div>
  </div>

  <div class="omni-page-grid">
    <div class="omni-list-stage">
      <div class="p-0">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <h2 class="text-xl font-semibold">Users & Permissions</h2>
          <div class="flex flex-wrap items-center gap-2">
            <span class="omni-inline-stat">{filteredSystemUsers.length} visible</span>
            <span class="omni-inline-stat">{internalUserCount} internal</span>
            <span class="omni-inline-stat">{hubAssignedCount} in hub</span>
          </div>
        </div>

        <div class="omni-toolbar-strip mt-4">
          <label class="omni-toolbar-field">
            <span class="text-xs uppercase tracking-[0.22em] text-muted-foreground">Search users</span>
            <input
              class="omni-input mt-2"
              type="search"
              placeholder="Search by name or email"
              bind:value={userSearch}
            />
          </label>
          <label class="omni-toolbar-field-compact">
            <span class="text-xs uppercase tracking-[0.22em] text-muted-foreground">Role</span>
            <select class="omni-select mt-2" bind:value={roleFilter}>
              <option value="all">All roles</option>
              {#each allRoleOptions as roleOption}
                <option value={roleOption.value}>{roleOption.label}</option>
              {/each}
            </select>
          </label>
        </div>

        <div class="omni-table-shell mt-4 overflow-auto">
          <table class="omni-table min-w-[760px]">
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Role</th>
                <th>Scope</th>
                <th>Status</th>
                <th class="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {#if filteredSystemUsers.length}
                {#each filteredSystemUsers as user (user.id)}
                  <tr class={editingUserId === user.id ? "omni-row-active" : ""}>
                    <td class="font-medium">{user.name}</td>
                    <td class="text-muted-foreground">{user.email}</td>
                    <td class="uppercase text-xs tracking-[0.18em] text-muted-foreground">{user.role}</td>
                    <td class="text-muted-foreground">
                      {#if isInternalRole(user.role)}
                        Internal
                      {:else}
                        Hub-bound
                      {/if}
                    </td>
                    <td class="text-muted-foreground">
                      {#if isInternalRole(user.role)}
                        Global access
                      {:else if isAssignedToSelectedHub(user)}
                        Assigned to {selectedHub?.code}
                      {:else}
                        Not in selected hub
                      {/if}
                    </td>
                    <td class="text-right">
                      {#if isInternalRole(user.role) || isAssignedToSelectedHub(user)}
                        <Button size="sm" variant="outline" onclick={() => startEditUser(user)}>
                          {isInternalRole(user.role) ? "Manage" : "Edit"}
                        </Button>
                      {:else}
                        <span class="text-xs text-muted-foreground">View only</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              {:else}
                <tr>
                  <td colspan="6" class="text-sm text-muted-foreground">No users match the current search or filters.</td>
                </tr>
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="omni-inspector-stage">
      {#if accessPage === "home"}
        <div>
          <div class="mt-4 grid gap-3">
            {#if editingUserId}
              <button type="button" class="omni-action-card text-left" on:click={() => (accessPage = "editor")}>
                <span class="text-base font-semibold text-foreground">{editingContext === "system" ? "Continue editing internal account" : "Continue editing hub account"}</span>
              </button>
            {/if}
            <button type="button" class="omni-action-card text-left" on:click={() => (accessPage = "internal")}>
              <span class="text-base font-semibold text-foreground">Create Omni admin users</span>
            </button>
            <button type="button" class="omni-action-card text-left" on:click={() => (accessPage = "hub")}>
              <span class="text-base font-semibold text-foreground">Create selected-hub users</span>
            </button>
            <button type="button" class="omni-action-card text-left" on:click={() => (accessPage = "matrix")}>
              <span class="text-base font-semibold text-foreground">View role baseline</span>
            </button>
          </div>
        </div>
      {/if}

      {#if accessPage === "editor"}
        {#if editingUserId}
          <div class="omni-panel border-0 shadow-none p-5">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h4 class="text-lg font-semibold">{editingContext === "system" ? "Manage internal account" : "Edit hub account"}</h4>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <span class="rounded-full border border-border/70 bg-background/70 px-3 py-1 text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  {editingContext === "system" ? "Internal user" : "Hub user"}
                </span>
                <Button size="sm" variant="outline" onclick={() => (accessPage = "home")} disabled={saving}>Back</Button>
              </div>
            </div>
            <div class="omni-form-grid mt-5">
              <div class="omni-field">
                <label for="edit-user-name">Name</label>
                <input id="edit-user-name" class="omni-input" bind:value={editForm.name} />
              </div>
              <div class="omni-field">
                <label for="edit-user-email">Email</label>
                <input id="edit-user-email" class="omni-input" type="email" bind:value={editForm.email} />
              </div>
              <div class="omni-field">
                <label for="edit-user-role">Role</label>
                <select id="edit-user-role" class="omni-select" bind:value={editForm.role}>
                  {#each editingContext === "system" ? internalRoleOptions : hubRoleOptions as roleOption}
                    <option value={roleOption.value}>{roleOption.label}</option>
                  {/each}
                </select>
              </div>
              <div class="omni-field">
                <label for="edit-user-password">New password (optional)</label>
                <input id="edit-user-password" class="omni-input" type="password" minlength="8" bind:value={editForm.password} placeholder="Leave blank to keep the current password" />
              </div>
              {#if editingContext === "system"}
                <div class="omni-field">
                  <label for="edit-user-active">Account status</label>
                  <select id="edit-user-active" class="omni-select" bind:value={editForm.isActive}>
                    <option value={true}>Active</option>
                    <option value={false}>Inactive</option>
                  </select>
                </div>
              {/if}
            </div>
            <div class="mt-5 flex flex-wrap gap-2">
              <Button size="sm" onclick={saveUserEdits} disabled={saving || loading || !editForm.email || (editForm.password.length > 0 && editForm.password.length < 8)}>
                {saving ? "Saving..." : "Save changes"}
              </Button>
              {#if editingContext === "system"}
                <Button size="sm" variant="outline" onclick={deactivateSelectedSystemUser} disabled={saving || !selectedSystemUser?.isActive}>
                  Deactivate
                </Button>
              {/if}
              <Button size="sm" variant="outline" onclick={cancelEditUser} disabled={saving}>Cancel</Button>
            </div>
            {#if editingContext === "system"}
              <p class="mt-3 text-sm text-muted-foreground">The bootstrap superuser remains protected.</p>
            {/if}
          </div>
        {:else}
          <div class="omni-empty-state py-10">Choose a user from the directory to open the account editor.</div>
        {/if}
      {/if}

      {#if accessPage === "internal"}
        <div class="omni-panel border-0 shadow-none p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 class="text-lg font-semibold">Create Omni admin users</h3>
            </div>
            <Button size="sm" variant="outline" onclick={() => (accessPage = "home")} disabled={saving}>Back</Button>
          </div>
          <div class="omni-form-grid mt-5">
            <div class="omni-field">
              <label for="new-system-user-name">Name</label>
              <input id="new-system-user-name" class="omni-input" bind:value={internalUserForm.name} />
            </div>
            <div class="omni-field">
              <label for="new-system-user-email">Email</label>
              <input id="new-system-user-email" class="omni-input" type="email" bind:value={internalUserForm.email} />
            </div>
            <div class="omni-field">
              <label for="new-system-user-role">Role</label>
              <select id="new-system-user-role" class="omni-select" bind:value={internalUserForm.role}>
                {#each internalRoleOptions as roleOption}
                  <option value={roleOption.value}>{roleOption.label}</option>
                {/each}
              </select>
            </div>
            <div class="omni-field">
              <label for="new-system-user-password">Password</label>
              <input id="new-system-user-password" class="omni-input" type="password" minlength="8" bind:value={internalUserForm.password} placeholder="At least 8 characters" />
            </div>
          </div>
          <div class="mt-5 flex flex-wrap items-center gap-3">
            <Button size="sm" onclick={addInternalUser} disabled={saving || !internalUserForm.email || !internalUserForm.password || internalUserForm.password.length < 8}>
              {saving ? "Saving..." : "Create internal user"}
            </Button>
          </div>
        </div>
      {/if}

      {#if accessPage === "hub"}
        <div class="omni-panel border-0 shadow-none p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 class="text-lg font-semibold">Add hub user</h3>
            </div>
            <Button size="sm" variant="outline" onclick={() => (accessPage = "home")} disabled={saving}>Back</Button>
          </div>
          <div class="omni-form-grid mt-5">
            <div class="omni-field">
              <label for="new-user-name">Name</label>
              <input id="new-user-name" class="omni-input" bind:value={hubUserForm.name} />
            </div>
            <div class="omni-field">
              <label for="new-user-email">Email</label>
              <input id="new-user-email" class="omni-input" type="email" bind:value={hubUserForm.email} />
            </div>
            <div class="omni-field">
              <label for="new-user-role">Role</label>
              <select id="new-user-role" class="omni-select" bind:value={hubUserForm.role}>
                {#each hubRoleOptions as roleOption}
                  <option value={roleOption.value}>{roleOption.label}</option>
                {/each}
              </select>
            </div>
            <div class="omni-field">
              <label for="new-user-password">Password</label>
              <input id="new-user-password" class="omni-input" type="password" minlength="8" bind:value={hubUserForm.password} placeholder="At least 8 characters" />
            </div>
          </div>
          <div class="mt-5 flex flex-wrap items-center gap-3">
            <Button size="sm" onclick={addHubUser} disabled={saving || loading || !selectedHubId || !hubUserForm.email || !hubUserForm.password || hubUserForm.password.length < 8}>
              {saving ? "Saving..." : "Add hub user"}
            </Button>
          </div>
        </div>
      {/if}

      {#if accessPage === "matrix"}
        <div class="omni-panel border-0 shadow-none p-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 class="text-lg font-semibold">Permission matrix</h3>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <Button size="sm" variant="outline" onclick={() => (accessPage = "home")}>Back</Button>
            </div>
          </div>
          <div class="omni-table-shell mt-4 overflow-auto">
            <table class="omni-table min-w-[620px]">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>View hub data</th>
                  <th>Edit hub data</th>
                  <th>Manage users</th>
                  <th>Billing actions</th>
                </tr>
              </thead>
              <tbody>
                {#each permissions as item (item.role)}
                  <tr>
                    <td class="font-medium uppercase">{item.role}</td>
                    <td>{item.canView ? "Yes" : "No"}</td>
                    <td>{item.canEdit ? "Yes" : "No"}</td>
                    <td>{item.canManageUsers ? "Yes" : "No"}</td>
                    <td>{item.canBilling ? "Yes" : "No"}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}
    </div>
  </div>

  {#if feedback}
    <div class="omni-panel border-slate-200/70 bg-slate-50/85 px-4 py-3 text-sm shadow-none dark:border-white/10 dark:bg-slate-950/50">{feedback}</div>
  {/if}
</section>
