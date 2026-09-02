<script lang="ts">
  import { Ellipsis } from "lucide-svelte";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import { buttonVariants } from "$lib/components/ui/button/button.svelte";
  import { cn } from "$lib/utils.js";
  import type { Device } from "./columns";
  import DeviceDetailsModal from "./DeviceDetailsModal.svelte";

  export let device: Device;

  let showDetails = false;

  async function copyIMEI() {
    try {
      await navigator.clipboard.writeText(device.imei);
    } catch (error) {
      console.error("Unable to copy IMEI", error);
    }
  }

  function viewDetails() {
    showDetails = true;
  }

  function editDevice() {
    // Placeholder: parent component handles editing selection
    const ev = new CustomEvent("requestEdit", { detail: { deviceId: device.id } });
    dispatchEvent(ev);
  }

  const triggerClasses = cn(
    buttonVariants({ variant: "ghost", size: "icon" }),
    "relative h-8 w-8 p-0"
  );
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger class={triggerClasses} aria-label="Open device actions">
    <span class="sr-only">Open device actions</span>
    <Ellipsis class="size-4" />
  </DropdownMenu.Trigger>
  <DropdownMenu.Content>
    <DropdownMenu.Group>
      <DropdownMenu.Label>Actions</DropdownMenu.Label>
      <DropdownMenu.Item onclick={copyIMEI}>Copy IMEI</DropdownMenu.Item>
    </DropdownMenu.Group>
    <DropdownMenu.Separator />
    <DropdownMenu.Item onclick={viewDetails}>View details</DropdownMenu.Item>
    <DropdownMenu.Item onclick={editDevice}>Edit device</DropdownMenu.Item>
  </DropdownMenu.Content>
</DropdownMenu.Root>

