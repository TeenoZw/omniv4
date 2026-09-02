<svelte:head>
  <title>Omni Logistics · Terms and Conditions</title>
  <meta
    name="description"
    content="Terms and Conditions for the Omni Logistics website, customer accounts, tracking platform, hardware, installation, and related fleet management services."
  />
</svelte:head>

<script lang="ts">
  type TermsSection = {
    title: string;
    paragraphs: string[];
    bullets?: string[];
  };

  const terms: TermsSection[] = [
    {
      title: "1. About these Terms",
      paragraphs: [
        "These Terms and Conditions govern access to and use of the Omni Logistics public website, online enquiries, customer accounts, vehicle tracking platform, mobile or web-based services, tracking hardware, installation services and related fleet management services.",
        "Omni Logistics is a trading division of Omni Industrial Solutions (Private) Limited, a company registered in Zimbabwe. In these Terms, \"Omni\", \"we\", \"us\" and \"our\" refer to Omni Industrial Solutions (Private) Limited trading as Omni Logistics. \"You\" and \"your\" refer to any visitor, customer, account holder, authorised user or organisation using the Site or Services.",
        "Our principal business address is 1 Emerald Drive, Redcliff, Kwekwe, Zimbabwe.",
        "By accessing the Site, submitting an enquiry, accepting a quotation, purchasing hardware, authorising an installation, opening an account or using the Services, you agree to these Terms. If you act for a company or another person, you confirm that you have authority to bind them.",
      ],
    },
    {
      title: "2. Documents forming the agreement",
      paragraphs: [
        "Your agreement with Omni may include these Terms, an accepted quotation, order form, invoice, service schedule, installation form, written proposal, Privacy Policy and any special terms agreed in writing.",
        "If documents conflict, the following order applies unless we expressly agree otherwise in writing: an individually negotiated and signed service agreement; an accepted quotation or order form; a service schedule or installation form; these Terms; and information published generally on the Site.",
        "Prices, service levels, hardware specifications and delivery dates stated in an accepted quotation take priority over general information on the Site.",
      ],
    },
    {
      title: "3. Eligibility and authority",
      paragraphs: [
        "You must be at least eighteen years old and legally capable of entering into a contract to purchase or use the Services.",
        "You may only request installation or tracking for a vehicle that you own or are lawfully authorised to manage. We may require reasonable proof of ownership or authority, including a vehicle registration book, company letter or identity document. We may refuse or suspend an installation where ownership, authority or intended use cannot reasonably be verified.",
      ],
    },
    {
      title: "4. Our Services",
      paragraphs: [
        "Depending on your chosen plan, vehicle compatibility, installed hardware and network coverage, the Services may include live or near-live vehicle location information, route and trip history, geofences and alerts, driver behaviour reporting, approved immobilisation features, driver identification, fuel or vehicle telemetry, maintenance reminders, fleet reports, customer support, training and account administration.",
        "Some features require compatible hardware, sensors, accessories, vehicle wiring, manufacturer support or a specific subscription plan. Features described on the Site are general descriptions and are not guaranteed for every vehicle.",
      ],
    },
    {
      title: "5. Quotations, orders and pricing",
      paragraphs: [
        "Information and prices shown on the Site may be changed before an order is accepted. A Site enquiry is not an accepted order and does not reserve hardware, installation time or pricing.",
        "A quotation remains valid for the period shown on it. If no validity period is stated, it remains valid for fourteen days from its issue date, subject to stock availability and correction of obvious errors.",
        "Unless stated otherwise, amounts are quoted in United States dollars. The quotation or invoice will state whether taxes, delivery, installation, travel, accessories, SIM costs and subscription fees are included.",
        "You must pay all charges shown in the accepted quotation, invoice or service agreement by their due dates. Hardware fees and installation fees are normally once-off charges. Platform access, connectivity, support and related services may be charged monthly, annually or for another agreed licence period.",
        "We may change recurring fees by giving at least thirty days' notice. A fee change will not alter a fully prepaid fixed term licence during its current term unless required by law, tax, network operator charges or an agreed adjustment to the Services.",
      ],
    },
    {
      title: "6. Payments and overdue accounts",
      paragraphs: [
        "Payments must be made using a payment method approved by Omni. Any bank, payment platform or currency conversion fees charged to you are your responsibility unless agreed otherwise.",
        "Where an amount remains unpaid after its due date, we may send reminders, restrict paid features or suspend the affected Services after giving reasonable notice. Suspension does not erase amounts already due. We will not remotely immobilise a vehicle merely to collect an overdue debt.",
        "If a payment is disputed, you must notify us promptly and identify the invoice and disputed amount. The undisputed part remains payable.",
      ],
    },
    {
      title: "7. Installation and vehicle requirements",
      paragraphs: [
        "You must provide accurate vehicle details and disclose relevant modifications, electrical faults, warranty conditions, hazardous use, inaccessible equipment and any other fact that could materially affect installation.",
        "You must make the vehicle available at the agreed place and time in a safe, accessible condition. Additional visits, travel, repairs, removals, relocations or work caused by inaccurate information, vehicle defects or lack of access may be charged separately with your approval.",
        "We will use reasonable care and appropriately qualified personnel or approved technicians. Installation may involve connection to the vehicle electrical system, removal of trim and secure placement of hardware. You should disclose manufacturer warranty requirements before installation. No statement that an installation is \"warranty safe\" means that a vehicle manufacturer or dealer cannot independently apply its own lawful warranty conditions.",
        "After installation, you must promptly report warning lights, battery drain, damaged trim, abnormal vehicle behaviour or suspected faults. You must not tamper with, move, open or rewire installed equipment unless authorised by Omni.",
      ],
    },
    {
      title: "8. Hardware ownership, risk and warranty",
      paragraphs: [
        "Ownership of purchased hardware passes to you only after full payment. Risk of accidental loss or damage passes on delivery or installation, whichever applies.",
        "Rental, loan or subsidised equipment remains Omni's property where the quotation or service agreement says so. You must keep it reasonably safe and return it when the agreement ends, fair wear and tear excepted.",
        "Hardware and installation are covered by the warranty stated in the quotation, product documentation or applicable law. If no specific written period is stated, Omni will provide the warranty and remedies required by Zimbabwean law.",
        "Warranty cover does not extend to faults caused by collision, fire, flooding, theft, vandalism, unauthorised tampering, incorrect external wiring, misuse, abnormal voltage, vehicle defects, third party repairs, network changes or failure to follow reasonable instructions. This exclusion does not remove any right that cannot lawfully be excluded.",
        "Before approving a remedy, we may inspect and test the vehicle or equipment. Depending on the circumstances and applicable law, a valid remedy may include repair, replacement, reinstallation, service correction, credit or refund.",
      ],
    },
    {
      title: "9. Customer accounts and security",
      paragraphs: [
        "You are responsible for keeping usernames, passwords, authentication codes and account devices secure. You must use accurate account information, restrict access to authorised users and remove access when a user no longer needs it.",
        "You must notify Omni promptly if you suspect unauthorised access, credential loss, account compromise, device theft or misuse. We may temporarily restrict access where reasonably necessary to protect vehicles, people, data or the platform.",
        "Actions taken through a properly authenticated account may be treated as authorised unless you had already notified us of compromise or we knew, or reasonably should have known, that the action was unauthorised.",
      ],
    },
    {
      title: "10. Fleet operators, drivers and lawful monitoring",
      paragraphs: [
        "If you use the Services to monitor employees, contractors, drivers, passengers or other people, you are responsible for having a lawful basis and providing all notices, policies, consultations, permissions or consents required by law.",
        "You must clearly tell affected persons what information is collected, why it is collected, how it is used, who may access it and how long it may be retained. You must restrict access to people with a genuine operational, safety, security, compliance or legal need.",
        "The Services must not be used for secret, unlawful, discriminatory or abusive surveillance. Omni may request confirmation of lawful authority and may restrict or terminate access where there is credible evidence of unlawful monitoring.",
      ],
    },
    {
      title: "11. Location information and platform accuracy",
      paragraphs: [
        "Tracking information depends on satellite visibility, mobile network availability, device power, correct installation, map information, server availability and other technical factors. Locations, speeds, fuel levels, distances, driver events and arrival times may therefore be delayed, incomplete or inaccurate.",
        "The Services are fleet management and security aids. They are not emergency services, certified measuring instruments, police services, insurance products or a substitute for responsible driving, physical security, vehicle maintenance or independent verification.",
        "You must not rely solely on the platform where inaccurate or delayed information could cause death, injury, unlawful action, loss of liberty, unsafe vehicle operation or serious property damage.",
      ],
    },
    {
      title: "12. Remote immobilisation and control features",
      paragraphs: [
        "Important safety notice: remote immobilisation or engine cut off can create a risk of collision, injury, vehicle damage or unlawful interference if used while a vehicle is moving, in an unsafe place or without proper authority.",
        "You may use a remote control feature only where it is lawful, reasonably safe and authorised by the vehicle owner. Unless a specifically engineered safety function provides otherwise, an immobilisation command should only be issued after you have reasonably confirmed that the vehicle is stationary and safely positioned.",
        "You are responsible for decisions to issue commands through your account. Omni may delay, reject or disable a command where we reasonably believe it is unauthorised, technically unsafe, unlawful or likely to harm a person or property.",
        "Nothing in the Services guarantees recovery of a stolen vehicle. Suspected theft should be reported promptly to the Zimbabwe Republic Police or the relevant local authority. You should not personally confront a suspected thief based only on tracking information.",
      ],
    },
    {
      title: "13. Acceptable use",
      paragraphs: ["You must not:"],
      bullets: [
        "Use the Site or Services unlawfully or to violate another person's rights.",
        "Track a person or vehicle without lawful authority.",
        "Harass, stalk, intimidate, discriminate against or endanger another person.",
        "Attempt to defeat security, gain unauthorised access, introduce malicious code, overload the platform or interfere with other users.",
        "Copy, scrape, reverse engineer, resell, sublicense or commercially exploit the platform except as expressly authorised in writing.",
        "Submit false ownership, identity, vehicle or payment information.",
        "Use reports as conclusive evidence without considering accuracy limitations and context.",
        "Use remote commands in an unsafe or unauthorised way.",
      ],
    },
    {
      title: "14. SIM cards, networks and third party services",
      paragraphs: [
        "The Services may depend on mobile network operators, satellite systems, mapping providers, hosting providers, payment providers, hardware manufacturers and fleet software providers that Omni does not control.",
        "Network coverage, roaming, older network technologies, maps and third party systems may change or become unavailable. We may make reasonably necessary technical substitutions or migrations to maintain the Services. If a material change significantly reduces paid functionality, we will provide a reasonable remedy as required by the agreement and applicable law.",
        "SIM cards supplied or managed by Omni may only be used in approved tracking equipment. Unauthorised removal, transfer, voice use or data use may result in restriction and recovery of associated costs.",
      ],
    },
    {
      title: "15. Maintenance, availability and support",
      paragraphs: [
        "We aim to provide reliable Services but do not promise uninterrupted or error-free availability. Maintenance, upgrades, faults, cyber incidents, power failures, network outages and events outside reasonable control may interrupt access.",
        "We may perform planned maintenance and will give reasonable notice where practical. Support channels and response targets are those stated in your plan, quotation or service agreement. A response target is not a guarantee that every fault will be resolved within that period.",
      ],
    },
    {
      title: "16. Privacy and data protection",
      paragraphs: [
        "Our Privacy Policy explains how Omni collects, uses, stores, shares and protects personal information, including account information, vehicle location, trip records, device identifiers and support communications. The Privacy Policy forms part of these Terms.",
        "Where a customer determines why and how employee, driver or passenger information is processed, that customer may be the data controller and Omni may act as a processor or service provider on the customer's instructions. The parties will comply with their respective obligations under Zimbabwe's Cyber and Data Protection Act and other applicable law.",
        "You must not upload unnecessary personal information or instruct Omni to process information unlawfully. We may process and disclose information where reasonably necessary to provide the Services, protect security, comply with law, respond to valid legal process or enforce the agreement.",
      ],
    },
    {
      title: "17. Intellectual property",
      paragraphs: [
        "The Site, platform, software, branding, graphics, reports, documentation and other content supplied by Omni or its licensors are protected by intellectual property law. Except for the limited right to use the Services during your subscription, no ownership right is transferred to you.",
        "You retain rights in information that you lawfully provide. You grant Omni and its service providers a limited right to host, transmit, process, display and use that information only as reasonably necessary to provide, secure, improve and support the Services, comply with law and meet the purposes described in the Privacy Policy.",
        "You may download or print your reports for lawful internal use. Removal of ownership notices, unauthorised publication of platform content and use of Omni branding without permission are prohibited.",
      ],
    },
    {
      title: "18. Customer content and feedback",
      paragraphs: [
        "You confirm that you have the right to provide all vehicle, driver, user and other information submitted through the Services. You are responsible for its accuracy and legality.",
        "If you voluntarily give suggestions or general feedback, Omni may use them without payment or restriction, provided we do not publicly identify you or disclose confidential information without permission.",
      ],
    },
    {
      title: "19. Confidentiality",
      paragraphs: [
        "Each party must take reasonable care to protect non-public technical, commercial and operational information received from the other and use it only for the agreement. This obligation does not cover information that is public through no breach, already lawfully known, independently developed, lawfully received from another source or required to be disclosed by law.",
      ],
    },
    {
      title: "20. Suspension and termination",
      paragraphs: [
        "You may stop using the Site at any time. Subscription cancellation, notice periods, minimum terms and prepaid licence conditions are set out in the accepted quotation or service agreement.",
        "We may suspend or terminate affected Services after reasonable notice if you materially breach the agreement, fail to pay an undisputed amount, use the Services unlawfully, create a serious security or safety risk, misuse remote control features or repeatedly interfere with the platform.",
        "We may act immediately where reasonably necessary to prevent imminent harm, unlawful surveillance, unauthorised immobilisation, fraud, cyberattack or serious platform disruption. We will explain the action when lawful and reasonably practical.",
        "On termination, your right to use the affected Services ends. Amounts already due remain payable. Treatment of prepaid amounts, hardware, stored data and account exports will follow the accepted quotation, applicable law and the Privacy Policy. Sections that by their nature should continue after termination remain effective.",
      ],
    },
    {
      title: "21. Refunds and cancellations",
      paragraphs: [
        "Refunds and cancellations depend on the type of purchase, work already completed, hardware condition, special orders, activated SIM or licence costs and applicable consumer law.",
        "Nothing in these Terms removes a statutory right to a repair, replacement, correction, refund, cancellation or other remedy. If you change your mind where no statutory cancellation right applies, Omni may still agree to cancellation on reasonable written terms, including recovery of properly incurred and disclosed costs.",
        "Custom configured, installed, damaged or used hardware may not qualify for a change-of-mind return, but this does not affect remedies for defective, unsafe, misdescribed or incorrectly supplied goods or services.",
      ],
    },
    {
      title: "22. Warranties and responsibility",
      paragraphs: [
        "Omni will perform the Services with reasonable care and skill and will honour warranties required by applicable law.",
        "Except where expressly stated or required by law, we do not guarantee that the Services will prevent theft, recover a vehicle, eliminate fuel loss, prove driver misconduct, remain available at all times or produce perfectly accurate data.",
        "You remain responsible for fleet decisions, driver management, legal compliance, insurance, maintenance, physical security and verifying important information before acting on it.",
      ],
    },
    {
      title: "23. Limitation of liability",
      paragraphs: [
        "Important liability notice: this section limits the circumstances and amount for which Omni may be responsible. Please read it before purchasing or using the Services.",
        "Nothing in these Terms excludes or limits liability that cannot lawfully be excluded, including liability arising from fraud, wilful misconduct, gross negligence, death or personal injury where exclusion is prohibited, or a consumer right protected by law.",
        "Subject to the paragraph above, Omni is not responsible for indirect or consequential loss, loss of profit, loss of anticipated savings, loss of business opportunity or loss caused by a customer's unlawful use, unsafe immobilisation command, unauthorised account access resulting from the customer's failure to protect credentials, vehicle defect, third party network failure or event beyond Omni's reasonable control.",
        "For a business customer, and only to the extent permitted by law, Omni's total liability arising from one event or a series of related events will not exceed the total service fees paid for the affected vehicle or service during the twelve months immediately before the event. This limit does not reduce any mandatory remedy relating to hardware or services and does not apply where a signed agreement states a different limit.",
        "For an individual consumer, liability will be determined under applicable consumer law, and no financial cap in these Terms will take away a right or remedy that the law does not allow Omni to limit.",
      ],
    },
    {
      title: "24. Indemnity for unlawful use",
      paragraphs: [
        "To the extent permitted by law, a business customer will be responsible for reasonable losses, claims and costs suffered by Omni because the customer or its authorised users knowingly use the Services for unlawful tracking, unauthorised immobilisation, infringement of another person's rights or a material breach of these Terms.",
        "This responsibility does not apply to the extent that the loss was caused by Omni's breach, negligence or unlawful conduct. Nothing in this section requires an individual consumer to assume liability in a manner prohibited by consumer law.",
      ],
    },
    {
      title: "25. Events outside reasonable control",
      paragraphs: [
        "Neither party is responsible for delay or failure caused by an event beyond its reasonable control, including natural disaster, severe weather, fire, war, civil disturbance, government action, widespread network or power failure, labour disruption, border delay or major failure of a critical third party system.",
        "The affected party must take reasonable steps to reduce the effect and resume performance. This section does not excuse payment for Services already supplied.",
      ],
    },
    {
      title: "26. Changes to the Services or these Terms",
      paragraphs: [
        "We may update these Terms to reflect legal, security, technical or service changes. The latest version and effective date will be published on the Site.",
        "For a material change affecting an active paid Service, we will give reasonable advance notice through email, the platform, the Site or another agreed channel. If the change materially disadvantages you, any right to cancel will be handled under your service agreement and applicable law.",
        "Continued use after the effective date constitutes acceptance where permitted by law. Changes will not retrospectively remove accrued rights or alter an agreed fixed term price without a lawful and contractual basis.",
      ],
    },
    {
      title: "27. Notices and electronic communications",
      paragraphs: [
        "You agree that enquiries, quotations, invoices, notices and service communications may be sent electronically using the contact information you provide. You must keep your contact details current.",
        "Formal notices to Omni may be delivered to our stated business address or through the official contact details published on the Site. A notice is treated as received according to applicable law and any specific notice clause in your service agreement.",
      ],
    },
    {
      title: "28. Complaints and dispute resolution",
      paragraphs: [
        "Please first send a complaint through the official contact details on the Site, giving your name, account or vehicle reference, the issue and the remedy requested. We will acknowledge and address complaints within a reasonable time.",
        "The parties should first try in good faith to resolve a dispute through direct discussion. They may then agree to mediation or another lawful form of alternative dispute resolution.",
        "Nothing in this section prevents a consumer from approaching the Consumer Protection Commission, a competent court or another regulator, or from exercising any non-waivable right.",
      ],
    },
    {
      title: "29. Governing law and jurisdiction",
      paragraphs: [
        "These Terms and the agreement are governed by the laws of Zimbabwe. Subject to any mandatory consumer right or agreed dispute procedure, the courts of Zimbabwe have jurisdiction.",
        "If the Services are used in another country, you are also responsible for complying with the laws that apply where the vehicle, driver and users are located. This does not exclude the application of any mandatory local law.",
      ],
    },
    {
      title: "30. General provisions",
      paragraphs: [
        "If any provision is unlawful or unenforceable, it will be limited or removed only to the extent necessary, and the remaining provisions will continue.",
        "A delay in enforcing a right is not a waiver of that right. You may not transfer your agreement or account without Omni's written consent, which will not be unreasonably withheld. Omni may transfer the agreement as part of a genuine restructuring, financing or sale of the relevant business, subject to applicable law and continued protection of your rights.",
        "These Terms do not create a partnership, employment relationship, franchise or agency between you and Omni.",
        "Headings are for convenience and do not change the meaning of the Terms. Words such as \"including\" do not limit the examples that follow.",
      ],
    },
    {
      title: "31. Contacting Omni",
      paragraphs: [
        "Questions, complaints, privacy requests and legal notices may be submitted through the official contact channels published at www.omnilogistics.co.zw or delivered to Omni Industrial Solutions (Private) Limited, trading as Omni Logistics, 1 Emerald Drive, Redcliff, Kwekwe, Zimbabwe.",
        "When contacting us about an account or vehicle, we may ask for reasonable information to verify your identity and authority before disclosing information or making account changes.",
      ],
    },
  ];
</script>

<section class="mx-auto mt-6 max-w-4xl rounded-3xl border border-slate-100 bg-white/90 p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-950/90 sm:p-8">
  <div class="space-y-4">
    <a href="/" class="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">
      Back to home
    </a>
    <div>
      <p class="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300">Omni Logistics</p>
      <h1 class="mt-3 text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">Terms and Conditions</h1>
      <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">Last updated: September 1, 2026</p>
      <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
        These terms apply to the Omni Logistics website, customer accounts, vehicle tracking platform, hardware,
        installation services and related fleet management services.
      </p>
    </div>
  </div>

  <div class="mt-8 space-y-7 text-sm leading-7 text-slate-700 dark:text-slate-300">
    {#each terms as section}
      <article>
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{section.title}</h2>
        <div class="mt-2 space-y-2">
          {#each section.paragraphs as paragraph}
            <p>{paragraph}</p>
          {/each}
          {#if section.bullets}
            <ul class="list-disc space-y-2 pl-5">
              {#each section.bullets as bullet}
                <li>{bullet}</li>
              {/each}
            </ul>
          {/if}
        </div>
      </article>
    {/each}
  </div>
</section>
