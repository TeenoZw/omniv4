<script lang="ts">
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card";
</script>

<section class="space-y-6">
  <div>
    <p class="text-xs uppercase tracking-wide text-muted-foreground">Platform access</p>
    <h1 class="text-3xl font-semibold">Integrations</h1>
    <p class="text-sm text-muted-foreground">Tracking portal access and connected platform services.</p>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>Tracking portal</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4 text-sm text-muted-foreground">
      <p>
        Omni Logistics manages onboarding, billing, and support while the tracking portal provides live fleet visibility.
        Use the tracking portal when you need real-time telematics and route monitoring.
      </p>
      <a
        href="/tracking"
        target="_blank"
        rel="noreferrer"
        class="inline-flex w-fit rounded-md border border-input px-4 py-2 text-sm font-medium text-foreground transition hover:bg-muted"
      >
        Open tracking portal
      </a>
      <div class="rounded-lg border border-dashed border-muted-foreground/30 p-4 text-sm text-muted-foreground">
        Additional integrations for ERP, dispatch, and analytics workflows will be introduced in a future release.
      </div>
    </CardContent>
  </Card>
</section>
