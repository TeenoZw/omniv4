<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { buttonVariants } from "$lib/components/ui/button";
  import { cn } from "$lib/utils.js";

  const supportChannels = [
    { label: "Email", value: "support@omnilogistics.co.zw" },
    { label: "Phone", value: "+263 777 233 814" },
    { label: "WhatsApp", value: "+263 777 233 814" },
  ];
</script>

<section class="space-y-6">
  <div class="flex flex-col gap-2">
    <p class="text-xs uppercase tracking-wide text-muted-foreground">Support</p>
    <h1 class="text-3xl font-semibold leading-tight">Technical support</h1>
    <p class="text-sm text-muted-foreground">
      Omni Logistics supports onboarding, billing, subscription management, and hardware-related service requests.
    </p>
  </div>

  <div class="grid gap-6 lg:grid-cols-2">
    <Card>
      <CardHeader>
        <CardTitle>Contact support</CardTitle>
        <CardDescription>Reach our team for installation, SIM, subscription, or billing assistance.</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4 text-sm text-muted-foreground">
        <div class="space-y-2">
          {#each supportChannels as channel}
            <div class="flex items-center justify-between">
              <span>{channel.label}</span>
              <span class="font-medium text-foreground">{channel.value}</span>
            </div>
          {/each}
        </div>
        <div class="flex flex-wrap gap-2">
          <Badge variant="secondary">Response target: 24 to 48 hours</Badge>
          <Badge variant="secondary">Escalation support available</Badge>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Feedback</CardTitle>
        <CardDescription>Help us improve your onboarding and service experience.</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4 text-sm text-muted-foreground">
        <p>
          Share feedback after onboarding, billing support, or hardware service interactions. Every submission is reviewed and followed up by the Omni team.
        </p>
        <a href="/enquiry" class={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
          Send feedback
        </a>
      </CardContent>
    </Card>
  </div>
</section>
