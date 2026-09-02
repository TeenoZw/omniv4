<script>
  import { onDestroy, onMount } from "svelte";
  import { ModeWatcher, toggleMode } from "mode-watcher";
  import { Button } from "$lib/components/ui/button";
  import {
    Menu,
    X,
    LayoutDashboard,
    ClipboardList,
    CreditCard,
    Boxes,
    Shield,
    BarChart3,
    LogOut,
    Settings,
    Search,
    ChevronRight,
    ScrollText,
    Moon,
    Wrench,
  } from "lucide-svelte";

  import SessionExpiryWatcher from "$lib/components/SessionExpiryWatcher.svelte";
  import LoginShell from "$lib/components/LoginShell.svelte";
  import ProtectedSection from "$lib/components/ProtectedSection.svelte";
  import ConfirmDialog from "$lib/components/ConfirmDialog.svelte";
  import ToastStack from "$lib/components/ToastStack.svelte";
  import { logout as apiLogout } from "$lib/api/auth";
  import { fetchAdminActivity } from "$lib/api/activity";
  import { fetchComplianceOverview } from "$lib/api/compliance";
  import { fetchHubs } from "$lib/api/hubs";
  import { fetchDeviceInventory } from "$lib/api/devices";
  import { fetchTechnicianJobs } from "$lib/api/technician-jobs";
  import { sessionStore } from "$lib/stores/session";
  import { workspaceNavStore } from "$lib/stores/workspace-nav";

  const componentLoaders = {
    PivotDashboard: () => import("$lib/components/PivotDashboard.svelte"),
    EnquiryBoard: () => import("$lib/components/EnquiryBoard.svelte"),
    HubManagement: () => import("$lib/components/HubManagement.svelte"),
    BillingManagement: () => import("$lib/components/BillingManagement.svelte"),
    AssetRegistry: () => import("$lib/components/AssetRegistry.svelte"),
    SimInventory: () => import("$lib/components/SimInventory.svelte"),
    HardwareIntakeForm: () => import("$lib/components/HardwareIntakeForm.svelte"),
    DeviceInventoryNew: () => import("$lib/components/DeviceInventoryNew.svelte"),
    TechnicianWorkflowBoard: () => import("$lib/components/TechnicianWorkflowBoard.svelte"),
    HubAccessControl: () => import("$lib/components/HubAccessControl.svelte"),
    ComplianceOverviewBoard: () => import("$lib/components/ComplianceOverviewBoard.svelte"),
    DataSubjectRequestsBoard: () => import("$lib/components/DataSubjectRequestsBoard.svelte"),
    SecurityIncidentsBoard: () => import("$lib/components/SecurityIncidentsBoard.svelte"),
    InternalStatsPanel: () => import("$lib/components/InternalStatsPanel.svelte"),
    AuditTrailPage: () => import("$lib/components/AuditTrailPage.svelte"),
    TerminalLogPanel: () => import("$lib/components/TerminalLogPanel.svelte"),
  };

  const componentPromises = new Map();

  function loadComponent(name) {
    if (!componentPromises.has(name)) {
      componentPromises.set(name, componentLoaders[name]());
    }
    return componentPromises.get(name);
  }

  const workspaces = [
    {
      id: "operations",
      label: "Operations",
      icon: LayoutDashboard,
      roles: ["admin"],
      description: "Dashboard, enquiries, hubs, and billing.",
    },
    {
      id: "registry",
      label: "Registry",
      icon: Boxes,
      roles: ["admin"],
      description: "Assets, devices, SIMs, and intake.",
    },
    {
      id: "field",
      label: "Field",
      icon: Wrench,
      roles: ["admin", "technician"],
      description: "Jobs and controlled field corrections.",
    },
    {
      id: "governance",
      label: "Governance",
      icon: Shield,
      roles: ["admin"],
      description: "Users, permissions, and audit controls.",
    },
    {
      id: "intelligence",
      label: "Intelligence",
      icon: BarChart3,
      roles: ["admin"],
      description: "Live operational visibility.",
    },
  ];

  const modules = [
    {
      id: "dashboard",
      workspace: "operations",
      label: "Dashboard",
      icon: LayoutDashboard,
      roles: ["admin"],
    },
    {
      id: "enquiries",
      workspace: "operations",
      label: "Enquiries",
      icon: ClipboardList,
      roles: ["admin"],
    },
    {
      id: "hubs",
      workspace: "operations",
      label: "Hubs",
      icon: ClipboardList,
      roles: ["admin"],
    },
    {
      id: "billing",
      workspace: "operations",
      label: "Billing",
      icon: CreditCard,
      roles: ["admin"],
    },
    {
      id: "assets",
      workspace: "registry",
      label: "Assets",
      icon: Boxes,
      roles: ["admin"],
    },
    {
      id: "sims",
      workspace: "registry",
      label: "SIMs",
      icon: Boxes,
      roles: ["admin"],
    },
    {
      id: "inventory",
      workspace: "registry",
      label: "Devices",
      icon: Boxes,
      roles: ["admin"],
    },
    {
      id: "intake",
      workspace: "registry",
      label: "Device Intake",
      icon: Boxes,
      roles: ["admin"],
    },
    {
      id: "job-cards",
      workspace: "field",
      label: "Jobs",
      icon: Wrench,
      roles: ["admin", "technician"],
    },
    {
      id: "hardware-assignment",
      workspace: "field",
      label: "Device Assignment",
      icon: Wrench,
      roles: ["admin"],
    },
    {
      id: "compliance-overview",
      workspace: "governance",
      label: "Overview",
      icon: Shield,
      roles: ["admin"],
    },
    {
      id: "access",
      workspace: "governance",
      label: "Users & Permissions",
      icon: Shield,
      roles: ["admin"],
    },
    {
      id: "data-requests",
      workspace: "governance",
      label: "Data Requests",
      icon: Shield,
      roles: ["admin"],
    },
    {
      id: "security-incidents",
      workspace: "governance",
      label: "Security Incidents",
      icon: Shield,
      roles: ["admin"],
    },
    {
      id: "stats",
      workspace: "intelligence",
      label: "Live Statistics",
      icon: BarChart3,
      roles: ["admin"],
    },
    {
      id: "audit",
      workspace: "governance",
      label: "Audit Trail",
      icon: ScrollText,
      roles: ["admin"],
    },
  ];
  const QUICK_ROUTE_MODULE_ID = {
    "goto-dashboard": "dashboard",
    "goto-hubs": "hubs",
    "goto-enquiries": "enquiries",
    "goto-assets": "assets",
    "goto-sims": "sims",
    "goto-inventory": "inventory",
    "goto-intake": "intake",
    "goto-assignments": "hardware-assignment",
    "goto-job-cards": "job-cards",
    "goto-access": "access",
    "goto-data-requests": "data-requests",
    "goto-security-incidents": "security-incidents",
    "goto-audit": "audit",
  };

  let activeSection = "dashboard";
  let activeWorkspace = "operations";
  let loginVisible = false;
  let mobileNavOpen = false;
  let finderOpen = false;
  let finderQuery = "";
  let finderBusy = false;
  let finderError = "";
  let finderToken = 0;
  let finderHubResults = [];
  let finderDeviceResults = [];
  let finderDeviceStatus = "all";
  let finderDevicePage = 1;
  let finderDevicePerPage = 8;
  let finderDeviceTotal = 0;
  let finderHubPool = [];
  let finderDebounce = null;
  let themeIsDark = false;
  let themeObserver = null;
  let activityEntries = [];
  let activityLoading = false;
  let activityError = "";
  let activityPollHandle = null;
  let complianceSignals = null;
  let complianceSignalsError = "";
  let compliancePollHandle = null;
  let operationalSignals = {
    jobs: { assigned: 0, accepted: 0 },
    billing: { attention: 0, critical: 0 },
  };
  let operationalSignalsError = "";
  let operationalPollHandle = null;
  let navPulseState = {};
  const navPulseTimers = new Map();
  let previousComplianceSnapshot = null;
  let previousOperationalSnapshot = null;
  let previousAuthState = false;
  let dashboardViewPromise = null;
  let enquiryViewPromise = null;
  let hubManagementViewPromise = null;
  let billingViewPromise = null;
  let assetRegistryViewPromise = null;
  let simInventoryViewPromise = null;
  let intakeViewPromise = null;
  let inventoryViewPromise = null;
  let technicianViewPromise = null;
  let complianceOverviewViewPromise = null;
  let accessViewPromise = null;
  let dataRequestsViewPromise = null;
  let securityIncidentsViewPromise = null;
  let statsViewPromise = null;
  let auditViewPromise = null;
  let terminalLogViewPromise = null;

  $: session = $sessionStore;
  $: isAuthenticated = Boolean(session?.token);
  $: normalizedRoles = (session?.roles ?? []).map((role) => (role ?? "").toString().toLowerCase());
  $: hasInternalRole = normalizedRoles.includes("admin") || normalizedRoles.includes("technician");
  $: isOmniAdmin = normalizedRoles.includes("admin");
  $: isTechnicianUser = normalizedRoles.includes("technician") && !isOmniAdmin;
  $: availableHubContexts = session?.hubs ?? [];
  $: selectedHubContextValue = session?.currentHubId ?? "__all__";
  $: moduleAccess = modules.reduce((acc, module) => {
    const hasAccess = isAuthenticated && (isOmniAdmin || module.roles?.some((role) => normalizedRoles.includes(role)));
    acc[module.id] = hasAccess;
    return acc;
  }, {});
  $: accessibleModules = modules.filter((module) => moduleAccess[module.id]);
  $: workspaceAccess = workspaces.reduce((acc, workspace) => {
    const hasAccess =
      isAuthenticated &&
      accessibleModules.some((module) => module.workspace === workspace.id) &&
      (isOmniAdmin || workspace.roles?.some((role) => normalizedRoles.includes(role)));
    acc[workspace.id] = hasAccess;
    return acc;
  }, {});
  $: visibleWorkspaces = workspaces.filter((workspace) => workspaceAccess[workspace.id]);
  $: if (isAuthenticated && !isOmniAdmin && activeSection === "dashboard") {
    activeSection = "job-cards";
  }
  $: if (isAuthenticated && !hasInternalRole) {
    sessionStore.logout();
    loginVisible = true;
  }
  $: if (!accessibleModules.some((module) => module.id === activeSection)) {
    activeSection = accessibleModules[0]?.id ?? "dashboard";
  }
  $: if (!workspaceAccess[activeWorkspace]) {
    activeWorkspace = visibleWorkspaces[0]?.id ?? "operations";
  }
  $: workspaceTabs = accessibleModules.filter((module) => module.workspace === activeWorkspace);
  $: if (workspaceTabs.length > 0 && !workspaceTabs.some((module) => module.id === activeSection)) {
    activeSection = workspaceTabs[0].id;
  }
  $: activeModuleMeta = modules.find((module) => module.id === activeSection) ?? modules[0] ?? null;
  $: quickRoutes = [
    {
      id: "goto-dashboard",
      label: "Dashboard",
      hint: "Operational snapshot",
      action: () => {
        activeSection = "dashboard";
      },
    },
    {
      id: "goto-hubs",
      label: "Hub Management",
      hint: "Hubs and provisioning",
      action: () => {
        activeSection = "hubs";
      },
    },
    {
      id: "goto-enquiries",
      label: "Enquiries",
      hint: "Customer enquiries",
      action: () => {
        activeSection = "enquiries";
      },
    },
    {
      id: "goto-assets",
      label: "Asset Registry",
      hint: "Hub assets and detail records",
      action: () => {
        activeSection = "assets";
      },
    },
    {
      id: "goto-sims",
      label: "SIM Inventory",
      hint: "Managed SIM cards and roaming",
      action: () => {
        activeSection = "sims";
      },
    },
    {
      id: "goto-inventory",
      label: "Device Inventory",
      hint: "Hardware inventory",
      action: () => {
        activeSection = "inventory";
      },
    },
    {
      id: "goto-intake",
      label: "Device Intake",
      hint: "Stock intake",
      action: () => {
        activeSection = "intake";
      },
    },
    {
      id: "goto-assignments",
      label: "Device Assignment",
      hint: "Manual assignment controls",
      action: () => {
        activeSection = "hardware-assignment";
      },
    },
    {
      id: "goto-job-cards",
      label: "Jobs",
      hint: "Installations and job cards",
      action: () => {
        activeSection = "job-cards";
      },
    },
    {
      id: "goto-access",
      label: "Access Control",
      hint: "Users, roles, and access",
      action: () => {
        activeSection = "access";
      },
    },
    {
      id: "goto-data-requests",
      label: "Data Requests",
      hint: "Track subject access and correction requests",
      action: () => {
        activeSection = "data-requests";
      },
    },
    {
      id: "goto-security-incidents",
      label: "Security Incidents",
      hint: "Track compromises, breaches, and investigations",
      action: () => {
        activeSection = "security-incidents";
      },
    },
    {
      id: "goto-audit",
      label: "Audit Trail",
      hint: "Audit records and integrity checks",
      action: () => {
        activeSection = "audit";
      },
    },
  ];
  $: normalizedFinderQuery = finderQuery.trim().toLowerCase();
  $: allowedQuickRoutes = isOmniAdmin
    ? quickRoutes
    : quickRoutes.filter((route) => ["goto-job-cards"].includes(route.id));
  $: quickRouteAccess = quickRoutes.reduce((acc, route) => {
    const moduleId = QUICK_ROUTE_MODULE_ID[route.id];
    const moduleAllowed = moduleId ? Boolean(moduleAccess[moduleId]) : isAuthenticated;
    const featureAllowed = route.id === "goto-intake" ? isOmniAdmin : route.id === "goto-assignments" ? isOmniAdmin : true;
    acc[route.id] = moduleAllowed && featureAllowed;
    return acc;
  }, {});
  $: finderRouteResults = normalizedFinderQuery
    ? allowedQuickRoutes.filter((route) =>
        `${route.label} ${route.hint}`.toLowerCase().includes(normalizedFinderQuery),
      )
    : allowedQuickRoutes;
  $: if (!isAuthenticated && !loginVisible) {
    loginVisible = true;
  }
  $: dashboardViewPromise = activeSection === "dashboard" ? loadComponent("PivotDashboard") : null;
  $: enquiryViewPromise = activeSection === "enquiries" ? loadComponent("EnquiryBoard") : null;
  $: hubManagementViewPromise = activeSection === "hubs" ? loadComponent("HubManagement") : null;
  $: billingViewPromise = activeSection === "billing" ? loadComponent("BillingManagement") : null;
  $: assetRegistryViewPromise = activeSection === "assets" ? loadComponent("AssetRegistry") : null;
  $: simInventoryViewPromise = activeSection === "sims" ? loadComponent("SimInventory") : null;
  $: intakeViewPromise = activeSection === "intake" ? loadComponent("HardwareIntakeForm") : null;
  $: inventoryViewPromise =
    activeSection === "inventory" || activeSection === "hardware-assignment" ? loadComponent("DeviceInventoryNew") : null;
  $: technicianViewPromise = activeSection === "job-cards" ? loadComponent("TechnicianWorkflowBoard") : null;
  $: complianceOverviewViewPromise =
    activeSection === "compliance-overview" ? loadComponent("ComplianceOverviewBoard") : null;
  $: accessViewPromise = activeSection === "access" ? loadComponent("HubAccessControl") : null;
  $: dataRequestsViewPromise = activeSection === "data-requests" ? loadComponent("DataSubjectRequestsBoard") : null;
  $: securityIncidentsViewPromise =
    activeSection === "security-incidents" ? loadComponent("SecurityIncidentsBoard") : null;
  $: statsViewPromise = activeSection === "stats" ? loadComponent("InternalStatsPanel") : null;
  $: auditViewPromise = activeSection === "audit" ? loadComponent("AuditTrailPage") : null;
  $: terminalLogViewPromise = isAuthenticated && isOmniAdmin ? loadComponent("TerminalLogPanel") : null;

  function openLogin() {
    loginVisible = true;
  }

  function selectSection(sectionId) {
    if (!moduleAccess[sectionId]) {
      return;
    }
    activeSection = sectionId;
    activeWorkspace = modules.find((module) => module.id === sectionId)?.workspace ?? activeWorkspace;
    mobileNavOpen = false;
  }

  function selectWorkspace(workspaceId) {
    if (!workspaceAccess[workspaceId]) {
      return;
    }
    activeWorkspace = workspaceId;
    const nextSection = accessibleModules.find((module) => module.workspace === workspaceId)?.id;
    if (nextSection) {
      activeSection = nextSection;
    }
    mobileNavOpen = false;
  }

  function toggleThemeMode() {
    toggleMode();
  }

  function handleHubContextChange(event) {
    const value = event.currentTarget?.value ?? event.target?.value;
    sessionStore.selectHub(value === "__all__" ? null : value);
  }

  function syncThemeFlag() {
    themeIsDark = document.documentElement.classList.contains("dark");
  }

  function formatDate(value) {
    if (!value) return "—";
    const normalized = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }

  function formatTime(value) {
    if (!value) return "—";
    const normalized = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  }

  async function loadActivityFeed() {
    if (!isAuthenticated) {
      activityEntries = [];
      activityError = "";
      return;
    }
    try {
      activityLoading = true;
      activityError = "";
      activityEntries = await fetchAdminActivity(15);
    } catch (error) {
      console.error("Unable to load activity feed", error);
      activityError = "Unable to load the activity feed.";
    } finally {
      activityLoading = false;
    }
  }

  async function loadComplianceSignals() {
    if (!isAuthenticated || !isOmniAdmin) {
      complianceSignals = null;
      complianceSignalsError = "";
      previousComplianceSnapshot = null;
      return;
    }

    try {
      complianceSignalsError = "";
      const nextSignals = await fetchComplianceOverview();
      const nextSnapshot = {
        governance: Number(nextSignals?.requests?.overdue ?? 0) +
          Number(nextSignals?.incidents?.critical_open ?? 0) +
          Number(nextSignals?.incidents?.notification_required ?? 0),
        dataRequests: Number(nextSignals?.requests?.overdue ?? 0),
        securityIncidents:
          Number(nextSignals?.incidents?.critical_open ?? 0) +
          Number(nextSignals?.incidents?.notification_required ?? 0),
      };

      if (previousComplianceSnapshot) {
        if (nextSnapshot.governance > previousComplianceSnapshot.governance) {
          triggerNavPulse("workspace-governance");
          triggerNavPulse("compliance-overview");
        }
        if (nextSnapshot.dataRequests > previousComplianceSnapshot.dataRequests) {
          triggerNavPulse("data-requests");
        }
        if (nextSnapshot.securityIncidents > previousComplianceSnapshot.securityIncidents) {
          triggerNavPulse("security-incidents");
        }
      }

      complianceSignals = nextSignals;
      previousComplianceSnapshot = nextSnapshot;
    } catch (error) {
      console.error("Unable to load compliance navigation signals", error);
      complianceSignalsError = "Unable to load compliance signals.";
    }
  }

  function buildBillingSignals(hubs = []) {
    let attention = 0;
    let critical = 0;
    for (const hub of hubs) {
      const status = String(hub?.status ?? "").toLowerCase();
      const daysLeft = Number(hub?.subscriptionDaysLeft);
      const hasDaysValue = Number.isFinite(daysLeft);
      const isCritical =
        ["suspended", "inactive", "cancelled"].includes(status) || (hasDaysValue && daysLeft < 0);
      const isUrgent = !isCritical && hasDaysValue && daysLeft <= 7;
      const needsAttention =
        isCritical || isUrgent || ["provisioning", "pending"].includes(status) || (hasDaysValue && daysLeft <= 14);

      if (needsAttention) attention += 1;
      if (isCritical) critical += 1;
    }
    return { attention, critical };
  }

  function triggerNavPulse(key) {
    if (!key) return;
    navPulseState = { ...navPulseState, [key]: true };
    if (navPulseTimers.has(key)) {
      clearTimeout(navPulseTimers.get(key));
    }
    const timeout = setTimeout(() => {
      navPulseState = { ...navPulseState, [key]: false };
      navPulseTimers.delete(key);
    }, 6000);
    navPulseTimers.set(key, timeout);
  }

  function badgeMotionClass(key) {
    return navPulseState[key] ? "motion-safe:animate-pulse" : "";
  }

  async function loadOperationalSignals() {
    if (!isAuthenticated || !hasInternalRole) {
      operationalSignals = {
        jobs: { assigned: 0, accepted: 0 },
        billing: { attention: 0, critical: 0 },
      };
      operationalSignalsError = "";
      previousOperationalSnapshot = null;
      return;
    }

    try {
      operationalSignalsError = "";
      const [assignedJobs, acceptedJobs, hubs] = await Promise.all([
        moduleAccess["job-cards"] ? fetchTechnicianJobs({ status_group: "assigned", page: 1, limit: 1 }) : Promise.resolve(null),
        moduleAccess["job-cards"] ? fetchTechnicianJobs({ status_group: "accepted", page: 1, limit: 1 }) : Promise.resolve(null),
        isOmniAdmin && moduleAccess.billing ? fetchHubs() : Promise.resolve([]),
      ]);

      const nextSignals = {
        jobs: {
          assigned: Number(assignedJobs?.meta?.total ?? 0),
          accepted: Number(acceptedJobs?.meta?.total ?? 0),
        },
        billing: buildBillingSignals(hubs ?? []),
      };
      const nextSnapshot = {
        jobs: nextSignals.jobs.assigned + nextSignals.jobs.accepted,
        billing: nextSignals.billing.attention,
      };

      if (previousOperationalSnapshot) {
        if (nextSnapshot.jobs > previousOperationalSnapshot.jobs) {
          triggerNavPulse("workspace-field");
          triggerNavPulse("job-cards");
        }
        if (nextSnapshot.billing > previousOperationalSnapshot.billing) {
          triggerNavPulse("workspace-operations");
          triggerNavPulse("billing");
        }
      }

      operationalSignals = nextSignals;
      previousOperationalSnapshot = nextSnapshot;
    } catch (error) {
      console.error("Unable to load operational navigation signals", error);
      operationalSignalsError = "Unable to load navigation signals.";
    }
  }

  function clearFinderDebounce() {
    if (finderDebounce) {
      clearTimeout(finderDebounce);
      finderDebounce = null;
    }
  }

  async function loadHubPool() {
    if (!isAuthenticated || finderHubPool.length > 0) {
      return;
    }
    finderHubPool = await fetchHubs();
  }

  async function runFinderSearch() {
    clearFinderDebounce();
    if (!finderOpen) return;

    const query = finderQuery.trim().toLowerCase();
    const token = ++finderToken;
    finderError = "";

    try {
      finderBusy = true;
      await loadHubPool();

      if (token !== finderToken) return;

      finderHubResults = query
        ? finderHubPool
            .filter((hub) =>
              `${hub.name} ${hub.code} ${hub.city ?? ""} ${hub.country ?? ""}`
                .toLowerCase()
                .includes(query),
            )
            .slice(0, 8)
        : finderHubPool.slice(0, 8);

      if (query.length >= 2) {
        const deviceResult = await fetchDeviceInventory({
          search: query,
          status: finderDeviceStatus,
          page: finderDevicePage,
          limit: finderDevicePerPage,
        });
        if (token !== finderToken) return;
        finderDeviceResults = deviceResult?.items ?? [];
        finderDeviceTotal = Number(deviceResult?.meta?.total ?? finderDeviceResults.length);
      } else {
        finderDeviceResults = [];
        finderDeviceTotal = 0;
      }
    } catch (error) {
      console.error("Global finder failed", error);
      finderError = "Unable to complete the global search.";
      finderHubResults = [];
      finderDeviceResults = [];
      finderDeviceTotal = 0;
    } finally {
      if (token === finderToken) {
        finderBusy = false;
      }
    }
  }

  function openFinder() {
    if (!isAuthenticated) return;
    finderOpen = true;
    if (!finderQuery.trim()) {
      void runFinderSearch();
    }
  }

  function closeFinder() {
    finderOpen = false;
    finderQuery = "";
    finderBusy = false;
    finderError = "";
    finderHubResults = [];
    finderDeviceResults = [];
    finderDeviceTotal = 0;
    finderDevicePage = 1;
    finderDeviceStatus = "all";
    clearFinderDebounce();
  }

  function selectFinderRoute(route) {
    if (!quickRouteAccess[route.id]) {
      return;
    }
    route.action();
    closeFinder();
  }

  function selectFinderHub(hub) {
    activeSection = "hubs";
    workspaceNavStore.focusHub(hub.id);
    closeFinder();
  }

  function selectFinderDevice(device) {
    activeSection = "inventory";
    workspaceNavStore.focusDevice(device.imei ?? device.id);
    closeFinder();
  }

  function openInventoryForDevice(event) {
    const deviceSearch = event?.detail?.deviceSearch;
    if (!deviceSearch) return;
    activeSection = "inventory";
    workspaceNavStore.focusDevice(deviceSearch);
  }

  function handleFinderInput(event) {
    finderQuery = event.target.value;
    finderDevicePage = 1;
    clearFinderDebounce();
    finderDebounce = setTimeout(() => {
      void runFinderSearch();
    }, 220);
  }

  function handleFinderDeviceStatusChange(event) {
    finderDeviceStatus = event.target.value;
    finderDevicePage = 1;
    void runFinderSearch();
  }

  function goFinderDevicePage(direction) {
    const nextPage = finderDevicePage + direction;
    const maxPage = Math.max(1, Math.ceil(finderDeviceTotal / finderDevicePerPage));
    finderDevicePage = Math.min(maxPage, Math.max(1, nextPage));
    void runFinderSearch();
  }

  function handleKeydown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      if (finderOpen) {
        closeFinder();
      } else {
        openFinder();
      }
    }
    if (event.key === "Escape" && finderOpen) {
      event.preventDefault();
      closeFinder();
    }
  }

  function handleExternalNavigate(event) {
    const section = event?.detail?.section;
    if (typeof section === "string" && moduleAccess[section]) {
      selectSection(section);
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
    window.addEventListener("omni-admin-navigate", handleExternalNavigate);
    activityPollHandle = setInterval(() => {
      void loadActivityFeed();
    }, 10000);
    compliancePollHandle = setInterval(() => {
      void loadComplianceSignals();
    }, 30000);
    operationalPollHandle = setInterval(() => {
      void loadOperationalSignals();
    }, 30000);
    syncThemeFlag();
    themeObserver = new MutationObserver(() => syncThemeFlag());
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
    window.removeEventListener("omni-admin-navigate", handleExternalNavigate);
    clearFinderDebounce();
    if (activityPollHandle) {
      clearInterval(activityPollHandle);
      activityPollHandle = null;
    }
    if (compliancePollHandle) {
      clearInterval(compliancePollHandle);
      compliancePollHandle = null;
    }
    if (operationalPollHandle) {
      clearInterval(operationalPollHandle);
      operationalPollHandle = null;
    }
    for (const timer of navPulseTimers.values()) {
      clearTimeout(timer);
    }
    navPulseTimers.clear();
    if (themeObserver) {
      themeObserver.disconnect();
      themeObserver = null;
    }
  });

  $: {
    if (isAuthenticated && !previousAuthState) {
      activeSection = isOmniAdmin ? "dashboard" : "job-cards";
      activeWorkspace = isOmniAdmin ? "operations" : "field";
      void loadActivityFeed();
      void loadComplianceSignals();
      void loadOperationalSignals();
    }
    if (!isAuthenticated && previousAuthState) {
      activityEntries = [];
      activityError = "";
      complianceSignals = null;
      complianceSignalsError = "";
      operationalSignals = {
        jobs: { assigned: 0, accepted: 0 },
        billing: { attention: 0, critical: 0 },
      };
      operationalSignalsError = "";
    }
    previousAuthState = isAuthenticated;
  }

  function handleLoginSuccess() {
    loginVisible = false;
    activeSection = isOmniAdmin ? "dashboard" : "job-cards";
    activeWorkspace = isOmniAdmin ? "operations" : "field";
    void loadActivityFeed();
    void loadComplianceSignals();
    void loadOperationalSignals();
  }

  function handleLoginClose() {
    if (isAuthenticated) {
      loginVisible = false;
    }
  }

  async function handleLogout() {
    try {
      await apiLogout(session?.refreshToken ?? null);
    } catch (error) {
      console.warn("Logout failed, clearing local session", error);
    } finally {
      sessionStore.logout();
      loginVisible = true;
    }
  }

  const moduleDescriptions = {
    dashboard: "Monitor hub activity, devices, subscriptions, and connectivity from one calm command surface.",
    enquiries: "Review incoming enquiries and move commercial follow-up without mixing it into hub operations.",
    hubs: "Provision, inspect, and maintain hubs on a dedicated working page with clear operational detail.",
    assets: "Review asset records, drill into Asset 360 details, and keep field data clean.",
    sims: "Manage SIM inventory, roaming state, assignment history, and recall actions from a dedicated connectivity ledger.",
    inventory: "Inspect tracker inventory, edit hardware metadata, and keep stock deployment-ready.",
    intake: "Capture new hardware into inventory without competing tables or extra workflow noise.",
    billing: "Adjust subscription state, renewals, and billing days with a focused commercial workspace.",
    "job-cards": "Dispatch, accept, and complete technician job cards through a clean status-driven queue.",
    "hardware-assignment": "Run manual device assignment and override actions when field corrections are required.",
    access: "Manage users and permissions while keeping internal and client access clearly separated.",
    "data-requests": "Keep data subject requests in one governed register with ownership, due dates, and response records.",
    "security-incidents": "Track incident severity, notification decisions, containment, and evidence in one place.",
    stats: "Inspect real-time internal metrics for capacity, utilisation, and operational load.",
    audit: "Review immutable records of system activity and administrative changes.",
  };
  const workspaceLabels = workspaces.reduce((acc, workspace) => {
    acc[workspace.id] = workspace.label;
    return acc;
  }, {});
  const workspaceSectionCounts = modules.reduce((acc, module) => {
    acc[module.workspace] = (acc[module.workspace] ?? 0) + 1;
    return acc;
  }, {});

  $: governanceAttentionCount = isOmniAdmin
    ? Number(complianceSignals?.requests?.overdue ?? 0) +
      Number(complianceSignals?.incidents?.critical_open ?? 0) +
      Number(complianceSignals?.incidents?.notification_required ?? 0)
    : 0;
  $: jobAttentionCount = moduleAccess["job-cards"]
    ? Number(operationalSignals?.jobs?.assigned ?? 0) + Number(operationalSignals?.jobs?.accepted ?? 0)
    : 0;
  $: billingAttentionCount = isOmniAdmin ? Number(operationalSignals?.billing?.attention ?? 0) : 0;
  $: billingCriticalCount = isOmniAdmin ? Number(operationalSignals?.billing?.critical ?? 0) : 0;

  function governanceTabBadge(moduleId) {
    if (!isOmniAdmin || !complianceSignals) return null;
    if (moduleId === "compliance-overview") {
      return governanceAttentionCount > 0 ? { value: governanceAttentionCount, tone: "alert" } : null;
    }
    if (moduleId === "data-requests") {
      const count = Number(complianceSignals?.requests?.overdue ?? 0);
      return count > 0 ? { value: count, tone: "warning" } : null;
    }
    if (moduleId === "security-incidents") {
      const count =
        Number(complianceSignals?.incidents?.critical_open ?? 0) +
        Number(complianceSignals?.incidents?.notification_required ?? 0);
      return count > 0 ? { value: count, tone: "alert" } : null;
    }
    return null;
  }

  function jobsTabBadge(moduleId) {
    if (moduleId !== "job-cards" || !moduleAccess["job-cards"] || jobAttentionCount <= 0) return null;
    const assignedCount = Number(operationalSignals?.jobs?.assigned ?? 0);
    const acceptedCount = Number(operationalSignals?.jobs?.accepted ?? 0);
    if (assignedCount > 0) {
      return { value: assignedCount, tone: "alert" };
    }
    return { value: acceptedCount, tone: "warning" };
  }

  function billingTabBadge(moduleId) {
    if (moduleId !== "billing" || !isOmniAdmin || billingAttentionCount <= 0) return null;
    return { value: billingAttentionCount, tone: billingCriticalCount > 0 ? "alert" : "warning" };
  }

  function governanceWorkspaceBadge(workspaceId) {
    if (workspaceId !== "governance" || !isOmniAdmin) return null;
    if (governanceAttentionCount > 0) return { value: governanceAttentionCount, tone: "alert" };
    if (complianceSignals && !complianceSignalsError) return { value: "Clear", tone: "ok" };
    return null;
  }

  function fieldWorkspaceBadge(workspaceId) {
    if (workspaceId !== "field" || !moduleAccess["job-cards"] || jobAttentionCount <= 0) return null;
    const assignedCount = Number(operationalSignals?.jobs?.assigned ?? 0);
    const acceptedCount = Number(operationalSignals?.jobs?.accepted ?? 0);
    if (assignedCount > 0) {
      return { value: assignedCount, tone: "alert" };
    }
    return { value: acceptedCount, tone: "warning" };
  }

  function operationsWorkspaceBadge(workspaceId) {
    if (workspaceId !== "operations" || !isOmniAdmin || billingAttentionCount <= 0) return null;
    return { value: billingAttentionCount, tone: billingCriticalCount > 0 ? "alert" : "warning" };
  }

  function navBadgeForWorkspace(workspaceId) {
    return governanceWorkspaceBadge(workspaceId) ?? fieldWorkspaceBadge(workspaceId) ?? operationsWorkspaceBadge(workspaceId);
  }

  function navBadgeForModule(moduleId) {
    return governanceTabBadge(moduleId) ?? jobsTabBadge(moduleId) ?? billingTabBadge(moduleId);
  }

  function shortcutSectionForBadge(sourceId) {
    const overdueRequests = Number(complianceSignals?.requests?.overdue ?? 0);
    const incidentAttention =
      Number(complianceSignals?.incidents?.critical_open ?? 0) +
      Number(complianceSignals?.incidents?.notification_required ?? 0);

    if (sourceId === "workspace-governance" || sourceId === "compliance-overview") {
      if (overdueRequests > 0) return "data-requests";
      if (incidentAttention > 0) return "security-incidents";
      return "compliance-overview";
    }
    if (sourceId === "workspace-field" || sourceId === "job-cards") {
      return "job-cards";
    }
    if (sourceId === "workspace-operations" || sourceId === "billing") {
      return "billing";
    }
    if (sourceId === "data-requests") return "data-requests";
    if (sourceId === "security-incidents") return "security-incidents";
    return null;
  }

  function badgeTitle(sourceId) {
    const target = shortcutSectionForBadge(sourceId);
    if (target === "data-requests") return "Jump to overdue requests";
    if (target === "security-incidents") return "Jump to incidents that need attention";
    if (target === "job-cards") {
      return Number(operationalSignals?.jobs?.assigned ?? 0) > 0
        ? "Jump to newly assigned jobs"
        : "Jump to accepted jobs that are still in progress";
    }
    if (target === "billing") {
      return billingCriticalCount > 0
        ? "Jump to expired or inactive billing profiles"
        : "Jump to billing profiles that need attention soon";
    }
    return "Open governance overview";
  }

  function badgeClasses(tone) {
    if (tone === "alert") {
      return "border-red-300 bg-red-100 text-red-700 dark:border-red-400/30 dark:bg-red-500/10 dark:text-red-200";
    }
    if (tone === "warning") {
      return "border-amber-300 bg-amber-100 text-amber-700 dark:border-amber-400/30 dark:bg-amber-500/10 dark:text-amber-200";
    }
    return "border-emerald-300 bg-emerald-100 text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-500/10 dark:text-emerald-200";
  }

  function handleWorkspaceClick(workspaceId, event) {
    const badgeClicked = event?.target?.closest?.("[data-smart-badge='true']");
    if (badgeClicked) {
      const sourceId =
        workspaceId === "governance"
          ? "workspace-governance"
          : workspaceId === "field"
            ? "workspace-field"
            : workspaceId === "operations"
              ? "workspace-operations"
              : null;
      const target = shortcutSectionForBadge(sourceId);
      if (target) {
        selectSection(target);
        return;
      }
    }
    selectWorkspace(workspaceId);
  }

  function handleWorkspaceTabClick(moduleId, event) {
    const badgeClicked = event?.target?.closest?.("[data-smart-badge='true']");
    if (badgeClicked) {
      const target = shortcutSectionForBadge(moduleId);
      if (target) {
        selectSection(target);
        return;
      }
    }
    selectSection(moduleId);
  }
</script>

<ModeWatcher />
<SessionExpiryWatcher warningWindowMs={60000} />
<ConfirmDialog />
<ToastStack />

<div class="omni-shell-bg min-h-screen text-slate-900 dark:text-slate-100">
  <div class="pointer-events-none fixed inset-0 -z-10">
    <div class="omni-grid-overlay absolute inset-0 opacity-60"></div>
    <div class="absolute -left-24 top-0 h-80 w-80 rounded-full bg-cyan-400/15 blur-3xl"></div>
    <div class="absolute right-0 top-12 h-96 w-96 rounded-full bg-sky-500/15 blur-3xl"></div>
  </div>
  <header class="sticky top-0 z-40 border-b border-white/60 bg-white/80 backdrop-blur-2xl dark:border-white/10 dark:bg-slate-950/45">
    <div class="mx-auto flex min-h-16 max-w-[1600px] flex-wrap items-center gap-3 px-4 py-3 sm:px-6 sm:py-2">
      <div class="flex min-w-0 flex-1 items-center gap-3">
        <button
          type="button"
          class="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-300 bg-white lg:hidden dark:border-white/20 dark:bg-white/5"
          onclick={() => (mobileNavOpen = !mobileNavOpen)}
          aria-label="Toggle admin navigation"
        >
          {#if mobileNavOpen}
            <X class="h-5 w-5" />
          {:else}
            <Menu class="h-5 w-5" />
          {/if}
        </button>

        <div class="flex min-w-0 items-center gap-3">
          <img src="/brand/omni-logo-horizontal.svg" alt="Omni Industrial Solutions" class="h-9 w-auto shrink-0 object-contain sm:h-10" />
          <div class="min-w-0">
            <p class="truncate text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300/80">Omni Business Platform</p>
            <h1 class="truncate text-sm font-semibold text-slate-900 sm:text-base dark:text-white">Operations workspace</h1>
          </div>
        </div>
      </div>

      <div class="flex w-full flex-wrap items-center justify-end gap-2 sm:w-auto sm:flex-nowrap">
        {#if isAuthenticated}
          <div class="hidden items-center gap-2 rounded-full border border-white/70 bg-white/75 px-3 py-1.5 text-xs text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300 lg:inline-flex">
            <span class="h-2 w-2 rounded-full bg-emerald-400"></span>
            {isOmniAdmin ? "Platform admin" : isTechnicianUser ? "Technician" : "Restricted"}
          </div>
          {#if availableHubContexts.length > 0}
            <label class="hidden items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-700 dark:border-white/15 dark:bg-white/5 dark:text-white/80 md:inline-flex">
              <span class="uppercase tracking-[0.16em] text-slate-500 dark:text-slate-300/70">Hub</span>
              <select class="bg-transparent outline-none" value={selectedHubContextValue} onchange={handleHubContextChange}>
                {#if isOmniAdmin}
                  <option value="__all__">All</option>
                {/if}
                {#each availableHubContexts as hub (hub.id)}
                  <option value={hub.id}>{hub.name}</option>
                {/each}
              </select>
            </label>
          {/if}
        {/if}
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-700 transition hover:border-slate-400 hover:bg-slate-50 dark:border-white/20 dark:bg-white/5 dark:text-white/85 dark:hover:border-white/35 dark:hover:bg-white/10"
          onclick={toggleThemeMode}
          aria-label="Toggle theme"
        >
          <Moon class="h-3.5 w-3.5" />
          {themeIsDark ? "Light mode" : "Dark mode"}
        </button>
        {#if isAuthenticated}
          {#if isOmniAdmin}
            <button
              type="button"
              class="hidden items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-700 transition hover:border-slate-400 hover:bg-slate-50 dark:border-white/15 dark:bg-white/5 dark:text-white/80 dark:hover:border-white/30 dark:hover:bg-white/10 md:inline-flex"
              onclick={openFinder}
            >
              <Search class="h-3.5 w-3.5" />
              Search records
              <span class="rounded border border-white/20 px-1.5 py-0.5 text-[10px] uppercase tracking-wide">⌘K</span>
            </button>
          {/if}
          <div class="hidden rounded-full border border-cyan-400/40 bg-cyan-100 px-3 py-1 text-xs text-cyan-700 dark:border-cyan-400/30 dark:bg-cyan-400/10 dark:text-cyan-200 md:block">
            {session?.user?.email ?? "Authenticated"}
          </div>
          <Button variant="outline" size="sm" onclick={handleLogout}>
            <LogOut class="mr-1 h-4 w-4" />
            Sign out
          </Button>
        {:else}
          <Button size="sm" onclick={openLogin}>
            <Settings class="mr-1 h-4 w-4" />
            Sign in
          </Button>
        {/if}
      </div>
    </div>
  </header>

  <div class="mx-auto grid max-w-[1600px] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[292px_minmax(0,1fr)] lg:py-8">
    <aside class="hidden lg:block">
      <div class="omni-scroll-rail sticky top-24 max-h-[calc(100vh-7rem)] overflow-y-auto pr-1">
        <div class="omni-nav-shell p-4">
          <div class="mb-4">
            <p class="text-[11px] uppercase tracking-[0.28em] text-cyan-700 dark:text-cyan-300/80">Workspaces</p>
          </div>
          <div class="mt-4 space-y-2">
            {#each visibleWorkspaces as workspace (workspace.id)}
              <button
                type="button"
                class={`omni-nav-item ${
                  !workspaceAccess[workspace.id]
                    ? "omni-nav-item-disabled"
                    : activeWorkspace === workspace.id
                      ? "omni-nav-item-active"
                      : "omni-nav-item-idle"
                }`}
                onclick={(event) => handleWorkspaceClick(workspace.id, event)}
                disabled={!workspaceAccess[workspace.id]}
              >
                <div class="flex items-start gap-3">
                  <span class="mt-0.5 inline-flex h-9 w-9 items-center justify-center rounded-[1rem] border border-white/70 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
                    <svelte:component this={workspace.icon} class="h-4 w-4" />
                  </span>
                  <div class="min-w-0">
                    <div class="flex items-center gap-2">
                      <p class="text-sm font-semibold text-slate-900 dark:text-white">{workspace.label}</p>
                      <span class="rounded-full border border-border/70 bg-background/75 px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] text-slate-500 dark:text-slate-300">
                        {workspaceSectionCounts[workspace.id] ?? 0} sections
                      </span>
                      {#if navBadgeForWorkspace(workspace.id)}
                        <span
                          data-smart-badge="true"
                          title={badgeTitle(
                            workspace.id === "governance"
                              ? "workspace-governance"
                              : workspace.id === "field"
                                ? "workspace-field"
                                : workspace.id === "operations"
                                  ? "workspace-operations"
                                  : workspace.id,
                          )}
                          class={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] ${badgeClasses(navBadgeForWorkspace(workspace.id).tone)} ${badgeMotionClass(
                            workspace.id === "governance"
                              ? "workspace-governance"
                              : workspace.id === "field"
                                ? "workspace-field"
                                : workspace.id === "operations"
                                  ? "workspace-operations"
                                  : workspace.id,
                          )}`}
                        >
                          {navBadgeForWorkspace(workspace.id).value}
                        </span>
                      {/if}
                    </div>
                  </div>
                </div>
              </button>
            {/each}
          </div>
        </div>
      </div>
    </aside>

    {#if mobileNavOpen}
      <button
        type="button"
        class="fixed inset-0 z-30 bg-black/60 lg:hidden"
        aria-label="Close navigation overlay"
        onclick={() => (mobileNavOpen = false)}
      ></button>
      <aside class="fixed left-2 right-2 top-[4.5rem] z-40 h-[calc(100vh-5rem)] overflow-y-auto rounded-[1.6rem] border border-white/60 bg-white/92 p-4 shadow-2xl backdrop-blur-2xl dark:border-white/10 dark:bg-[#081325] lg:hidden">
        <div class="space-y-4">
          <div class="flex items-center justify-between gap-3 border-b border-white/60 pb-3 dark:border-white/10">
            <div class="min-w-0">
              <p class="truncate text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300/80">Omni Business Platform</p>
              <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">Operations workspace</p>
            </div>
            {#if isAuthenticated}
              <span class="rounded-full border border-white/70 bg-white/80 px-3 py-1 text-[11px] text-slate-500 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300">
                {isOmniAdmin ? "Platform admin" : "Technician"}
              </span>
            {/if}
          </div>
          {#if isAuthenticated && availableHubContexts.length > 0}
            <label class="flex flex-col gap-2 rounded-2xl border border-white/60 bg-white/80 px-3 py-3 text-sm text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-white/80">
              <span class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-300/70">Hub context</span>
              <select class="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white" value={selectedHubContextValue} onchange={handleHubContextChange}>
                {#if isOmniAdmin}
                  <option value="__all__">All</option>
                {/if}
                {#each availableHubContexts as hub (hub.id)}
                  <option value={hub.id}>{hub.name}</option>
                {/each}
              </select>
            </label>
          {/if}
          {#each visibleWorkspaces as workspace (workspace.id)}
            <button
              type="button"
              class={`omni-nav-item ${
                !workspaceAccess[workspace.id]
                  ? "omni-nav-item-disabled"
                  : activeWorkspace === workspace.id
                    ? "omni-nav-item-active"
                    : "omni-nav-item-idle"
              }`}
              onclick={(event) => handleWorkspaceClick(workspace.id, event)}
              disabled={!workspaceAccess[workspace.id]}
            >
              <div class="flex items-center gap-3">
                <svelte:component this={workspace.icon} class="h-4 w-4" />
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="block text-sm font-semibold text-slate-900 dark:text-white">{workspace.label}</span>
                    {#if navBadgeForWorkspace(workspace.id)}
                      <span
                        data-smart-badge="true"
                        title={badgeTitle(
                          workspace.id === "governance"
                            ? "workspace-governance"
                            : workspace.id === "field"
                              ? "workspace-field"
                              : workspace.id === "operations"
                                ? "workspace-operations"
                                : workspace.id,
                        )}
                        class={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] ${badgeClasses(navBadgeForWorkspace(workspace.id).tone)} ${badgeMotionClass(
                          workspace.id === "governance"
                            ? "workspace-governance"
                            : workspace.id === "field"
                              ? "workspace-field"
                              : workspace.id === "operations"
                                ? "workspace-operations"
                                : workspace.id,
                        )}`}
                      >
                        {navBadgeForWorkspace(workspace.id).value}
                      </span>
                    {/if}
                  </div>
                </div>
              </div>
            </button>
          {/each}
        </div>
      </aside>
    {/if}

    <main class="min-w-0 space-y-6">
      {#if workspaceTabs.length > 1}
        <section class="omni-panel px-4 py-3">
          <div class="omni-tab-rail">
            {#each workspaceTabs as module (module.id)}
              <button
                type="button"
                class={activeSection === module.id ? "omni-tab-button omni-tab-button-active" : "omni-tab-button omni-tab-button-idle"}
                data-state={activeSection === module.id ? "active" : "inactive"}
                onclick={(event) => handleWorkspaceTabClick(module.id, event)}
              >
                <span>{module.label}</span>
                {#if navBadgeForModule(module.id)}
                  <span
                    data-smart-badge="true"
                    title={badgeTitle(module.id)}
                    class={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] ${badgeClasses(navBadgeForModule(module.id).tone)} ${badgeMotionClass(
                      module.id,
                    )}`}
                  >
                    {navBadgeForModule(module.id).value}
                  </span>
                {/if}
              </button>
            {/each}
          </div>
        </section>
      {/if}

      {#if activeSection === "dashboard"}
        <ProtectedSection
          title="Session required"
          ctaLabel="Sign in to continue"
          on:requestLogin={openLogin}
        >
          {#await dashboardViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading dashboard workspace…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load the dashboard workspace.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "enquiries"}
        <ProtectedSection
          title="Enquiries"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await enquiryViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading enquiries…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load enquiries right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "hubs"}
        <ProtectedSection
          title="Hubs"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await hubManagementViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading hub management…</span></div>
          {:then module}
            <svelte:component
              this={module.default}
              on:gotoInventory={openInventoryForDevice}
            />
          {:catch}
            <div class="omni-inline-state">Unable to load hub management right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "billing"}
        <ProtectedSection
          title="Billing management"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await billingViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading billing management…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load billing management right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "assets"}
        <ProtectedSection
          title="Assets"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await assetRegistryViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading asset registry…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load the asset registry right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "sims"}
        <ProtectedSection
          title="SIM inventory"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await simInventoryViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading SIM inventory…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load SIM inventory right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "inventory"}
        <ProtectedSection
          title="Device inventory"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await inventoryViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading inventory…</span></div>
          {:then module}
            <svelte:component this={module.default} mode="inventory" />
          {:catch}
            <div class="omni-inline-state">Unable to load inventory right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "intake"}
        <ProtectedSection
          title="Device intake"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          <div class="omni-panel border-0 p-6 shadow-none">
            {#await intakeViewPromise}
              <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading hardware intake…</span></div>
            {:then module}
              <svelte:component this={module.default} />
            {:catch}
              <div class="omni-inline-state">Unable to load hardware intake right now.</div>
            {/await}
          </div>
        </ProtectedSection>
      {:else if activeSection === "job-cards"}
        <ProtectedSection
          title="Jobs"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await technicianViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading job cards…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load the job card workspace right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "hardware-assignment"}
        <ProtectedSection
          title="Device assignment"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await inventoryViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading device assignment…</span></div>
          {:then module}
            <svelte:component this={module.default} mode="assignment" />
          {:catch}
            <div class="omni-inline-state">Unable to load device assignment right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "compliance-overview"}
        <ProtectedSection
          title="Compliance overview"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await complianceOverviewViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading compliance overview…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load the compliance overview right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "access"}
        <ProtectedSection
          title="Access management"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await accessViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading access control…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load access control right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "data-requests"}
        <ProtectedSection
          title="Data subject requests"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await dataRequestsViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading data request register…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load the data request register right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "security-incidents"}
        <ProtectedSection
          title="Security incidents"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await securityIncidentsViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading security incidents…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load the security incident register right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "stats"}
        <ProtectedSection
          title="Internal analytics"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await statsViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading live statistics…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load live statistics right now.</div>
          {/await}
        </ProtectedSection>
      {:else if activeSection === "audit"}
        <ProtectedSection
          title="Audit records"
          ctaLabel="Authenticate"
          on:requestLogin={openLogin}
        >
          {#await auditViewPromise}
            <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading audit trail…</span></div>
          {:then module}
            <svelte:component this={module.default} />
          {:catch}
            <div class="omni-inline-state">Unable to load the audit trail right now.</div>
          {/await}
        </ProtectedSection>
      {/if}

      {#if isAuthenticated && isOmniAdmin}
        <section class="omni-panel p-4">
          <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300/70">Global Terminal</p>
            </div>
            <div class="flex items-center gap-2">
              <Button variant="outline" size="sm" onclick={loadActivityFeed} disabled={activityLoading}>
                {activityLoading ? "Refreshing…" : "Refresh"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onclick={() => selectSection("audit")}
                disabled={!moduleAccess.audit}
              >
                Open audit page
              </Button>
            </div>
          </div>

          {#if activityError}
            <p class="rounded-xl border border-red-300 bg-red-100 px-3 py-4 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
              {activityError}
            </p>
          {:else if activityEntries.length === 0}
            <p class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-4 text-sm text-slate-600 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/60">
              No activity has been recorded yet.
            </p>
          {:else}
            {#await terminalLogViewPromise}
              <div class="omni-loading-state"><span class="omni-loading-spinner" aria-hidden="true"></span><span>Loading live terminal feed…</span></div>
            {:then module}
              <svelte:component
                this={module.default}
                panelTitle="global-audit-tail"
                panelCountLabel="events"
                tone="cyan"
                maxHeight="14rem"
                entries={activityEntries}
                columns={[
                  { key: "date", label: "Date", render: (entry) => formatDate(String(entry.timestamp ?? "")) },
                  { key: "time", label: "Time", render: (entry) => formatTime(String(entry.timestamp ?? "")) },
                  { key: "module", label: "Module", render: (entry) => String(entry.module ?? "") },
                  { key: "change", label: "Change", render: (entry) => String(entry.change ?? "") },
                  { key: "details", label: "What changed", render: (entry) => String(entry.details ?? "") },
                  { key: "user_email", label: "Changed by (email)", render: (entry) => String(entry.user_email ?? entry.user ?? "") },
                ]}
              />
            {:catch}
              <div class="omni-inline-state">Unable to load the live terminal feed right now.</div>
            {/await}
          {/if}
        </section>
      {/if}
    </main>
  </div>
</div>

{#if finderOpen}
  <button
    type="button"
    class="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-[2px] dark:bg-black/70"
    aria-label="Close global search"
    onclick={closeFinder}
  ></button>
  <section class="fixed left-1/2 top-20 z-[60] w-[min(920px,92vw)] -translate-x-1/2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-white/15 dark:bg-[#08111f]">
    <div class="border-b border-slate-200 p-4 dark:border-white/10">
      <label class="flex items-center gap-3 rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 dark:border-white/15 dark:bg-white/5">
        <Search class="h-4 w-4 text-cyan-700 dark:text-cyan-200/80" />
        <input
          class="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-500 dark:text-white dark:placeholder:text-white/40"
          type="search"
          placeholder="Search modules, hubs, companies, or IMEI"
          value={finderQuery}
          oninput={handleFinderInput}
        />
      </label>
    </div>

    <div class="grid max-h-[65vh] gap-4 overflow-y-auto p-4 md:grid-cols-3">
      <div class="space-y-2 md:col-span-1">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-white/45">Navigation</p>
        {#if finderRouteResults.length === 0}
          <p class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/50">No matching route found.</p>
        {:else}
          {#each finderRouteResults.slice(0, 8) as route (route.id)}
            <button
              type="button"
              class={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                quickRouteAccess[route.id]
                  ? "border-slate-200 bg-slate-50 text-slate-800 hover:border-cyan-400/50 hover:bg-cyan-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-white dark:hover:border-cyan-300/40 dark:hover:bg-cyan-500/10"
                  : "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-500 opacity-65 dark:border-white/10 dark:bg-white/[0.02] dark:text-white/40"
              }`}
              onclick={() => selectFinderRoute(route)}
              disabled={!quickRouteAccess[route.id]}
            >
              <p class="font-medium">{route.label}</p>
              <p class="text-xs text-slate-500 dark:text-white/55">{route.hint}</p>
              {#if !quickRouteAccess[route.id]}
                <p class="text-[11px] text-slate-500 dark:text-white/45">Access restricted</p>
              {/if}
            </button>
          {/each}
        {/if}
      </div>

      <div class="space-y-2 md:col-span-1">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-white/45">Hubs</p>
        {#if finderHubResults.length === 0}
          <p class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/50">No matching hub found.</p>
        {:else}
          {#each finderHubResults as hub (hub.id)}
            <button
              type="button"
              class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm text-slate-800 transition hover:border-cyan-400/50 hover:bg-cyan-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-white dark:hover:border-cyan-300/40 dark:hover:bg-cyan-500/10"
              onclick={() => selectFinderHub(hub)}
            >
              <p class="font-medium">{hub.name}</p>
              <p class="text-xs text-slate-500 dark:text-white/55">{hub.code} · {hub.city || "N/A"} · {hub.tier}</p>
            </button>
          {/each}
        {/if}
      </div>

      <div class="space-y-2 md:col-span-1">
        <div class="flex items-center justify-between gap-2">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-white/45">Devices</p>
          <select
            class="rounded-md border border-slate-300 bg-slate-50 px-2 py-1 text-[11px] text-slate-700 outline-none dark:border-white/15 dark:bg-white/5 dark:text-white/80"
            value={finderDeviceStatus}
            onchange={handleFinderDeviceStatusChange}
          >
            <option value="all">All</option>
            <option value="in_stock">In stock</option>
            <option value="assigned">Deployed</option>
            <option value="maintenance">Maintenance</option>
            <option value="faulty">Faulty</option>
            <option value="retired">Retired</option>
          </select>
        </div>
        {#if finderQuery.trim().length < 2}
          <p class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/50">
            Type at least 2 characters to search by IMEI/serial.
          </p>
        {:else if finderDeviceResults.length === 0}
          <p class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/50">No matching device found.</p>
        {:else}
          {#each finderDeviceResults as device (device.id)}
            <button
              type="button"
              class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm text-slate-800 transition hover:border-cyan-400/50 hover:bg-cyan-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-white dark:hover:border-cyan-300/40 dark:hover:bg-cyan-500/10"
              onclick={() => selectFinderDevice(device)}
            >
              <p class="font-medium">{device.imei}</p>
              <p class="text-xs text-slate-500 dark:text-white/55">{device.model ?? "Tracker"} · {device.status}</p>
            </button>
          {/each}
          <div class="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-2 py-2 text-xs text-slate-600 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/60">
            <span>
              Page {finderDevicePage} of {Math.max(1, Math.ceil(finderDeviceTotal / finderDevicePerPage))}
            </span>
            <div class="flex items-center gap-1">
              <button
                type="button"
                class="rounded-md border border-slate-300 px-2 py-1 disabled:opacity-40 dark:border-white/15"
                onclick={() => goFinderDevicePage(-1)}
                disabled={finderDevicePage <= 1 || finderBusy}
              >
                Prev
              </button>
              <button
                type="button"
                class="rounded-md border border-slate-300 px-2 py-1 disabled:opacity-40 dark:border-white/15"
                onclick={() => goFinderDevicePage(1)}
                disabled={finderDevicePage >= Math.max(1, Math.ceil(finderDeviceTotal / finderDevicePerPage)) || finderBusy}
              >
                Next
              </button>
            </div>
          </div>
        {/if}
      </div>
    </div>

    {#if finderBusy || finderError}
      <div class="border-t border-slate-200 px-4 py-2 text-xs dark:border-white/10">
        {#if finderBusy}
          <span class="text-cyan-700 dark:text-cyan-200">Searching…</span>
        {:else if finderError}
          <span class="text-red-700 dark:text-red-200">{finderError}</span>
        {/if}
      </div>
    {/if}
  </section>
{/if}

{#if loginVisible}
  <LoginShell
    allowClose={isAuthenticated}
    on:success={handleLoginSuccess}
    on:close={handleLoginClose}
  />
{/if}
