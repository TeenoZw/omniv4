<script>
  import { createEventDispatcher } from "svelte";

  export let device = null;
  export let open = false;

  const dispatch = createEventDispatcher();

  function close() {
    dispatch("close");
  }
</script>

{#if open}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div class="w-full max-w-2xl rounded-lg bg-white p-6 text-black shadow-lg">
      <div class="flex items-start justify-between">
        <h3 class="text-lg font-semibold">Device details</h3>
        <button aria-label="Close" class="text-sm text-muted-foreground" on:click={close}>
          Close
        </button>
      </div>

      {#if device}
        <div class="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-xs text-muted-foreground">IMEI</p>
            <div class="font-medium">{device.imei}</div>
          </div>
          <div>
            <p class="text-xs text-muted-foreground">Serial</p>
            <div class="font-medium">{device.serialNumber ?? '—'}</div>
          </div>

          <div>
            <p class="text-xs text-muted-foreground">Manufacturer</p>
            <div class="font-medium">{device.manufacturer ?? '—'}</div>
          </div>
          <div>
            <p class="text-xs text-muted-foreground">Model</p>
            <div class="font-medium">{device.model ?? '—'}</div>
          </div>

          <div>
            <p class="text-xs text-muted-foreground">Firmware</p>
            <div class="font-medium">{device.firmwareVersion ?? '—'}</div>
          </div>
          <div>
            <p class="text-xs text-muted-foreground">Managed SIM</p>
            <div class="font-medium">{device.sim ? [device.sim.iccid, device.sim.msisdn, device.sim.carrier].filter(Boolean).join(" · ") : '—'}</div>
          </div>

          <div class="col-span-2">
            <p class="text-xs text-muted-foreground">Notes</p>
            <div class="text-sm">{device.notes ?? '—'}</div>
          </div>
        </div>
      {:else}
        <p class="mt-4 text-sm text-muted-foreground">No device data available.</p>
      {/if}

      <div class="mt-6 flex justify-end">
        <button class="rounded-md border px-3 py-1 text-sm" on:click={close}>Close</button>
      </div>
    </div>
  </div>
{/if}
