import { writable } from "svelte/store";

const initialState = {
  hubFocusId: null,
  deviceSearch: "",
  jobFocusId: null,
  issuedAt: 0,
};

function createWorkspaceNavStore() {
  const { subscribe, set, update } = writable(initialState);

  return {
    subscribe,
    reset() {
      set(initialState);
    },
    focusHub(hubId) {
      update((current) => ({
        ...current,
        hubFocusId: hubId ?? null,
        issuedAt: Date.now(),
      }));
    },
    focusDevice(deviceSearch) {
      update((current) => ({
        ...current,
        deviceSearch: deviceSearch?.trim?.() ?? "",
        issuedAt: Date.now(),
      }));
    },
    clearDeviceFocus() {
      update((current) => ({
        ...current,
        deviceSearch: "",
      }));
    },
    focusJob(jobId) {
      update((current) => ({
        ...current,
        jobFocusId: jobId ?? null,
        issuedAt: Date.now(),
      }));
    },
  };
}

export const workspaceNavStore = createWorkspaceNavStore();
