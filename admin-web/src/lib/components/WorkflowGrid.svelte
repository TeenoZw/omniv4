<script>
  const workflows = [
    {
      id: "enquiry",
      title: "Enquiry Intake",
      actors: "Public → Admin",
      description: "Capture onboarding requests and hardware needs.",
      steps: [
        "Customer submits enquiry form",
        "Admin reviews and categorizes request",
        "Status remains new until quotation"
      ]
    },
    {
      id: "quotation",
      title: "Quotation & Approval",
      actors: "Admin, Finance",
      description: "Respond with pricing and confirm onboarding.",
      steps: [
        "Prepare hardware + plan quote",
        "Send quotation to customer",
        "Mark accepted and proceed to onboarding"
      ]
    },
    {
      id: "onboarding",
      title: "Hub & User Onboarding",
      actors: "System Admin",
      description: "Provision hubs, users, and plan details.",
      steps: [
        "Create hub and billing profile",
        "Assign plan type and contacts",
        "Seed first user + permissions"
      ]
    },
    {
      id: "inventory",
      title: "Hardware Inventory",
      actors: "System Admin",
      description: "Track device lifecycle and dispositions.",
      steps: [
        "Capture IMEI, Serial, Supplier, and cost details",
        "Move dispositions In Stock → Technician → Paired",
        "Audit every change with immutable logs"
      ]
    },
    {
      id: "billing",
      title: "Billing & Subscription",
      actors: "Finance Manager",
      description: "Automate billing cycles and subscription updates.",
      steps: [
        "Issue invoices and receipts",
        "Apply billing cadence (monthly)",
        "Suspend or reactivate based on payments"
      ]
    },
    {
      id: "support",
      title: "Support & Escalation",
      actors: "Support, Engineering",
      description: "Structured ticket flow with SLA tracking.",
      steps: [
        "Frontline troubleshooting",
        "Technical deep-dive",
        "Engineering escalation"
      ]
    },
    {
      id: "wialon",
      title: "Wialon Handoff",
      actors: "Client Users",
      description: "Provide tracking access through Wialon.",
      steps: [
        "Confirm Wialon credentials",
        "Share access link and onboarding steps",
        "Verify tracking access with sample device"
      ]
    }
  ];
</script>

<section class="rounded-3xl border border-white/10 bg-black/40 p-6 text-white">
  <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.4em] text-primary">Workflow Matrix</p>
      <h2 class="text-2xl font-semibold">Operational Playbook</h2>
      <p class="text-sm text-white/70">
        These tiles mirror `docs/30_Admin_onboarding.md` so every admin can see which workflows are in scope.
      </p>
    </div>
    <span class="rounded-full border border-white/10 px-4 py-1 text-xs uppercase tracking-[0.4em] text-white/60">
      {workflows.length} Workflows
    </span>
  </div>

  <div class="mt-6 grid gap-4 lg:grid-cols-3">
    {#each workflows as flow (flow.id)}
      <article class="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.4em] text-white/50">{flow.actors}</p>
            <h3 class="mt-1 text-lg font-semibold">{flow.title}</h3>
          </div>
          <span class="rounded-full border border-white/10 px-3 py-1 text-[0.65rem] uppercase tracking-[0.4em] text-white/60">
            {flow.id}
          </span>
        </div>
        <p class="mt-3 text-sm text-white/70">{flow.description}</p>
        <ul class="mt-4 space-y-2 text-sm text-white/80">
          {#each flow.steps as step (step)}
            <li class="flex items-start gap-2 rounded-xl border border-white/5 bg-black/30 px-3 py-2">
              <span class="mt-1 h-1.5 w-1.5 rounded-full bg-primary"></span>
              <span>{step}</span>
            </li>
          {/each}
        </ul>
      </article>
    {/each}
  </div>
</section>
