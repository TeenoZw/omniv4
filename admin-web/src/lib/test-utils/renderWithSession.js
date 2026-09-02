import { get } from "svelte/store";
import { render } from "@testing-library/svelte/svelte5";
import { sessionStore } from "$lib/stores/session";

/**
 * Renders a component with session context primed for authenticated screens.
 * @param {import('svelte').ComponentType} Component
 * @param {object} [options]
 * @param {object} [options.session]
 * @param {object} [options.props]
 * @param {object} [options.renderOptions]
 */
export function renderWithSession(Component, options = {}) {
  const overrides = options.session ?? {};

  const session = {
    token: "test-token",
    refreshToken: "refresh-token",
    user: {
      id: "user-1",
      name: "QA Admin",
      email: "qa@omni.dev",
    },
    roles: ["admin"],
    hubs: [
      { id: "hub-1", name: "Dallas Core", role: "SuperUser", tier: "Individual" },
      { id: "hub-2", name: "NYC Ops", role: "Observer", tier: "Business" },
    ],
    currentHubId: "hub-1",
    ...overrides,
  };

  const hasExplicitHubId = Object.prototype.hasOwnProperty.call(overrides, "currentHubId");
  if (!hasExplicitHubId) {
    session.currentHubId = session.currentHubId ?? session.hubs[0]?.id ?? null;
  }
  session.currentHub = session.hubs.find((hub) => hub.id === session.currentHubId) ?? null;

  sessionStore.login(session);
  const result = render(Component, { props: options.props, ...options.renderOptions });
  return {
    ...result,
    session: get(sessionStore),
    resetSession() {
      sessionStore.logout();
    },
  };
}
