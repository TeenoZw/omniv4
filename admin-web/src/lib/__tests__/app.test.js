import { cleanup } from "@testing-library/svelte/svelte5";
import { vi } from "vitest";
import { renderWithSession } from "$lib/test-utils/renderWithSession";
import Passthrough from "$lib/components/Passthrough.svelte";
import App from "../../App.svelte";

function stubComponent() {
  return function StubComponent() {
    this.$destroy = () => {};
    this.$set = () => {};
  };
}

vi.mock("$lib/components/SessionExpiryWatcher.svelte", () => ({
  default: function SessionExpiryWatcherMock() {
    this.$destroy = () => {};
    this.$set = () => {};
  },
}));

vi.mock("mode-watcher", () => ({ ModeWatcher: stubComponent() }));
vi.mock("$lib/components/ui/button", () => ({ Button: stubComponent() }));
vi.mock("$lib/components/ui/separator", () => ({ Separator: stubComponent() }));
vi.mock("$lib/components/DeviceInventoryNew.svelte", () => ({ default: stubComponent() }));
vi.mock("$lib/components/HardwareIntakeForm.svelte", () => ({ default: stubComponent() }));
vi.mock("$lib/components/ChangeLogHistory.svelte", () => ({ default: stubComponent() }));
vi.mock("$lib/components/HubManagement.svelte", () => ({ default: stubComponent() }));
vi.mock("$lib/components/LoginShell.svelte", () => ({ default: stubComponent() }));
vi.mock("$lib/api/activity", () => ({
  fetchAdminActivity: vi.fn(async () => []),
}));
vi.mock("$lib/api/compliance", () => ({
  fetchComplianceOverview: vi.fn(async () => ({
    requests: { overdue: 0 },
    incidents: { critical_open: 0, notification_required: 0 },
  })),
}));
vi.mock("$lib/api/hubs", () => ({
  fetchHubs: vi.fn(async () => []),
}));
vi.mock("$lib/api/devices", () => ({
  fetchDeviceInventory: vi.fn(async () => ({ items: [], meta: { page: 1, perPage: 20, total: 0 } })),
}));
vi.mock("$lib/api/technician-jobs", () => ({
  fetchTechnicianJobs: vi.fn(async () => ({ items: [], meta: { page: 1, perPage: 1, total: 0 } })),
}));

vi.mock("$lib/components/ui/sidebar", () => {
  const passthrough = Passthrough;
  return {
    Sidebar: passthrough,
    SidebarHeader: passthrough,
    SidebarContent: passthrough,
    SidebarGroup: passthrough,
    SidebarGroupLabel: passthrough,
    SidebarGroupContent: passthrough,
    SidebarMenu: passthrough,
    SidebarMenuItem: passthrough,
    SidebarMenuButton: passthrough,
    SidebarMenuSkeleton: passthrough,
    SidebarFooter: passthrough,
    SidebarProvider: passthrough,
    Provider: passthrough,
    SidebarTrigger: passthrough,
    SidebarInset: passthrough,
    SidebarInput: passthrough,
    SidebarGroupAction: passthrough,
    SidebarMenuAction: passthrough,
    SidebarMenuBadge: passthrough,
    SidebarMenuButtonItem: passthrough,
    SidebarMenuSub: passthrough,
    SidebarMenuSubButton: passthrough,
    SidebarMenuSubItem: passthrough,
    SidebarSeparator: passthrough,
    SidebarRail: passthrough,
    SidebarMenuSkeletonItem: passthrough,
  };
});

describe("App", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the branded admin shell after authentication", () => {
    const { getAllByText, getByText, resetSession } = renderWithSession(App);
    expect(getAllByText(/Omni Business Platform/i).length).toBeGreaterThan(0);
    expect(getByText(/Operations workspace/i)).toBeInTheDocument();
    expect(getByText(/Workspaces/i)).toBeInTheDocument();
    resetSession();
  });

  it("shows technician workspace access instead of locking modules by plan", () => {
    const { getByText, queryByText, resetSession } = renderWithSession(App, {
      session: {
        roles: ["technician"],
        hubs: [{ id: "hub-basic", name: "Dallas Core", role: "Technician", tier: "Individual" }],
        currentHubId: "hub-basic",
      },
    });
    expect(getByText(/Technician/i)).toBeInTheDocument();
    expect(getByText(/Field/i)).toBeInTheDocument();
    expect(getByText(/Loading job cards/i)).toBeInTheDocument();
    expect(queryByText(/plan required/i)).not.toBeInTheDocument();
    resetSession();
  });

  it("does not render the hub selector overlay for admin workflows", () => {
    const { queryByText, resetSession } = renderWithSession(App, {
      session: {
        currentHubId: null,
        hubs: [],
      },
    });
    expect(queryByText(/Choose a Hub Context/i)).not.toBeInTheDocument();
    resetSession();
  });

  it("displays the Omni admin scope in the status bar", () => {
    const { getAllByText, getByText, resetSession } = renderWithSession(App, {
      session: {
        roles: ["admin"],
        hubs: [{ id: "hub-basic", name: "Dallas Core", role: "SuperUser", tier: "Individual" }],
        currentHubId: "hub-basic",
      },
    });
    expect(getAllByText(/Omni Business Platform/i).length).toBeGreaterThan(0);
    expect(getByText(/Platform admin/i)).toBeInTheDocument();
    resetSession();
  });
});
