<script>
  import { onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { sessionStore } from "$lib/stores/session";
  import { workspaceNavStore } from "$lib/stores/workspace-nav";
  import { decodeAssetVin, fetchHubs, fetchHubAssets, createHubAsset } from "$lib/api/hubs";
  import { assignDevice, fetchDeviceInventory, fetchSimInventory, recallDevice } from "$lib/api/devices";
  import {
    createTechnicianJob,
    fetchTechnicianJobs,
    fetchTechnicians,
    updateTechnicianJob,
  } from "$lib/api/technician-jobs";
  import { confirmAndRun } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  const assetTypeOptions = [
    "trailer",
    "truck",
    "bus",
    "sedan",
    "hatchback",
    "tractor",
    "excavator",
    "other",
  ];

  let session = null;
  let hubs = [];
  let technicianOptions = [];
  let hardwareOptions = [];
  let simOptions = [];
  let assignedHubDevices = [];
  let hubAssetOptions = [];
  let jobs = [];
  let selectedJobId = null;
  let selectedJobAssets = [];
  let bootstrappedForSession = "";
  let workspaceNavState = { jobFocusId: null, issuedAt: 0 };

  let loading = false;
  let saving = false;
  let assetsLoading = false;
  let vinDecoding = false;
  let vinDecodeFeedback = "";
  let feedback = "";
  let feedbackKind = "info";

  let page = 1;
  let perPage = 25;
  let total = 0;
  let search = "";
  let hubFilter = "";
  let assignedToMe = false;
  let activeTab = "accepted";

  let jobCounts = {
    assigned: 0,
    accepted: 0,
    completed: 0,
    declined: 0,
  };

  let createForm = {
    hubId: "",
    assignedTechnicianId: "",
    priority: "normal",
    scheduledFor: "",
    installationLocation: "",
    notes: "",
  };

  let assetForm = createAssetForm();
  let declineReason = "";
  let workflowWindow = "home";
  let moveForm = {
    deviceId: "",
    targetAssetId: "",
    reason: "",
  };
  let recallForm = {
    deviceId: "",
    status: "in_stock",
    reason: "",
  };

  function createAssetForm() {
    return {
      assetType: "truck",
      assetTypeOther: "",
      assetName: "",
      registration: "",
      make: "",
      model: "",
      year: "",
      color: "",
      vin: "",
      engineCapacity: "",
      co2Emissions: "",
      fuelType: "",
      notes: "",
      hardwareIds: [],
      hardwareSimMap: {},
    };
  }

  $: roles = (session?.roles ?? []).map((role) => `${role}`.toLowerCase());
  $: isAdmin = roles.includes("admin");
  $: isTechnician = roles.includes("technician") && !isAdmin;
  $: currentUserId = session?.user?.id ?? null;
  $: currentUserEmail = session?.user?.email ?? "";
  $: if (isTechnician) {
    assignedToMe = true;
  }
  $: selectedJob = jobs.find((job) => job.id === selectedJobId) ?? null;
  $: selectedJobHub = hubs.find((hub) => hub.id === selectedJob?.hubId) ?? null;
  $: selectedHardwareCount = assetForm.hardwareIds.length;
  $: availableHardwareOptions = hardwareOptions.filter((item) => item.status === "in_stock");
  $: availableSimOptions = simOptions.filter((item) => item.status === "in_stock");
  $: availableAssignedDevices = assignedHubDevices.filter((item) => item.assignment);
  $: selectedJobAssetCount = selectedJobAssets.length;
  $: canCreateJob = Boolean(createForm.hubId && createForm.assignedTechnicianId);
  $: canCaptureAssets = Boolean(
    isTechnician &&
      selectedJob &&
      ["assigned", "in_progress"].includes(selectedJob.status) &&
      canActOnJob(selectedJob),
  );
  $: sessionBootstrapKey = `${session?.token ?? ""}:${isAdmin ? "admin" : isTechnician ? "technician" : "unknown"}`;
  $: selectedMoveAsset = hubAssetOptions.find((asset) => asset.id === moveForm.targetAssetId) ?? null;
  $: draftHardwareOptions = availableHardwareOptions.filter((item) => assetForm.hardwareIds.includes(item.id));
  $: isBriefPage = Boolean(selectedJob);
  $: if (workspaceNavState.jobFocusId && workspaceNavState.jobFocusId !== selectedJobId && jobs.some((job) => job.id === workspaceNavState.jobFocusId)) {
    selectJob(workspaceNavState.jobFocusId);
  }

  function setFeedback(kind, message) {
    feedbackKind = kind;
    feedback = message;
  }

  function resetAssetForm() {
    assetForm = createAssetForm();
    vinDecodeFeedback = "";
  }

  function toIso(value) {
    if (!value) return undefined;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return undefined;
    return date.toISOString();
  }

  function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString();
  }

  function statusBadgeClass(status) {
    switch (status) {
      case "completed":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-200";
      case "in_progress":
        return "bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-200";
      case "assigned":
        return "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200";
      case "cancelled":
        return "bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-200";
      default:
        return "bg-slate-200 text-slate-700 dark:bg-slate-600/30 dark:text-slate-200";
    }
  }

  function trackingBadgeClass(trackingState) {
    return trackingState === "tracked"
      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-200"
      : "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200";
  }

  function hubLabel(hub) {
    return hub ? `${hub.name} (${hub.code})` : "—";
  }

  function jobStatusGroupForTab(tab) {
    switch (tab) {
      case "assigned":
        return "assigned";
      case "accepted":
        return "accepted";
      case "completed":
        return "closed";
      case "declined":
        return "declined";
      default:
        return "all";
    }
  }

  function canActOnJob(job) {
    return Boolean(isAdmin || (job?.assignedTechnicianId && job.assignedTechnicianId === currentUserId));
  }

  function canAccept(job) {
    return Boolean(job && job.status === "assigned" && !isAdmin && canActOnJob(job));
  }

  function canDecline(job) {
    return Boolean(job && job.status === "assigned" && !isAdmin && canActOnJob(job));
  }

  function canComplete(job) {
    return Boolean(job && ["assigned", "in_progress"].includes(job.status) && (isAdmin || canActOnJob(job)));
  }

  function shouldShowVehicleFields(assetType) {
    return ["truck", "bus", "sedan", "hatchback", "tractor"].includes((assetType || "").toLowerCase());
  }

  function applyDecodedVinToAssetForm(decoded) {
    if (!decoded) return;
    assetForm = {
      ...assetForm,
      vin: decoded.normalized_vin || assetForm.vin,
      make: decoded.make || assetForm.make,
      model: decoded.model || assetForm.model,
      year: decoded.year || assetForm.year,
      fuelType: decoded.fuel_type || assetForm.fuelType,
      engineCapacity: decoded.engine_capacity || assetForm.engineCapacity,
      assetType:
        assetForm.assetType && assetForm.assetType !== "other"
          ? assetForm.assetType
          : decoded.suggested_asset_type || assetForm.assetType,
    };
  }

  function hardwareLabel(hardware) {
    return [
      hardware.imei,
      hardware.manufacturer,
      hardware.model,
      hardware.hardwareType,
      hardware.sim?.iccid ? `SIM ${hardware.sim.iccid}` : null,
      hardware.sim?.roamingEnabled ? "Roaming" : null,
    ]
      .filter(Boolean)
      .join(" · ");
  }

  function toggleHardwareSelection(hardwareId) {
    const normalized = Number(hardwareId);
    if (!normalized) return;
    const nextSet = new Set(assetForm.hardwareIds);
    if (nextSet.has(normalized)) {
      nextSet.delete(normalized);
    } else {
      nextSet.add(normalized);
    }
    const nextMap = { ...(assetForm.hardwareSimMap ?? {}) };
    if (!nextSet.has(normalized)) {
      delete nextMap[normalized];
    }
    assetForm = { ...assetForm, hardwareIds: Array.from(nextSet), hardwareSimMap: nextMap };
  }

  function setHardwareSim(hardwareId, simId) {
    const normalizedHardwareId = Number(hardwareId);
    if (!normalizedHardwareId) return;
    const nextMap = { ...(assetForm.hardwareSimMap ?? {}) };
    if (simId) {
      nextMap[normalizedHardwareId] = Number(simId);
    } else {
      delete nextMap[normalizedHardwareId];
    }
    assetForm = { ...assetForm, hardwareSimMap: nextMap };
  }

  function availableSimsForHardware(hardwareId) {
    const selectedMap = assetForm.hardwareSimMap ?? {};
    const selectedElsewhere = new Set(
      Object.entries(selectedMap)
        .filter(([key, value]) => Number(key) !== Number(hardwareId) && value)
        .map(([, value]) => Number(value)),
    );
    return availableSimOptions.filter((sim) => !selectedElsewhere.has(Number(sim.id)));
  }

  async function loadHubs() {
    try {
      hubs = await fetchHubs({ limit: 200 });
      if (isAdmin && !createForm.hubId) {
        createForm = { ...createForm, hubId: hubs[0]?.id ?? "" };
      }
    } catch (error) {
      console.error("Failed to load hubs", error);
      setFeedback("error", "Unable to load hubs.");
    }
  }

  async function loadTechnicians() {
    if (!isAdmin) {
      technicianOptions = [];
      return;
    }
    try {
      technicianOptions = await fetchTechnicians();
      if (!createForm.assignedTechnicianId) {
        createForm = { ...createForm, assignedTechnicianId: technicianOptions[0]?.id ?? "" };
      }
    } catch (error) {
      console.error("Failed to load technicians", error);
      setFeedback("error", "Unable to load technicians.");
    }
  }

  async function loadHardwareInventory() {
    try {
      const result = await fetchDeviceInventory({ status: "in_stock", page: 1, limit: 200 });
      hardwareOptions = result?.items ?? [];
    } catch (error) {
      console.error("Failed to load hardware options", error);
      setFeedback("error", "Unable to load working hardware from inventory.");
    }
  }

  async function loadSimInventory() {
    try {
      const result = await fetchSimInventory({ status: "in_stock", page: 1, limit: 200 });
      simOptions = result?.items ?? [];
    } catch (error) {
      console.error("Failed to load SIM options", error);
      setFeedback("error", "Unable to load managed SIM inventory.");
    }
  }

  async function loadJobHardwareContext(hubId) {
    if (!hubId) {
      assignedHubDevices = [];
      hubAssetOptions = [];
      return;
    }
    try {
      const [inventoryResult, assetResult] = await Promise.all([
        fetchDeviceInventory({ page: 1, limit: 200, hubId }),
        fetchHubAssets(hubId, { page: 1, limit: 100 }),
      ]);
      assignedHubDevices = (inventoryResult?.items ?? []).filter((item) => item.assignment);
      hubAssetOptions = assetResult?.items ?? [];
    } catch (error) {
      console.error("Failed to load job hardware context", error);
      assignedHubDevices = [];
      hubAssetOptions = [];
      setFeedback("error", "Unable to load assigned hardware and assets for this job.");
    }
  }

  async function loadJobs(forceSelection = false) {
    loading = true;
    try {
      const params = {
        page,
        limit: perPage,
        status_group: jobStatusGroupForTab(activeTab),
      };
      if (search.trim()) params.search = search.trim();
      if (hubFilter) params.hub_id = hubFilter;
      if (assignedToMe) params.assigned_to_me = true;
      const result = await fetchTechnicianJobs(params);
      jobs = result.items ?? [];
      total = Number(result?.meta?.total ?? jobs.length);

      const nextSelected =
        selectedJobId && jobs.some((job) => job.id === selectedJobId) && !forceSelection ? selectedJobId : null;
      selectedJobId = nextSelected;
      if (nextSelected) {
        await loadSelectedJobAssets(nextSelected);
      } else {
        selectedJobAssets = [];
        resetAssetForm();
      }
    } catch (error) {
      console.error("Failed to load technician jobs", error);
      setFeedback("error", error?.response?.data?.detail ?? "Unable to load job cards.");
    } finally {
      loading = false;
    }
  }

  async function loadJobCounts() {
    try {
      const baseParams = { page: 1, limit: 1 };
      if (hubFilter) baseParams.hub_id = hubFilter;
      if (assignedToMe) baseParams.assigned_to_me = true;

      const [assigned, accepted, completed, declined] = await Promise.all([
        fetchTechnicianJobs({ ...baseParams, status_group: "assigned" }),
        fetchTechnicianJobs({ ...baseParams, status_group: "accepted" }),
        fetchTechnicianJobs({ ...baseParams, status_group: "closed" }),
        fetchTechnicianJobs({ ...baseParams, status_group: "declined" }),
      ]);

      jobCounts = {
        assigned: Number(assigned?.meta?.total ?? 0),
        accepted: Number(accepted?.meta?.total ?? 0),
        completed: Number(completed?.meta?.total ?? 0),
        declined: Number(declined?.meta?.total ?? 0),
      };
    } catch (error) {
      console.error("Failed to load technician job counts", error);
    }
  }

  async function loadSelectedJobAssets(jobId = selectedJobId) {
    if (!jobId) {
      selectedJobAssets = [];
      return;
    }
    const job = jobs.find((item) => item.id === jobId);
    if (!job?.hubId) {
      selectedJobAssets = [];
      assignedHubDevices = [];
      hubAssetOptions = [];
      return;
    }
    assetsLoading = true;
    try {
      const response = await fetchHubAssets(job.hubId, {
        page: 1,
        limit: 100,
        source_job_id: job.id,
      });
      selectedJobAssets = response.items ?? [];
      await loadJobHardwareContext(job.hubId);
    } catch (error) {
      console.error("Failed to load job assets", error);
      setFeedback("error", "Unable to load assets captured under this job card.");
      selectedJobAssets = [];
      assignedHubDevices = [];
      hubAssetOptions = [];
    } finally {
      assetsLoading = false;
    }
  }

  async function createJobCard() {
    if (!canCreateJob) {
      setFeedback("error", "Select both a hub and a technician before creating a job card.");
      return;
    }
    await confirmAndRun(
      {
        title: "Create job card",
        description: "Technician onboarding workflow",
        message: `Create a new onboarding job card for ${hubLabel(hubs.find((hub) => hub.id === createForm.hubId))}?`,
        confirmLabel: "Create job card",
      },
      async () => {
        saving = true;
        try {
          const created = await createTechnicianJob({
            hubId: createForm.hubId,
            assignedTechnicianId: createForm.assignedTechnicianId,
            priority: createForm.priority,
            scheduledFor: toIso(createForm.scheduledFor),
            installationLocation: createForm.installationLocation?.trim() || undefined,
            notes: createForm.notes?.trim() || undefined,
          });
          setFeedback("success", "Job card created successfully.");
          toastStore.push({ title: "Job card created", message: `Assigned to ${created.assignedTechnicianEmail || "technician"}.`, tone: "success" });
          createForm = {
            ...createForm,
            scheduledFor: "",
            installationLocation: "",
            notes: "",
          };
          activeTab = "assigned";
          page = 1;
          await Promise.all([loadJobs(true), loadJobCounts()]);
          selectedJobId = created.id;
          await loadSelectedJobAssets(created.id);
        } catch (error) {
          console.error("Failed to create job card", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to create the job card.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function acceptSelectedJob() {
    if (!selectedJob) return;
    await confirmAndRun(
      {
        title: "Accept job card",
        description: "Technician action",
        message: "Accept this job and start the onboarding workflow?",
        confirmLabel: "Accept job",
      },
      async () => {
        saving = true;
        try {
          await updateTechnicianJob(selectedJob.id, { status: "assigned" });
          setFeedback("success", "Job accepted. You can now capture assets and assign hardware.");
          toastStore.push({ title: "Job accepted", message: "Asset capture is now open for this job.", tone: "success" });
          activeTab = "accepted";
          await Promise.all([loadJobs(true), loadJobCounts()]);
        } catch (error) {
          console.error("Failed to accept job", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to accept the job card.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function declineSelectedJob() {
    if (!selectedJob) return;
    const reason = declineReason.trim();
    if (!reason) {
      setFeedback("error", "A decline reason is required.");
      return;
    }
    await confirmAndRun(
      {
        title: "Decline job card",
        description: "Technician action",
        message: "Declining this job will stop the onboarding workflow until an admin reviews it.",
        confirmLabel: "Decline job",
        tone: "destructive",
      },
      async () => {
        saving = true;
        try {
          await updateTechnicianJob(selectedJob.id, { status: "cancelled", declineReason: reason });
          setFeedback("success", "Job declined and reason recorded.");
          toastStore.push({ title: "Job declined", message: reason, tone: "success" });
          declineReason = "";
          activeTab = "declined";
          await Promise.all([loadJobs(true), loadJobCounts()]);
        } catch (error) {
          console.error("Failed to decline job", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to decline the job card.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function completeSelectedJob() {
    if (!selectedJob) return;
    await confirmAndRun(
      {
        title: "Complete job card",
        description: "Technician onboarding workflow",
        message: selectedJobAssetCount > 0
          ? "Complete this job card now?"
          : "Complete this job card without any captured assets?",
        confirmLabel: "Complete job",
      },
      async () => {
        saving = true;
        try {
          await updateTechnicianJob(selectedJob.id, { status: "completed", installedAt: new Date().toISOString() });
          setFeedback("success", "Job marked as completed.");
          toastStore.push({ title: "Job completed", message: `${selectedJobAssetCount} asset${selectedJobAssetCount === 1 ? "" : "s"} captured under this job.`, tone: "success" });
          activeTab = "completed";
          await Promise.all([loadJobs(true), loadJobCounts()]);
        } catch (error) {
          console.error("Failed to complete job", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to complete the job card.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function cancelSelectedJobAsAdmin() {
    if (!selectedJob || !isAdmin) return;
    await confirmAndRun(
      {
        title: "Cancel job card",
        description: "Administrative override",
        message: "Cancel this job card? The technician will no longer be able to continue working on it.",
        confirmLabel: "Cancel job",
        tone: "destructive",
      },
      async () => {
        saving = true;
        try {
          await updateTechnicianJob(selectedJob.id, { status: "cancelled", declineReason: declineReason.trim() || undefined });
          setFeedback("success", "Job cancelled.");
          toastStore.push({ title: "Job cancelled", message: "Administrative cancellation recorded.", tone: "success" });
          activeTab = "declined";
          await Promise.all([loadJobs(true), loadJobCounts()]);
        } catch (error) {
          console.error("Failed to cancel job", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to cancel the job card.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function createAssetAssignment() {
    if (!selectedJob) {
      setFeedback("error", "Select a job card first.");
      return;
    }
    if (!assetForm.assetType || !assetForm.assetName.trim()) {
      setFeedback("error", "Asset type and asset name are required.");
      return;
    }

    await confirmAndRun(
      {
        title: "Create asset and assignment",
        description: "Technician onboarding workflow",
        message: selectedHardwareCount > 0
          ? `Create this asset and assign ${selectedHardwareCount} hardware item${selectedHardwareCount === 1 ? "" : "s"}?`
          : "Create this asset without assigning hardware yet?",
        confirmLabel: "Save asset",
      },
      async () => {
        saving = true;
        try {
          await createHubAsset(selectedJob.hubId, {
            assetType: assetForm.assetType,
            assetTypeOther: assetForm.assetType === "other" ? assetForm.assetTypeOther?.trim() || undefined : undefined,
            assetName: assetForm.assetName.trim(),
            registration: assetForm.registration?.trim() || undefined,
            make: assetForm.make?.trim() || undefined,
            model: assetForm.model?.trim() || undefined,
            year: assetForm.year?.trim() || undefined,
            color: assetForm.color?.trim() || undefined,
            vin: assetForm.vin?.trim() || undefined,
            engineCapacity: assetForm.engineCapacity?.trim() || undefined,
            co2Emissions: assetForm.co2Emissions?.trim() || undefined,
            fuelType: assetForm.fuelType?.trim() || undefined,
            notes: assetForm.notes?.trim() || undefined,
            sourceJobId: selectedJob.id,
            hardwareIds: assetForm.hardwareIds,
            hardwareAssignments: assetForm.hardwareIds.map((hardwareId) => ({
              hardwareId,
              simId: assetForm.hardwareSimMap?.[hardwareId] || undefined,
            })),
          });
          setFeedback("success", "Asset saved and linked to the selected job card.");
          toastStore.push({
            title: "Asset captured",
            message: selectedHardwareCount > 0 ? "Hardware assigned successfully." : "Asset saved without hardware.",
            tone: "success",
          });
          resetAssetForm();
          await Promise.all([loadHardwareInventory(), loadSimInventory(), loadSelectedJobAssets(selectedJob.id), loadJobs(), loadJobCounts()]);
        } catch (error) {
          console.error("Failed to save asset", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to save the asset for this job.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function reassignSelectedHardware() {
    if (!selectedJob || !canCaptureAssets) {
      setFeedback("error", "Select an active technician job first.");
      return;
    }
    if (!moveForm.deviceId || !moveForm.targetAssetId) {
      setFeedback("error", "Select both the deployed hardware and the target asset.");
      return;
    }
    if (!moveForm.reason.trim()) {
      setFeedback("error", "A reassignment reason is required.");
      return;
    }
    if (!selectedMoveAsset) {
      setFeedback("error", "Target asset could not be resolved.");
      return;
    }

    await confirmAndRun(
      {
        title: "Reassign hardware",
        description: "Technician field action",
        message: "Move this hardware to the selected asset?",
        confirmLabel: "Reassign hardware",
      },
      async () => {
        saving = true;
        try {
          await assignDevice(moveForm.deviceId, {
            hubId: selectedJob.hubId,
            vehicleId: selectedMoveAsset.id,
            sourceJobId: selectedJob.id,
            assetType: selectedMoveAsset.assetType || "other",
            assetName: selectedMoveAsset.assetName || selectedMoveAsset.label || "Unnamed asset",
            vehicleMake: selectedMoveAsset.make || undefined,
            vehicleModel: selectedMoveAsset.model || undefined,
            vehicleYear: selectedMoveAsset.year || undefined,
            engineCapacity: selectedMoveAsset.engineCapacity || undefined,
            vin: selectedMoveAsset.vin || undefined,
            technician: currentUserEmail || undefined,
            assetRegistration: selectedMoveAsset.registration || undefined,
            reassignmentReason: moveForm.reason,
          });
          setFeedback("success", "Hardware reassigned successfully.");
          toastStore.push({ title: "Hardware reassigned", message: "The selected device was moved to the new asset.", tone: "success" });
          moveForm = { deviceId: "", targetAssetId: "", reason: "" };
          await Promise.all([loadSelectedJobAssets(selectedJob.id), loadHardwareInventory(), loadSimInventory(), loadJobs(), loadJobCounts()]);
        } catch (error) {
          console.error("Failed to reassign hardware", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to reassign this hardware.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function recallSelectedHardware() {
    if (!selectedJob || !canCaptureAssets) {
      setFeedback("error", "Select an active technician job first.");
      return;
    }
    if (!recallForm.deviceId) {
      setFeedback("error", "Select the deployed hardware to recall.");
      return;
    }
    if (!recallForm.reason.trim()) {
      setFeedback("error", "A recall reason is required.");
      return;
    }

    await confirmAndRun(
      {
        title: "Recall hardware",
        description: "Technician field action",
        message: `Return this hardware to inventory as ${recallForm.status.replaceAll("_", " ")}?`,
        confirmLabel: "Recall hardware",
        tone: recallForm.status === "in_stock" ? "default" : "destructive",
      },
      async () => {
        saving = true;
        try {
          await recallDevice(recallForm.deviceId, {
            status: recallForm.status,
            reason: recallForm.reason,
            sourceJobId: selectedJob.id,
          });
          setFeedback("success", "Hardware recalled into inventory.");
          toastStore.push({ title: "Hardware recalled", message: "The selected device was returned to inventory.", tone: "success" });
          recallForm = { deviceId: "", status: "in_stock", reason: "" };
          await Promise.all([loadSelectedJobAssets(selectedJob.id), loadHardwareInventory(), loadSimInventory(), loadJobs(), loadJobCounts()]);
        } catch (error) {
          console.error("Failed to recall hardware", error);
          setFeedback("error", error?.response?.data?.detail ?? "Unable to recall this hardware.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function decodeAssetVinInput() {
    if (!assetForm.vin?.trim()) {
      setFeedback("error", "Enter a VIN before requesting vehicle metadata.");
      return;
    }
    vinDecoding = true;
    vinDecodeFeedback = "";
    try {
      const response = await decodeAssetVin(assetForm.vin);
      applyDecodedVinToAssetForm(response?.decoded);
      vinDecodeFeedback = response?.warnings?.[0] ?? "VIN metadata loaded.";
      toastStore.push({ title: "VIN decoded", message: "Vehicle metadata applied to this asset form.", tone: "success" });
    } catch (error) {
      console.error("Failed to decode VIN", error);
      setFeedback("error", error?.response?.data?.detail ?? error?.message ?? "Unable to decode this VIN.");
    } finally {
      vinDecoding = false;
    }
  }

  function selectJob(jobId) {
    selectedJobId = jobId;
    workflowWindow = "home";
    declineReason = "";
    resetAssetForm();
    moveForm = { deviceId: "", targetAssetId: "", reason: "" };
    recallForm = { deviceId: "", status: "in_stock", reason: "" };
    void loadSelectedJobAssets(jobId);
  }

  function openJob(jobId) {
    workspaceNavStore.focusJob(jobId);
    selectJob(jobId);
  }

  function returnToQueue() {
    workflowWindow = "home";
    selectedJobId = null;
    selectedJobAssets = [];
    assignedHubDevices = [];
    hubAssetOptions = [];
    declineReason = "";
    resetAssetForm();
    moveForm = { deviceId: "", targetAssetId: "", reason: "" };
    recallForm = { deviceId: "", status: "in_stock", reason: "" };
    workspaceNavStore.focusJob(null);
  }

  function changeTab(tab) {
    activeTab = tab;
    workflowWindow = "home";
    page = 1;
    selectedJobId = null;
    selectedJobAssets = [];
    assignedHubDevices = [];
    hubAssetOptions = [];
    declineReason = "";
    moveForm = { deviceId: "", targetAssetId: "", reason: "" };
    recallForm = { deviceId: "", status: "in_stock", reason: "" };
    void Promise.all([loadJobs(true), loadJobCounts()]);
  }

  function handleSearchInput(event) {
    search = event.target.value;
  }

  function submitSearch(event) {
    event.preventDefault();
    page = 1;
    void Promise.all([loadJobs(true), loadJobCounts()]);
  }

  function nextPage() {
    const totalPages = Math.max(1, Math.ceil(total / perPage));
    if (page < totalPages) {
      page += 1;
      void Promise.all([loadJobs(true), loadJobCounts()]);
    }
  }

  function prevPage() {
    if (page > 1) {
      page -= 1;
      void Promise.all([loadJobs(true), loadJobCounts()]);
    }
  }

  onMount(() => {
    const unsubscribe = sessionStore.subscribe((value) => {
      session = value;
    });
    const unsubscribeNav = workspaceNavStore.subscribe((value) => {
      workspaceNavState = value;
    });
    return () => {
      unsubscribe();
      unsubscribeNav();
    };
  });

  $: if (session?.token && sessionBootstrapKey !== bootstrappedForSession) {
    bootstrappedForSession = sessionBootstrapKey;
    activeTab = isTechnician ? "accepted" : "assigned";
    workflowWindow = "home";
    void Promise.all([loadHubs(), loadTechnicians(), loadHardwareInventory(), loadSimInventory()]).then(() =>
      Promise.all([loadJobs(true), loadJobCounts()]),
    );
  }
</script>

<section class="space-y-6 marketing-reveal">
  {#if feedback}
    <div
      class={`rounded-lg border px-4 py-3 text-sm ${
        feedbackKind === "error"
          ? "border-red-300 bg-red-50 text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200"
          : "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
      }`}
    >
      {feedback}
    </div>
  {/if}

  {#if isAdmin}
    <div class="omni-panel p-5">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="omni-kicker">Dispatch</p>
          <h3 class="mt-2 text-xl font-semibold text-slate-950 dark:text-white">Create job card</h3>
        </div>
        <Button size="sm" variant="outline" onclick={loadHardwareInventory} disabled={saving}>Refresh inventory</Button>
      </div>

      <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <label class="text-sm">
          Hub
          <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={createForm.hubId}>
            <option value="">Choose a hub</option>
            {#each hubs as hub (hub.id)}
              <option value={hub.id}>{hub.name} ({hub.code})</option>
            {/each}
          </select>
        </label>
        <label class="text-sm">
          Technician
          <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={createForm.assignedTechnicianId}>
            <option value="">Choose a technician</option>
            {#each technicianOptions as tech (tech.id)}
              <option value={tech.id}>{tech.name} ({tech.email})</option>
            {/each}
          </select>
        </label>
        <label class="text-sm">
          Priority
          <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={createForm.priority}>
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </label>
        <label class="text-sm">
          Scheduled date and time
          <input type="datetime-local" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={createForm.scheduledFor} />
        </label>
        <label class="text-sm md:col-span-2 xl:col-span-4">
          Installation site
          <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={createForm.installationLocation} />
        </label>
      </div>

      <label class="mt-3 block text-sm">
        Notes
        <textarea rows="2" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={createForm.notes}></textarea>
      </label>

      <div class="mt-4 flex flex-wrap gap-2">
        <Button size="sm" onclick={createJobCard} disabled={saving || !canCreateJob}>
          {saving ? "Saving…" : "Create job card"}
        </Button>
      </div>
    </div>
  {/if}

    <div class="omni-panel p-5">
      {#if isTechnician}
      <div class="mb-5 rounded-[1.5rem] border border-white/60 bg-white/60 p-4 dark:border-white/10 dark:bg-slate-950/35">
        <p class="text-xs uppercase tracking-[0.24em] text-muted-foreground">Field queue</p>
        <div class="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div class="omni-stat-card p-3 shadow-none">
            <p class="text-xs uppercase tracking-wide text-muted-foreground">Assigned</p>
            <p class="mt-2 text-2xl font-semibold">{jobCounts.assigned}</p>
          </div>
          <div class="omni-stat-card p-3 shadow-none">
            <p class="text-xs uppercase tracking-wide text-muted-foreground">Accepted</p>
            <p class="mt-2 text-2xl font-semibold">{jobCounts.accepted}</p>
          </div>
          <div class="omni-stat-card p-3 shadow-none">
            <p class="text-xs uppercase tracking-wide text-muted-foreground">Completed</p>
            <p class="mt-2 text-2xl font-semibold">{jobCounts.completed}</p>
          </div>
          <div class="omni-stat-card p-3 shadow-none">
            <p class="text-xs uppercase tracking-wide text-muted-foreground">Declined</p>
            <p class="mt-2 text-2xl font-semibold">{jobCounts.declined}</p>
          </div>
        </div>
      </div>
    {/if}

      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="omni-kicker">Jobs</p>
          <h3 class="mt-2 text-lg font-semibold">Status-driven queue</h3>
        </div>
        <span class="omni-inline-stat">{total} job card{total === 1 ? "" : "s"}</span>
      </div>

      <div class="omni-tab-rail">
        {#each [
          { id: "assigned", label: "Assigned" },
          { id: "accepted", label: "Accepted" },
          { id: "completed", label: "Completed" },
          { id: "declined", label: "Declined" },
        ] as tab}
          <button
            type="button"
            data-state={activeTab === tab.id ? "active" : "inactive"}
            class={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
              activeTab === tab.id
                ? "bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-200"
                : "text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-white/[0.04]"
            }`}
            onclick={() => changeTab(tab.id)}
          >
            {tab.label}
          </button>
        {/each}
      </div>

      <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
      <form class="xl:col-span-2" onsubmit={submitSearch}>
        <label class="text-sm">
          Search
          <input
            class="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            type="search"
            placeholder="Search by hub, technician, job ID, or notes"
            value={search}
            oninput={handleSearchInput}
          />
        </label>
      </form>
      {#if isAdmin}
        <label class="text-sm">
          Hub
          <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={hubFilter}>
            <option value="">All hubs</option>
            {#each hubs as hub (hub.id)}
              <option value={hub.id}>{hub.name} ({hub.code})</option>
            {/each}
          </select>
        </label>
      {/if}
      <label class="text-sm flex items-end">
        <span class="inline-flex items-center gap-2">
          <input type="checkbox" bind:checked={assignedToMe} onchange={() => { page = 1; void loadJobs(true); }} />
          Show only my jobs
        </span>
      </label>
    </div>
  </div>

    {#if !selectedJob}
    <div class="omni-list-stage">
    <div class="omni-panel overflow-hidden p-0">
      <div class="flex items-center justify-between border-b border-white/60 px-4 py-3 dark:border-white/10">
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">Queue</p>
          <p class="text-sm font-medium text-slate-900 dark:text-white">Active job cards</p>
        </div>
      </div>
      <table class="omni-table">
        <thead>
          <tr>
            <th>Job</th>
            <th>Hub</th>
            <th>Technician</th>
            <th>Status</th>
            <th>Updated</th>
            <th class="text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {#if loading}
            <tr>
              <td class="px-3 omni-table-loading" colspan="6">
                <div class="omni-loading-state">
                  <span class="omni-loading-spinner" aria-hidden="true"></span>
                  <span>Loading job cards…</span>
                </div>
              </td>
            </tr>
          {:else if jobs.length === 0}
            <tr>
              <td class="px-3 py-4 text-muted-foreground" colspan="6">No job cards match the current filters.</td>
            </tr>
            {:else}
            {#each jobs as job (job.id)}
              <tr class={selectedJobId === job.id ? "omni-row-active" : ""}>
                <td>
                  <div class="font-mono text-xs">{String(job.id).slice(0, 8)}</div>
                  <div class="text-xs text-muted-foreground">{job.priority}</div>
                </td>
                <td>
                  <div class="font-medium">{job.hubName || "—"}</div>
                  <div class="text-xs text-muted-foreground">{job.hubCode || "—"}</div>
                </td>
                <td>
                  <div>{job.assignedTechnicianName || "Not assigned"}</div>
                  <div class="text-xs text-muted-foreground">{job.assignedTechnicianEmail || "—"}</div>
                </td>
                <td>
                  <span class={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(job.status)}`}>
                    {job.status.replaceAll("_", " ")}
                  </span>
                </td>
                <td class="text-xs text-muted-foreground">{formatDateTime(job.updatedAt)}</td>
                <td class="text-right">
                  <Button size="sm" variant="outline" onclick={() => openJob(job.id)}>
                    Open
                  </Button>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
      <div class="flex items-center justify-between border-t px-4 py-3 text-sm">
        <p>
          Showing {total === 0 ? 0 : (page - 1) * perPage + 1} - {Math.min(page * perPage, total)} of {total}
        </p>
        <div class="flex gap-2">
          <Button size="sm" variant="outline" onclick={prevPage} disabled={page <= 1 || loading}>Previous</Button>
          <Button size="sm" variant="outline" onclick={nextPage} disabled={page >= Math.max(1, Math.ceil(total / perPage)) || loading}>Next</Button>
        </div>
      </div>
    </div>
    </div>
    {:else}
    <div class="omni-panel p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="omni-kicker">Field page</p>
          <h3 class="mt-2 text-lg font-semibold">Active brief</h3>
          <p class="text-sm text-muted-foreground">Focused job context, acceptance actions, asset capture, device work, and SIM pairing.</p>
        </div>
        <div class="flex gap-2">
          <Button size="sm" variant="outline" onclick={returnToQueue}>Back to Jobs</Button>
        </div>
      </div>
    </div>
    {/if}

    {#if selectedJob}
    <div>
    <div class="omni-panel p-5">
      {#if selectedJob}
        <div class="space-y-5">
          <div class="space-y-2">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="omni-kicker">Active brief</p>
                <h3 class="mt-2 text-xl font-semibold">{selectedJob.hubName}</h3>
                <p class="text-sm text-muted-foreground">{selectedJob.hubCode} · {selectedJob.assignedTechnicianEmail || currentUserEmail || "Technician pending"}</p>
              </div>
              <span class={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(selectedJob.status)}`}>
                {selectedJob.status.replaceAll("_", " ")}
              </span>
            </div>
            <div class="grid gap-3 sm:grid-cols-2 text-sm">
              <div class="omni-stat-card p-3 shadow-none">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Scheduled</p>
                <p class="mt-1 font-medium">{formatDateTime(selectedJob.scheduledFor)}</p>
              </div>
              <div class="omni-stat-card p-3 shadow-none">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Installation site</p>
                <p class="mt-1 font-medium">{selectedJob.installationLocation || "—"}</p>
              </div>
            </div>
            {#if selectedJob.notes}
              <div class="rounded-[1.2rem] border border-white/70 bg-white/65 p-3 text-sm dark:border-white/10 dark:bg-white/[0.03]">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Job notes</p>
                <p class="mt-1">{selectedJob.notes}</p>
              </div>
            {/if}
          </div>

          {#if workflowWindow === "home"}
          <div class="omni-workspace-shell">
            <div class="omni-workspace-header">
              <div class="omni-workspace-copy">
                <p class="omni-kicker">Field workflows</p>
                <h4 class="omni-workspace-title">Active brief pages</h4>
                <p class="omni-workspace-note">Open one field page at a time instead of stacking every workflow into this brief.</p>
              </div>
            </div>
            <div class="mt-4 grid gap-3">
              <button type="button" class="omni-action-card text-left" onclick={() => (workflowWindow = "brief")}>
                <span class="omni-kicker">Job acceptance</span>
                <span class="mt-2 block text-base font-semibold text-foreground">Open job controls</span>
                <span class="mt-1 block text-sm text-muted-foreground">Review acceptance, completion, or decline actions on their own page.</span>
              </button>
              {#if canCaptureAssets}
                <button type="button" class="omni-action-card text-left" onclick={() => (workflowWindow = "capture")}>
                  <span class="omni-kicker">Asset capture</span>
                  <span class="mt-2 block text-base font-semibold text-foreground">Open asset capture</span>
                  <span class="mt-1 block text-sm text-muted-foreground">Keep the asset form separate from device and SIM pairing.</span>
                </button>
                <button type="button" class="omni-action-card text-left" onclick={() => (workflowWindow = "device")}>
                  <span class="omni-kicker">Device assignment</span>
                  <span class="mt-2 block text-base font-semibold text-foreground">Open device workflow</span>
                  <span class="mt-1 block text-sm text-muted-foreground">Handle in-stock and deployed device actions on a dedicated page.</span>
                </button>
                <button type="button" class="omni-action-card text-left" onclick={() => (workflowWindow = "sim")}>
                  <span class="omni-kicker">SIM assignment</span>
                  <span class="mt-2 block text-base font-semibold text-foreground">Open SIM workflow</span>
                  <span class="mt-1 block text-sm text-muted-foreground">Pair managed SIMs after device selection, not alongside every other step.</span>
                </button>
                <button type="button" class="omni-action-card text-left" onclick={() => (workflowWindow = "assets")}>
                  <span class="omni-kicker">Captured assets</span>
                  <span class="mt-2 block text-base font-semibold text-foreground">Open captured assets</span>
                  <span class="mt-1 block text-sm text-muted-foreground">Review saved assets on their own page.</span>
                </button>
              {/if}
            </div>
          </div>
          {/if}

          {#if workflowWindow === "brief"}
            <div class="space-y-4 rounded-[1.5rem] border border-white/60 bg-white/60 p-5 shadow-sm dark:border-white/10 dark:bg-slate-950/35">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <p class="omni-kicker">Job acceptance</p>
                <Button size="sm" variant="outline" onclick={() => (workflowWindow = "home")}>Back</Button>
              </div>
              <div class="flex flex-wrap gap-2">
                {#if canAccept(selectedJob)}
                  <Button size="sm" onclick={acceptSelectedJob} disabled={saving}>Accept job</Button>
                {/if}
                {#if canComplete(selectedJob)}
                  <Button size="sm" variant="outline" onclick={completeSelectedJob} disabled={saving}>Complete job</Button>
                {/if}
                {#if isAdmin && ["assigned", "in_progress"].includes(selectedJob.status)}
                  <Button size="sm" variant="destructive" onclick={cancelSelectedJobAsAdmin} disabled={saving}>Cancel job</Button>
                {/if}
              </div>

              {#if canDecline(selectedJob)}
                <div class="rounded-xl border border-amber-300/60 bg-amber-50/70 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
                  <p class="text-sm font-medium">Decline this job</p>
                  <p class="text-xs text-muted-foreground">A reason is required so admin can reschedule or correct the brief.</p>
                  <textarea class="mt-3 w-full rounded-md border px-3 py-2 text-sm" rows="3" bind:value={declineReason} placeholder="Why are you declining this job?"></textarea>
                  <div class="mt-3">
                    <Button size="sm" variant="destructive" onclick={declineSelectedJob} disabled={saving || !declineReason.trim()}>
                      Decline with reason
                    </Button>
                  </div>
                </div>
              {/if}

              {#if isAdmin}
                <div class="rounded-[1.3rem] border border-slate-200 bg-slate-50/80 p-4 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-200">
                  Asset capture, device assignment, and SIM pairing are technician-only actions. Admin can create, monitor, reassign, or cancel job cards, while the assigned technician completes field onboarding.
                </div>
              {/if}
            </div>
          {/if}

          {#if workflowWindow === "capture" && canCaptureAssets}
            <div class="rounded-[1.5rem] border border-white/60 bg-white/60 p-5 shadow-sm dark:border-white/10 dark:bg-slate-950/35">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="omni-kicker">Field capture</p>
                  <h4 class="mt-2 font-semibold text-slate-950 dark:text-white">Capture asset details</h4>
                  <p class="mt-1 text-xs text-muted-foreground">This window focuses only on the asset record. Device and SIM selections happen in their own windows.</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-muted-foreground">{selectedHardwareCount} devices linked to this draft</span>
                  <Button size="sm" variant="outline" onclick={() => (workflowWindow = "home")}>Back</Button>
                </div>
              </div>

              <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                <label class="text-sm">
                  Asset type
                  <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.assetType}>
                    {#each assetTypeOptions as assetType}
                      <option value={assetType}>{assetType}</option>
                    {/each}
                  </select>
                </label>
                <label class="text-sm">
                  Asset name
                  <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.assetName} />
                </label>
                {#if assetForm.assetType === "other"}
                  <label class="text-sm">
                    Specify asset type
                    <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.assetTypeOther} />
                  </label>
                {/if}
                <label class="text-sm">
                  Registration
                  <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.registration} disabled={vinDecoding || saving} />
                </label>
                <div class="text-sm">
                  <span>VIN</span>
                  <div class="mt-1 flex gap-2">
                    <input class="min-w-0 flex-1 rounded-md border px-3 py-2 text-sm" bind:value={assetForm.vin} disabled={vinDecoding || saving} />
                    <Button size="sm" variant="outline" onclick={decodeAssetVinInput} disabled={vinDecoding || saving || !assetForm.vin.trim()}>
                      {vinDecoding ? "Decoding..." : "Decode VIN"}
                    </Button>
                  </div>
                  {#if vinDecodeFeedback}
                    <p class="mt-1 text-xs text-muted-foreground">{vinDecodeFeedback}</p>
                  {/if}
                </div>
                <label class="text-sm">
                  Fuel type
                  <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.fuelType} disabled={vinDecoding || saving} />
                </label>
                {#if shouldShowVehicleFields(assetForm.assetType)}
                  <label class="text-sm">
                    Make
                    <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.make} disabled={vinDecoding || saving} />
                  </label>
                  <label class="text-sm">
                    Model
                    <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.model} disabled={vinDecoding || saving} />
                  </label>
                  <label class="text-sm">
                    Year
                    <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.year} disabled={vinDecoding || saving} />
                  </label>
                  <label class="text-sm">
                    Color
                    <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.color} disabled={vinDecoding || saving} />
                  </label>
                  <label class="text-sm">
                    Engine capacity
                    <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.engineCapacity} disabled={vinDecoding || saving} />
                  </label>
                  <label class="text-sm">
                    CO2 emissions
                    <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.co2Emissions} disabled={vinDecoding || saving} />
                  </label>
                {/if}
              </div>

              <label class="mt-3 block text-sm">
                Asset notes
                <textarea rows="2" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assetForm.notes}></textarea>
              </label>

              <div class="mt-4 flex flex-wrap gap-2">
                <Button size="sm" onclick={createAssetAssignment} disabled={saving || !assetForm.assetName.trim()}>
                  Save asset
                </Button>
                <Button size="sm" variant="outline" onclick={resetAssetForm} disabled={saving}>
                  Reset form
                </Button>
              </div>
            </div>
          {/if}

          {#if workflowWindow === "device" && canCaptureAssets}
            <div class="space-y-4 rounded-[1.5rem] border border-white/60 bg-white/60 p-5 shadow-sm dark:border-white/10 dark:bg-slate-950/35">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="omni-kicker">Device workflow</p>
                  <h4 class="mt-2 font-semibold text-slate-950 dark:text-white">Assign or move devices</h4>
                  <p class="mt-1 text-xs text-muted-foreground">Use this window to pick in-stock devices for the current asset draft or reassign or reclaim deployed devices in the job hub.</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-muted-foreground">{availableHardwareOptions.length} in stock · {availableAssignedDevices.length} deployed</span>
                  <Button size="sm" variant="outline" onclick={() => (workflowWindow = "home")}>Back</Button>
                </div>
              </div>

              <div class="rounded-[1.35rem] border border-white/60 bg-white/70 p-4 dark:border-white/10 dark:bg-slate-950/40">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-sm font-medium">Device selection for current asset</p>
                    <p class="text-xs text-muted-foreground">Select one or more in-stock devices to bind to the asset draft you are capturing.</p>
                  </div>
                  <span class="text-xs text-muted-foreground">{selectedHardwareCount} selected</span>
                </div>
                {#if availableHardwareOptions.length > 0}
                  <div class="mt-3 grid gap-2 md:grid-cols-2">
                    {#each availableHardwareOptions as hardware (hardware.id)}
                      <div class={`rounded-lg border px-3 py-3 text-sm ${assetForm.hardwareIds.includes(hardware.id) ? "border-primary bg-primary/5" : "border-border bg-card"}`}>
                        <label class="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={assetForm.hardwareIds.includes(hardware.id)}
                            onchange={() => toggleHardwareSelection(hardware.id)}
                          />
                          <span class="min-w-0 flex-1">
                            <span class="block font-medium">{hardwareLabel(hardware)}</span>
                            <span class="block text-xs text-muted-foreground">Serial {hardware.serialNumber || "—"}</span>
                          </span>
                        </label>
                      </div>
                    {/each}
                  </div>
                {:else}
                  <div class="omni-empty-state py-8">No working in-stock devices are currently available.</div>
                {/if}
              </div>

              <div class="grid gap-4 xl:grid-cols-2">
                <div class="rounded-[1.4rem] border border-white/60 bg-white/60 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <h4 class="font-semibold">Reassign deployed device</h4>
                      <p class="text-xs text-muted-foreground">Move a working device from one asset to another within this hub.</p>
                    </div>
                    <span class="text-xs text-muted-foreground">{availableAssignedDevices.length} deployed</span>
                  </div>
                  <div class="mt-4 grid gap-3">
                    <label class="text-sm">
                      Installed device
                      <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={moveForm.deviceId}>
                        <option value="">Select device</option>
                        {#each availableAssignedDevices as device (device.id)}
                          <option value={device.id}>
                            {hardwareLabel(device)} · {device.assignment?.assetRegistration ?? device.assignment?.assetLabel ?? "Unlabelled asset"}
                          </option>
                        {/each}
                      </select>
                    </label>
                    <label class="text-sm">
                      Target asset
                      <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={moveForm.targetAssetId}>
                        <option value="">Select asset</option>
                        {#each hubAssetOptions as asset (asset.id)}
                          <option value={asset.id}>
                            {asset.assetName || asset.label || "Unnamed asset"}{asset.registration ? ` · ${asset.registration}` : ""}
                          </option>
                        {/each}
                      </select>
                    </label>
                    <label class="text-sm">
                      Reassignment reason
                      <textarea class="mt-1 w-full rounded-md border px-3 py-2 text-sm" rows="2" bind:value={moveForm.reason}></textarea>
                    </label>
                  </div>
                  <div class="mt-4">
                    <Button size="sm" variant="outline" onclick={reassignSelectedHardware} disabled={saving || !moveForm.deviceId || !moveForm.targetAssetId}>
                      Reassign device
                    </Button>
                  </div>
                </div>

                <div class="rounded-[1.4rem] border border-white/60 bg-white/60 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <h4 class="font-semibold">Recall device</h4>
                      <p class="text-xs text-muted-foreground">Return a deployed device back into inventory and record why it was recalled.</p>
                    </div>
                  </div>
                  <div class="mt-4 grid gap-3">
                    <label class="text-sm">
                      Installed device
                      <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={recallForm.deviceId}>
                        <option value="">Select device</option>
                        {#each availableAssignedDevices as device (device.id)}
                          <option value={device.id}>
                            {hardwareLabel(device)} · {device.assignment?.assetRegistration ?? device.assignment?.assetLabel ?? "Unlabelled asset"}
                          </option>
                        {/each}
                      </select>
                    </label>
                    <label class="text-sm">
                      Return status
                      <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={recallForm.status}>
                        <option value="in_stock">In stock</option>
                        <option value="maintenance">Maintenance</option>
                        <option value="faulty">Faulty</option>
                        <option value="retired">Retired</option>
                      </select>
                    </label>
                    <label class="text-sm">
                      Recall reason
                      <textarea class="mt-1 w-full rounded-md border px-3 py-2 text-sm" rows="2" bind:value={recallForm.reason}></textarea>
                    </label>
                  </div>
                  <div class="mt-4">
                    <Button size="sm" variant="outline" onclick={recallSelectedHardware} disabled={saving || !recallForm.deviceId}>
                      Recall device
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          {/if}

          {#if workflowWindow === "sim" && canCaptureAssets}
            <div class="space-y-4 rounded-[1.5rem] border border-white/60 bg-white/60 p-5 shadow-sm dark:border-white/10 dark:bg-slate-950/35">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="omni-kicker">SIM workflow</p>
                  <h4 class="mt-2 font-semibold text-slate-950 dark:text-white">Pair managed SIMs to selected devices</h4>
                  <p class="mt-1 text-xs text-muted-foreground">This window only handles SIM selection for the devices already chosen in the device assignment window.</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-muted-foreground">{availableSimOptions.length} SIMs in stock</span>
                  <Button size="sm" variant="outline" onclick={() => (workflowWindow = "home")}>Back</Button>
                </div>
              </div>

              {#if draftHardwareOptions.length > 0}
                <div class="space-y-3">
                  {#each draftHardwareOptions as hardware (hardware.id)}
                    <div class="rounded-[1.15rem] border border-white/60 bg-white/70 p-4 dark:border-white/10 dark:bg-slate-950/40">
                      <div class="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p class="font-medium text-slate-950 dark:text-white">{hardwareLabel(hardware)}</p>
                          <p class="text-xs text-muted-foreground">Assign a managed SIM for this device before saving the asset.</p>
                        </div>
                        <span class="text-xs text-muted-foreground">Device #{hardware.id}</span>
                      </div>
                      <div class="mt-3">
                        <label class="text-sm">
                          Managed SIM
                          <select
                            class="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                            value={assetForm.hardwareSimMap?.[hardware.id] ?? ""}
                            onchange={(event) => setHardwareSim(hardware.id, event.currentTarget.value)}
                          >
                            <option value="">No SIM selected</option>
                            {#each availableSimsForHardware(hardware.id) as sim (sim.id)}
                              <option value={sim.id}>
                                {sim.iccid}{sim.msisdn ? ` · ${sim.msisdn}` : ""}{sim.roamingEnabled ? " · Roaming" : ""}
                              </option>
                            {/each}
                          </select>
                        </label>
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="omni-empty-state py-8">
                  Select one or more devices in the device assignment window to start pairing SIMs.
                </div>
              {/if}
            </div>
          {/if}

          {#if workflowWindow === "assets" || !canCaptureAssets}
          <div class="space-y-3">
            <div class="flex items-center justify-between gap-3">
              <div>
                <h4 class="font-semibold">Captured assets</h4>
                <p class="text-xs text-muted-foreground">Every asset saved in this workflow appears here with its assignment state.</p>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-muted-foreground">{selectedJobAssetCount} asset{selectedJobAssetCount === 1 ? "" : "s"}</span>
                {#if canCaptureAssets}
                  <Button size="sm" variant="outline" onclick={() => (workflowWindow = "home")}>Back</Button>
                {/if}
              </div>
            </div>

            {#if assetsLoading}
              <div class="omni-loading-state">
                <span class="omni-loading-spinner" aria-hidden="true"></span>
                <span>Loading captured assets…</span>
              </div>
            {:else if selectedJobAssets.length > 0}
              <div class="space-y-3 max-h-[26rem] overflow-auto pr-1">
                {#each selectedJobAssets as asset (asset.id)}
                  <div class="rounded-[1.3rem] border border-white/60 bg-white/60 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                    <div class="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p class="font-semibold">{asset.assetName || asset.label || "Unnamed asset"}</p>
                        <p class="text-sm text-muted-foreground">
                          {(asset.assetType || "asset").replaceAll("_", " ")}
                          {#if asset.assetTypeOther}
                            · {asset.assetTypeOther}
                          {/if}
                          {#if asset.registration}
                            · {asset.registration}
                          {/if}
                        </p>
                      </div>
                      <div class="flex flex-wrap gap-2">
                        <span class={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${trackingBadgeClass(asset.trackingState)}`}>
                          {asset.trackingState === "tracked" ? "Hardware assigned" : "No hardware assigned"}
                        </span>
                        <span class="inline-flex rounded-full bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-600/30 dark:text-slate-200">
                          {asset.assignedDeviceCount} device{asset.assignedDeviceCount === 1 ? "" : "s"}
                        </span>
                      </div>
                    </div>
                    <div class="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2 xl:grid-cols-3">
                      <p>VIN: <span class="font-medium text-foreground">{asset.vin || "—"}</span></p>
                      <p>Make / model: <span class="font-medium text-foreground">{[asset.make, asset.model].filter(Boolean).join(" ") || "—"}</span></p>
                      <p>Year: <span class="font-medium text-foreground">{asset.year || "—"}</span></p>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="omni-empty-state py-8">
                No assets have been captured under this job card yet.
              </div>
            {/if}
          </div>
          {/if}

        </div>
      {:else}
        <div class="omni-empty-state py-12">
          Select a job card to review its technician workflow.
        </div>
      {/if}
    </div>
    </div>
    {/if}
</section>
