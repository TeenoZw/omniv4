<script lang="ts">
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Label } from "$lib/components/ui/label";
</script>

<section class="space-y-6">
  <div>
    <p class="text-xs uppercase tracking-wide text-muted-foreground">Profile</p>
    <h1 class="text-3xl font-semibold">Settings</h1>
    <p class="text-sm text-muted-foreground">Manage appearance and account notification preferences.</p>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>Preferences</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <Label>Dark mode</Label>
          <p class="text-xs text-muted-foreground">Follow the shared theme setting used across the portal.</p>
        </div>
        <input type="checkbox" checked class="h-5 w-5 rounded border border-muted-foreground/50" aria-label="Toggle dark mode" />
      </div>
      <div class="flex items-center justify-between">
        <div>
          <Label>Weekly digest</Label>
          <p class="text-xs text-muted-foreground">Receive a weekly summary of billing and support updates for this hub.</p>
        </div>
        <input type="checkbox" class="h-5 w-5 rounded border border-muted-foreground/50" aria-label="Toggle weekly digest" />
      </div>
    </CardContent>
  </Card>
</section>
