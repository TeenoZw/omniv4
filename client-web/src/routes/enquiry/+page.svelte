<svelte:head>
  <title>Omni Logistics · Request a Quote</title>
</svelte:head>

<script lang="ts">
  import MarketingShell from "$lib/marketing/MarketingShell.svelte";
  import { EnquirySection } from "$lib/landing";
</script>

<MarketingShell
  currentPath="/enquiry"
  title="Request a fleet tracking quote."
  kicker="Detailed enquiry"
  intro="Tell us about your vehicles, tracking needs, preferred hardware, add-ons, and target installation date. Omni will review your request and respond with pricing and next steps."
  image="/landing/omni-loader.jpg"
  imageAlt="Heavy equipment and logistics operations"
  primaryAction={{ href: "#enquiry-form", label: "Start your enquiry" }}
  secondaryAction={{ href: "/tracking", label: "Tracking Portal" }}
>
  <section id="enquiry-form" class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <EnquirySection />
  </section>
</MarketingShell>
