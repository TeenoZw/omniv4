import type { ColumnDef } from "@tanstack/table-core";
import { renderComponent, renderSnippet } from "$lib/components/ui/data-table/index.js";
import { createRawSnippet } from "svelte";
import DeviceStatusCell from "./device-status-cell.svelte";

export type Device = {
  id: string;
  imei: string;
  serialNumber?: string | null;
  hardwareType?: string | null;
  model?: string | null;
  manufacturer?: string | null;
  firmwareVersion?: string | null;
  status: string;
  notes?: string | null;
  purchaseDate?: string | null;
  sim?: {
    id?: number | null;
    iccid?: string | null;
    msisdn?: string | null;
    carrier?: string | null;
    roamingEnabled?: boolean | null;
    status?: string | null;
  } | null;
  assignment?: {
    target?: string | null;
    hubId?: string | null;
    hubName?: string | null;
    vehicleId?: string | null;
    vehiclePlate?: string | null;
    technician?: string | null;
    assignedAt?: string | null;
    installedAt?: string | null;
    installationLocation?: string | null;
    installationLatitude?: number | null;
    installationLongitude?: number | null;
    assetLabel?: string | null;
    assetRegistration?: string | null;
    notes?: string | null;
    simId?: number | null;
    simIccid?: string | null;
    simMsisdn?: string | null;
    simCarrier?: string | null;
    simRoamingEnabled?: boolean | null;
  } | null;
  assignmentHistory?: Array<{
    id?: number | null;
    target?: string | null;
    hubId?: string | null;
    hubName?: string | null;
    vehicleId?: string | null;
    vehiclePlate?: string | null;
    technician?: string | null;
    assignedAt?: string | null;
    installedAt?: string | null;
    unassignedAt?: string | null;
    installationLocation?: string | null;
    installationLatitude?: number | null;
    installationLongitude?: number | null;
    assetLabel?: string | null;
    assetRegistration?: string | null;
    notes?: string | null;
    isActive?: boolean;
    simId?: number | null;
    simIccid?: string | null;
    simMsisdn?: string | null;
    simCarrier?: string | null;
    simRoamingEnabled?: boolean | null;
  }> | null;
};

export const columns: ColumnDef<Device>[] = [
  {
    accessorKey: "imei",
    header: "IMEI",
    cell: ({ row }) => {
      const imeiSnippet = createRawSnippet<[{ imei: string; serial?: string | null }]>(
        (getData) => {
          const { imei, serial } = getData();
          return {
            render: () =>
              `<div class="font-medium">${imei}</div>
               ${serial ? `<div class="text-xs text-muted-foreground">SN: ${serial}</div>` : ""}`,
          };
        }
      );
      return renderSnippet(imeiSnippet, {
        imei: row.original.imei,
        serial: row.original.serialNumber ?? undefined,
      });
    },
  },
  {
    accessorKey: "manufacturer",
    header: "Hardware",
    cell: ({ row }) => {
      const hardwareSnippet = createRawSnippet<[
        { manufacturer?: string | null; model?: string | null; hardwareType?: string | null }
      ]>((getData) => {
        const { manufacturer, model, hardwareType } = getData();
        const details = [model, hardwareType].filter(Boolean).join(" • ") || "Unknown";
        return {
          render: () =>
            `<div>${details}</div>
             ${manufacturer ? `<div class="text-xs text-muted-foreground">${manufacturer}</div>` : ""}`,
        };
      });
      return renderSnippet(hardwareSnippet, {
        manufacturer: row.original.manufacturer,
        model: row.original.model,
        hardwareType: row.original.hardwareType,
      });
    },
  },
  {
    accessorKey: "firmwareVersion",
    header: "Firmware",
    cell: ({ row }) => {
      const firmwareSnippet = createRawSnippet<[{ firmware?: string | null }]>(
        (getData) => {
          const { firmware } = getData();
          const label = firmware ?? "—";
          return {
            render: () => `<div>${label}</div>`,
          };
        }
      );
      return renderSnippet(firmwareSnippet, {
        firmware: row.original.firmwareVersion,
      });
    },
  },
  {
    accessorKey: "purchaseDate",
    header: "Purchased",
    cell: ({ row }) => {
      const purchaseSnippet = createRawSnippet<[{ purchaseDate?: string | null }]>(
        (getData) => {
          const { purchaseDate } = getData();
          if (!purchaseDate) {
            return { render: () => `<div class="text-muted-foreground">—</div>` };
          }
          const date = new Date(purchaseDate);
          const formatted = isNaN(date.getTime()) ? purchaseDate : date.toLocaleDateString();
          return {
            render: () => `<div>${formatted}</div>`,
          };
        }
      );
      return renderSnippet(purchaseSnippet, {
        purchaseDate: row.original.purchaseDate,
      });
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      return renderComponent(DeviceStatusCell, {
        status: row.original.status,
      });
    },
  },
  {
    accessorKey: "notes",
    header: "Notes",
    cell: ({ row }) => {
      const notesSnippet = createRawSnippet<[{ notes?: string | null }]>(
        (getData) => {
          const { notes } = getData();
          if (!notes) {
            return { render: () => `<div class="text-muted-foreground">—</div>` };
          }
          const truncated = notes.length > 80 ? `${notes.slice(0, 77)}…` : notes;
          return {
            render: () => `<div class="text-sm">${truncated}</div>`,
          };
        }
      );
      return renderSnippet(notesSnippet, {
        notes: row.original.notes,
      });
    },
  },
];
