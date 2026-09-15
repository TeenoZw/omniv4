<script lang="ts">
  const dataCategories = [
    "Customer and account details, including names, phone numbers, email addresses, company details, billing contacts, authorised portal users, and support contacts.",
    "Vehicle, asset, driver, and installation records, including registration numbers, make, model, VIN or chassis details where supplied, assigned tracker hardware, SIM records, installation notes, maintenance notes, and service history.",
    "Telematics and operational data, including GPS location, trip history, speed, ignition status, events, alerts, geofence activity, device diagnostics, connectivity status, odometer or engine-related readings where supported by the hardware, and related fleet reports.",
    "Commercial and financial records, including enquiries, quotations, contracts, orders, invoices, receipts, subscriptions, payment references, tax and fiscalisation records, and account status.",
    "Platform and security records, including login activity, role permissions, audit logs, session information, device identifiers, IP addresses, browser information, support tickets, customer portal activity, and administrative actions.",
    "Communications and support information, including emails, calls, WhatsApp or messaging records, installation coordination notes, ticket updates, and feedback submitted through our website or support channels.",
  ];

  const purposes = [
    "to respond to enquiries, prepare quotations, onboard customers, create customer portal access, and manage account relationships;",
    "to install, configure, support, recover, replace, reassign, and maintain GPS trackers, SIM cards, accessories, and related hardware;",
    "to provide fleet tracking, asset monitoring, trip history, alerting, reporting, customer support, and managed telematics services;",
    "to manage subscriptions, billing, invoicing, payment follow-up, tax records, fiscalisation requirements, and customer statements;",
    "to maintain platform security, audit user activity, investigate incidents, prevent misuse, and protect vehicles, assets, people, systems, and records;",
    "to improve our services, troubleshoot faults, plan stock and technician work, and understand service quality without using more personal information than reasonably necessary;",
    "to comply with Zimbabwean legal, regulatory, contractual, tax, accounting, telecommunications, cybersecurity, and data protection obligations.",
  ];

  const rights = [
    "ask whether we hold personal information about you and request access to that information;",
    "ask us to correct or update information that is inaccurate, incomplete, or outdated;",
    "ask us to delete, destroy, or de-identify information where we no longer have a lawful reason to keep it;",
    "object to certain processing activities where the law allows an objection;",
    "withdraw consent where processing is based on consent, without affecting lawful processing already carried out before withdrawal;",
    "ask for information about how to complain to the relevant Zimbabwean authority where a data protection concern cannot be resolved with us.",
  ];
</script>

<svelte:head>
  <title>Omni Logistics · Privacy Policy</title>
  <meta
    name="description"
    content="Privacy Policy for Omni Logistics, covering customer accounts, fleet tracking, telematics, installations, billing, support, and the Omni customer portal."
  />
</svelte:head>

<section class="mx-auto mt-6 max-w-4xl rounded-3xl border border-slate-100 bg-white/90 p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-950/90 sm:p-8">
  <div class="space-y-4">
    <a href="/" class="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">
      ← Back to home
    </a>
    <div>
      <p class="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300">Omni Logistics</p>
      <h1 class="mt-3 text-3xl font-bold text-slate-900 dark:text-white">Privacy Policy</h1>
      <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">
        Last updated: September 15, 2026
      </p>
    </div>
    <p class="max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
      This policy explains how Omni Logistics collects, uses, stores, shares, and protects personal information when
      providing fleet tracking, telematics, installation, SIM management, billing, support, customer portal, and related
      business services in Zimbabwe.
    </p>
  </div>

  <div class="mt-8 space-y-7 text-sm leading-7 text-slate-700 dark:text-slate-300">
    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">1. Who we are</h2>
      <p class="mt-2">
        Omni Logistics is a trading division of Omni Industrial Solutions (Private) Limited, a company registered in
        Zimbabwe. In this policy, "Omni", "we", "us" and "our" refer to Omni Industrial Solutions (Private) Limited
        trading as Omni Logistics.
      </p>
      <div class="mt-3 rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-900/70">
        <p class="font-semibold text-slate-900 dark:text-white">Privacy and data protection contact</p>
        <p>Tinotenda Langton Mutami</p>
        <p><a class="underline" href="mailto:info@omnilogistics.co.zw">info@omnilogistics.co.zw</a></p>
        <p>+263 777 233 814</p>
        <p>1 Emerald Drive, Redcliff, Kwekwe, Zimbabwe</p>
      </div>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">2. Legal framework</h2>
      <p class="mt-2">
        This policy is prepared with reference to Zimbabwe's Cyber and Data Protection Act [Chapter 12:07], applicable
        regulations and implementation guidance, and other Zimbabwean laws that apply to our services, including tax,
        accounting, telecommunications, contract, consumer protection, and company record-keeping requirements.
      </p>
      <p class="mt-2">
        Where Omni determines why and how personal information is processed for its own services, we act as a data
        controller. Where we process information on the documented instructions of a customer, we may act as an operator
        or processor for that customer.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">3. Scope of this policy</h2>
      <p class="mt-2">
        This policy applies to the Omni public website, enquiry forms, customer onboarding, Omni customer portal,
        administrative platform, support desk, installation workflows, fleet records, telematics integrations, billing,
        invoicing, and related communication channels.
      </p>
      <p class="mt-2">
        Some tracking functions may also be provided through third-party telematics platforms or mobile network services.
        Those providers may have their own terms and privacy documents. Omni remains responsible for using such providers
        in a controlled way for the services we manage.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">4. Personal information we process</h2>
      <ul class="mt-2 list-disc space-y-2 pl-5">
        {#each dataCategories as category}
          <li>{category}</li>
        {/each}
      </ul>
      <p class="mt-2">
        We do not intentionally collect sensitive personal information unless it is necessary for a lawful service,
        support, security, employment, legal, or incident-related reason. Customers should not send us unnecessary
        personal information through free-text fields, documents, or support tickets.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">5. Location and telematics data</h2>
      <p class="mt-2">
        Fleet tracking services rely on location and device data. This may show where a vehicle or asset is, where it has
        travelled, when it stopped, whether ignition was on, whether alerts were triggered, and which customer account,
        hub, driver, technician, or device record is associated with the event.
      </p>
      <p class="mt-2">
        Telematics data is used to provide tracking, security, recovery support, route and trip history, reporting,
        maintenance planning, support diagnostics, billing checks, and operational accountability. It must not be used by
        customers or authorised users for secret, unlawful, discriminatory, or abusive surveillance.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">6. Customer responsibility for drivers and users</h2>
      <p class="mt-2">
        Where a customer uses Omni services to monitor vehicles, drivers, employees, contractors, or other users, the
        customer is responsible for having a lawful basis to do so and for giving any notices, workplace policies,
        consultations, permissions, or consents required by law. Omni may ask a customer to confirm that it has authority
        to request tracking, portal access, reports, commands, or record changes.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">7. Why we process personal information</h2>
      <ul class="mt-2 list-disc space-y-2 pl-5">
        {#each purposes as purpose}
          <li>{purpose}</li>
        {/each}
      </ul>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">8. Lawful basis for processing</h2>
      <p class="mt-2">
        Depending on the context, we process personal information because it is necessary for a contract or requested
        quotation, required by law, needed for a legitimate service or security interest, necessary to protect an interest
        of a data subject or another person, or based on consent where consent is the appropriate basis.
      </p>
      <p class="mt-2">
        We aim to collect information for specific, explicit, and lawful purposes; use it in a way compatible with those
        purposes; keep it accurate where practical; and avoid collecting more information than is reasonably necessary for
        the service or obligation involved.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">9. Sharing and disclosure</h2>
      <p class="mt-2">
        We may share information with authorised Omni directors, employees, technicians, contractors, installers,
        accountants, legal advisers, auditors, hosting providers, software providers, telematics platform providers,
        mobile network operators, payment or banking providers, tax or fiscalisation service providers, and support
        partners where they need the information to perform their role.
      </p>
      <p class="mt-2">
        We may also disclose information where required by law, lawful request, court order, regulator, tax authority,
        law enforcement process, emergency response, fraud prevention, debt recovery, insurance claim, or business
        continuity need.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">10. Cross-border processing</h2>
      <p class="mt-2">
        Some service providers, hosting infrastructure, software tools, email services, maps, payment systems, telematics
        platforms, or backup services may process information outside Zimbabwe. Where this happens, we take reasonable
        steps to use providers, contracts, controls, and access restrictions that protect the information in a manner
        appropriate to the service and applicable law.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">11. Security safeguards</h2>
      <p class="mt-2">
        Omni uses reasonable technical and organisational safeguards to protect personal information against loss,
        unauthorised access, unlawful processing, damage, misuse, alteration, or disclosure. These safeguards may include:
      </p>
      <ul class="mt-2 list-disc space-y-2 pl-5">
        <li>role-based access and least-privilege permissions;</li>
        <li>authentication, session controls, and account management;</li>
        <li>audit logs for administrative and security-relevant activity;</li>
        <li>controlled access to customer, vehicle, tracker, SIM, billing, and support records;</li>
        <li>secure hosting, backups, infrastructure controls, and deployment procedures;</li>
        <li>supplier and technician controls appropriate to the work being performed; and</li>
        <li>incident response, investigation, and escalation procedures.</li>
      </ul>
      <p class="mt-2">
        No system is completely risk-free, but we work to apply safeguards that are appropriate to the sensitivity of the
        information and the practical risks of fleet tracking operations.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">12. Data breach handling</h2>
      <p class="mt-2">
        If we become aware of a personal data breach affecting information we control, we will investigate, contain the
        incident, keep appropriate records, notify the Data Protection Authority or other relevant authority within the
        period required by Zimbabwean law where notification is required, and notify affected data subjects where required
        or where we believe notification is appropriate to reduce harm.
      </p>
      <p class="mt-2">
        Customers and authorised users must tell Omni promptly if they suspect account compromise, lost credentials,
        unauthorised portal access, device tampering, SIM misuse, or unauthorised disclosure of reports or tracking data.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">13. Retention</h2>
      <p class="mt-2">
        We keep personal information only for as long as reasonably necessary for the purpose collected, including service
        delivery, customer support, billing, legal compliance, tax and accounting records, auditability, dispute handling,
        security, warranty support, and legitimate operational history. Different record types may be kept for different
        periods.
      </p>
      <p class="mt-2">
        When information is no longer required, we will delete, destroy, archive, anonymise, or de-identify it where
        practical and lawful. Backups and audit records may persist for a limited period according to technical retention
        schedules.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">14. Data subject rights</h2>
      <p class="mt-2">Where applicable under Zimbabwean law, you may:</p>
      <ul class="mt-2 list-disc space-y-2 pl-5">
        {#each rights as right}
          <li>{right}</li>
        {/each}
      </ul>
      <p class="mt-2">
        Requests may be sent to <a class="underline" href="mailto:info@omnilogistics.co.zw">info@omnilogistics.co.zw</a>.
        We may ask for information needed to verify identity, authority, the affected customer account, and the records
        involved. We may refuse, limit, or defer a request where Zimbabwean law permits or requires us to do so.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">15. Marketing communications</h2>
      <p class="mt-2">
        Omni does not sell personal information. We may contact existing or prospective customers about Omni services,
        account matters, quotations, support, product changes, renewals, or operational updates. Promotional messages will
        be sent only where we have a lawful basis and will include a practical way to opt out where required.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">16. Cookies and website analytics</h2>
      <p class="mt-2">
        Our website and portal may use necessary cookies or local storage for login sessions, security, preferences,
        theme settings, form handling, and basic site functionality. If we introduce analytics, advertising, or optional
        tracking tools, we will configure them in a way that is consistent with this policy and applicable law.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">17. Children</h2>
      <p class="mt-2">
        Omni services are intended for businesses, organisations, and authorised adult users. We do not knowingly create
        customer portal accounts for children. If a customer's fleet activity incidentally involves children as passengers
        or service beneficiaries, the customer must ensure that any monitoring or record keeping is lawful and
        proportionate.
      </p>
    </div>

    <div>
      <h2 class="text-lg font-semibold text-slate-900 dark:text-white">18. Changes to this policy</h2>
      <p class="mt-2">
        We may update this policy from time to time to reflect legal, operational, technical, or service changes. The
        latest version will be published on this site. Material changes affecting active customer services may also be
        communicated through email, the customer portal, service documents, or another appropriate channel.
      </p>
    </div>
  </div>
</section>
