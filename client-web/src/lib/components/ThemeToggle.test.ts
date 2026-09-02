import { render, fireEvent, waitFor } from "@testing-library/svelte";
import ThemeToggle from "./ThemeToggle.svelte";
import { tick } from "svelte";

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string): MediaQueryList => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: () => void 0,
        removeEventListener: () => void 0,
        addListener: () => void 0,
        removeListener: () => void 0,
        dispatchEvent: () => false,
      }),
    });
  });

  it("toggles between light and dark themes", async () => {
    const { getByRole } = render(ThemeToggle);
    await tick();

    const button = getByRole("button", { name: /toggle color mode/i });
    expect(button.hasAttribute("disabled")).toBe(false);

    await fireEvent.click(button);

    await waitFor(() => {
      expect(localStorage.getItem("theme")).toBe("dark");
    });
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });
});
