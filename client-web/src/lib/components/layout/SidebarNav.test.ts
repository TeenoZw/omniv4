import { render, screen } from "@testing-library/svelte";
import SidebarNav from "./SidebarNav.svelte";
import type { NavItem } from "./nav-items";
import {
  faGaugeSimpleHigh,
  faCreditCard,
  faHeadset,
} from "@fortawesome/free-solid-svg-icons";

const storeHelpers = vi.hoisted(() => {
  let currentPath = "/app";
  const subscribers = new Set<(value: { url: URL }) => void>();

  const pageStore = {
    subscribe(run: (value: { url: URL }) => void) {
      run({ url: new URL(`https://example.test${currentPath}`) });
      subscribers.add(run);
      return () => subscribers.delete(run);
    },
  };

  const setPath = (next: string) => {
    currentPath = next;
    const snapshot = { url: new URL(`https://example.test${currentPath}`) };
    subscribers.forEach((run) => run(snapshot));
  };

  return { pageStore, setPath };
});

vi.mock("$app/stores", () => ({
  page: storeHelpers.pageStore,
}));

const { setPath } = storeHelpers;

const navItems: NavItem[] = [
  { title: "Dashboard", href: "/app", icon: faGaugeSimpleHigh },
  { title: "Billing", href: "/app/billing", icon: faCreditCard },
  { title: "Support", href: "/app/support", icon: faHeadset },
];

describe("SidebarNav", () => {
  beforeEach(() => {
    setPath("/app");
  });

  it("renders labels and links", () => {
    render(SidebarNav, { props: { items: navItems, label: "Fleet" } });

    expect(screen.getByText("Fleet")).toBeTruthy();
    navItems.forEach((item) => {
      expect(screen.getByRole("link", { name: item.title })).toBeTruthy();
    });
  });

  it("applies active styles when the current path matches", () => {
    setPath("/app");
    render(SidebarNav, { props: { items: navItems } });

    const activeLink = screen.getByRole("link", { name: "Dashboard" });
    const inactiveLink = screen.getByRole("link", { name: "Billing" });

    expect(activeLink.className).toContain("omni-nav-link-active");
    expect(inactiveLink.className).toContain("omni-nav-link-idle");
  });

  it("keeps section active for nested paths", () => {
    setPath("/app/billing/invoices");
    render(SidebarNav, { props: { items: navItems } });

    const billingLink = screen.getByRole("link", { name: "Billing" });
    expect(billingLink.className).toContain("omni-nav-link-active");
  });
});
