# Inbox Tab — Implementation Prompt

## Objective

Add a new **Inbox** tab to the existing supply-chain control-center application.

The Inbox should look and behave visually like a modern **Gmail-style enterprise email interface**, while remaining a fully simulated hackathon UI.

Its purpose is to let users see supplier communications and clearly distinguish emails sent autonomously by the **AI Supply Chain Agent** from normal supplier/company emails.

The existing database, backend logic, agent logic, APIs, IDs, relationships, scenarios, and other application functionality must remain unchanged.

---

## 1. Scope

This is primarily a frontend/UI addition.

Do not modify:

- Database schema
- Existing database IDs
- Foreign keys
- Existing tables
- Agent logic
- Existing tool definitions
- Existing APIs
- Scenario logic
- Procurement calculations
- Inventory calculations
- Production logic
- Audit-trail logic

Use hardcoded sample email data for the demo unless the existing application already has an appropriate email data source.

---

## 2. Sidebar

Add:

> **Inbox**

with a mail/envelope icon.

Use the application's existing sidebar, routing, typography, spacing, and theme.

Example:

```text
Dashboard
Disruptions
Inventory
Purchase Orders
Suppliers
Production
✉ Inbox
Agent Activity
Scenario Lab
```

Do not replace or restructure the existing sidebar.

---

## 3. Inbox UI

Create a Gmail-like layout:

```text
┌────────────────────────────────────────────────────────────┐
│ Inbox                                      Search mail 🔍  │
├────────────────────────────────────────────────────────────┤
│ Inbox (12)     Starred     Sent                            │
├────────────────────────────────────────────────────────────┤
│ □ ☆ Apex Auto Parts        Delay on PO-7712        2:14 AM │
│ □ ☆ PrimeDrive Components  RFQ Response – Brake Pad 2:11 │
│ □ ☆ Nova Mobility Parts    Certification Details   1:58  │
└────────────────────────────────────────────────────────────┘
```

Include:

- Inbox
- Sent
- Search UI
- Read/unread styling
- Sender
- Subject
- Timestamp
- Email preview/snippet
- Star icon
- Checkbox
- Email detail view
- Optional attachment indicator

Do not implement unnecessary real Gmail functionality.

---

## 4. Email Detail

Clicking an email should open a readable detail view.

Example:

```text
← Back to Inbox

Delay on PO-7712

Apex Auto Parts
procurement@apexautoparts.example
Today, 02:14 AM

Hello Procurement Team,

Due to transportation issues, the delivery for PO-7712
may be delayed by approximately five days.

We are checking whether a partial shipment can be arranged.

Regards,
Apex Auto Parts
```

Agent emails should clearly display:

```text
🤖 AI AGENT
```

Use a distinct accent text color for the AI Agent label/sender.

---

# 5. Received Emails

Hardcode at least **10 sample emails**.

Use the scenarios and expected behavior from the existing problem statement as the source of the email content.

The emails must cover:

1. Supplier delay
2. Revised delivery estimate
3. Partial shipment possibility
4. Alternate supplier quotation
5. Quality/certification information
6. Shipment/tracking update
7. Supplier availability confirmation
8. Supplier quantity limitation
9. Expedited shipping availability
10. Supplier response to an urgent RFQ
11. Production requirement
12. Emergency supply confirmation

Use fictional suppliers such as:

- Apex Auto Parts
- PrimeDrive Components
- Nova Mobility Parts
- Precision Auto Systems
- Vertex Components
- Metro Auto Parts
- Spark Automotive
- DriveTech Components
- Pioneer Auto Systems
- Summit Mobility

Do not imply these are real supplier relationships.

---

# 6. Sample Received Emails

Use these as the initial demo dataset.

### Email 1 — Supplier Delay

**Sender:** Apex Auto Parts  
**Subject:** Delay on PO-7712  
**Status:** Unread  
**Scenario:** Supplier Delay

```text
Hello Procurement Team,

Due to unexpected transportation issues, the delivery
for PO-7712 may be delayed by approximately 5 days.

The original expected delivery date was September 4.
Our current estimated delivery is September 9.

We are checking whether a partial shipment can be arranged
and will provide an update shortly.

Regards,
Apex Auto Parts
```

### Email 2 — Revised Delivery

**Sender:** Apex Auto Parts  
**Subject:** Updated ETA for PO-7712  
**Status:** Read

```text
Hello,

We have reviewed the shipment status for PO-7712.

The revised estimated delivery date is September 9.
We currently cannot guarantee an earlier full shipment.

We will notify you if the transportation situation improves.

Regards,
Apex Auto Parts
```

### Email 3 — Partial Shipment

**Sender:** Apex Auto Parts  
**Subject:** Partial Shipment Option – PO-7712  
**Status:** Read

```text
Hello Procurement Team,

We can arrange a partial shipment of 300 Brake Pads
within 3 days.

The remaining quantity would follow on the revised
September 9 delivery schedule.

Please confirm if you would like us to proceed.

Regards,
Apex Auto Parts
```

### Email 4 — Alternate Supplier Quote

**Sender:** PrimeDrive Components  
**Subject:** RFQ Response – Brake Pad  
**Status:** Unread

```text
Hello,

Thank you for your urgent RFQ.

We can provide 600 Brake Pads.

Unit price: ₹132
Lead time: 4 days
Minimum order quantity: 300 units
Expedited shipping: Available

Our quoted availability is valid for 6 hours.

Regards,
PrimeDrive Components
```

### Email 5 — Quality Certification

**Sender:** Nova Mobility Parts  
**Subject:** Certification Details – Brake Pad Supply  
**Status:** Read

```text
Hello,

We can supply the requested Brake Pads within 3 days.

However, our current production batch does not carry
the required automotive-grade certification.

Please confirm whether an exception has been approved
before placing an order.

Regards,
Nova Mobility Parts
```

This supports the quality-constraint scenario: the fastest/cheapest supplier should not automatically win if certification requirements are not satisfied.

### Email 6 — Tracking Update

**Sender:** Apex Auto Parts  
**Subject:** Shipment Tracking Update – PO-7712  
**Status:** Unread

```text
Hello,

PO-7712 has been dispatched from our facility.

Tracking information has been updated in the shipment
system.

Regards,
Apex Auto Parts
```

The separate simulated tracking system should be able to show:

```text
Status: Label Created
Pickup: Not Confirmed
Last Movement: None
```

This creates the supplier-claim contradiction required by the adversarial supplier scenario.

### Email 7 — Quantity Limitation

**Sender:** Precision Auto Systems  
**Subject:** Availability Confirmation – Battery Controller  
**Status:** Read

```text
Hello,

We currently have 350 Battery Controllers available
for immediate shipment.

We cannot fulfill the complete requested quantity of
600 units from current stock.

The remaining quantity would require approximately
8 additional days.

Regards,
Precision Auto Systems
```

### Email 8 — Expedited Shipping

**Sender:** Vertex Components  
**Subject:** Expedited Delivery Option  
**Status:** Unread

```text
Hello Procurement Team,

We can support expedited delivery for the requested
Brake Pad quantity.

Estimated delivery: 4 days
Expedite fee: ₹12,000

Please note that the quotation is valid for 6 hours.

Regards,
Vertex Components
```

### Email 9 — Supplier Availability

**Sender:** Metro Auto Parts  
**Subject:** Urgent Availability – Brake Pads  
**Status:** Read

```text
Hello,

We currently have 700 Brake Pads available.

Standard delivery is 6 days.

Unit price: ₹128
Minimum order quantity: 300 units

Expedited shipping is currently unavailable.

Regards,
Metro Auto Parts
```

### Email 10 — Production Requirement

**Sender:** Pune Vehicle Plant Procurement  
**Subject:** Urgent Production Requirement – Brake Pads  
**Status:** Unread

```text
Hello Procurement Team,

The Pune Vehicle Plant has confirmed that the current
high-priority production order requires 700 Brake Pads.

Current usable inventory is expected to provide limited
production coverage.

Please prioritize continuity of the high-priority order
and provide an updated recovery plan.

Regards,
Pune Vehicle Plant Procurement
```

### Email 11 — Urgent RFQ Response

**Sender:** DriveTech Components  
**Subject:** Urgent RFQ Response – Brake Pads  
**Status:** Read

```text
Hello,

We can supply 300 Brake Pads within 2 days.

Unit price: ₹145
Minimum order quantity: 300 units
Quality certification: Available

The quantity is limited and subject to confirmation.

Regards,
DriveTech Components
```

### Email 12 — Emergency Supply Confirmation

**Sender:** Pioneer Auto Systems  
**Subject:** Emergency Supply Confirmation  
**Status:** Read

```text
Hello,

We can reserve 400 Brake Pads for emergency procurement.

Delivery time is approximately 5 days.

Unit price: ₹136
Quality certification: Automotive Grade

Please confirm within 6 hours if you wish to reserve
this allocation.

Regards,
Pioneer Auto Systems
```

At least 10 emails are required; using all 12 is recommended.

---

# 7. Sent Section

Create a separate **Sent** section.

It must contain exactly **5 dummy sent emails**.

Of those:

> **4 must be sent by the AI AGENT.**

The fifth must be a normal human/company-sent email.

---

# 8. AI Agent Visual Treatment

AI Agent emails must be visually identifiable but still look professional.

Recommended:

```text
🤖 AI AGENT
Supply Chain Recovery Agent
```

Use a distinct text/accent color for:

- Sender
- AI AGENT label
- Optional small robot icon

Do not color the entire email body.

Normal company emails should use the standard text color.

---

# 9. Sent Email 1 — AI Agent

**Sender:** Supply Chain Recovery Agent  
**Recipient:** Apex Auto Parts  
**Subject:** Urgent ETA Confirmation – PO-7712

```text
Hello Apex Auto Parts,

We detected a production risk associated with the delayed
delivery of PO-7712.

Please confirm:

1. Current shipment status
2. Earliest achievable delivery date
3. Whether a partial shipment can be arranged
4. Quantity available for immediate dispatch

Please provide the updated information as soon as possible.

Regards,
Supply Chain Recovery Agent
AI Operations Controller
```

# 10. Sent Email 2 — AI Agent

**Sender:** Supply Chain Recovery Agent  
**Recipient:** PrimeDrive Components  
**Subject:** Urgent RFQ – Brake Pads

```text
Hello PrimeDrive Components,

We are evaluating emergency supply options for Brake Pads.

Please provide:

- Available quantity
- Unit price
- Earliest delivery date
- Minimum order quantity
- Quality certifications
- Expedited shipping availability
- Expedited shipping cost

Please treat this as an urgent procurement request.

Regards,
Supply Chain Recovery Agent
AI Operations Controller
```

# 11. Sent Email 3 — AI Agent

**Sender:** Supply Chain Recovery Agent  
**Recipient:** Vertex Components  
**Subject:** Emergency RFQ – Brake Pad Supply

```text
Hello Vertex Components,

We require an urgent quotation for Brake Pads.

Please confirm whether you can supply 600 units within
4 days.

Also provide the unit price and any expedited shipping
charges.

Regards,
Supply Chain Recovery Agent
AI Operations Controller
```

# 12. Sent Email 4 — AI Agent

**Sender:** Supply Chain Recovery Agent  
**Recipient:** DriveTech Components  
**Subject:** Availability Request – Emergency Brake Pad Supply

```text
Hello DriveTech Components,

We are evaluating a recovery plan for a high-priority
production order.

Please confirm your available Brake Pad quantity,
earliest delivery time, unit price, MOQ, and applicable
quality certifications.

If only partial quantity is available, please provide
the maximum quantity that can be dispatched immediately.

Regards,
Supply Chain Recovery Agent
AI Operations Controller
```

# 13. Sent Email 5 — Human / Normal

**Sender:** Procurement Operations  
**Recipient:** Apex Auto Parts  
**Subject:** PO-7712 – Delivery Follow-up

```text
Hello Apex Auto Parts,

Please keep our procurement team updated regarding the
revised delivery schedule for PO-7712.

We would appreciate confirmation once the shipment has
been picked up by the carrier.

Regards,
Procurement Operations
```

This email must NOT receive the AI Agent visual treatment.

---

# 14. Scenario Consistency

The Inbox should make the agent's scenarios understandable.

For the supplier-delay scenario:

```text
Supplier:
"Delivery delayed by 5 days."

        ↓

AI Agent:
"Please confirm revised ETA and partial shipment."

        ↓

Supplier:
"300 units available in 3 days."
```

The dashboard/audit trail can then show:

```text
✓ Delay detected
✓ Supplier contacted
✓ Partial shipment identified
✓ Alternate suppliers contacted
✓ Quotes compared
```

The Inbox itself only displays communications; it must not implement the agent's decision logic.

---

# 15. Adversarial Supplier Scenario

The Inbox should support the contradiction:

Supplier email:

> "PO-7712 has been dispatched."

Tracking system:

```text
Label created
No pickup
No movement
```

The UI should make both pieces of evidence easy to inspect.

The audit trail can then show:

```text
⚠ Supplier claim conflicts with tracking data

Supplier email:
"Shipment dispatched"

Tracking:
"Label created — no pickup"

Agent decision:
Do not rely on supplier ETA.
Continue alternate sourcing.
```

This is consistent with the documented adversarial supplier scenario.

---

# 16. Quality Scenario

The Inbox should also support:

```text
Nova Mobility Parts

Delivery: 3 days

Required certification: Automotive Grade
Supplier certification: Not available
```

The agent should be able to reject this option.

Do not implement the decision inside the Inbox.

---

# 17. Agent Email → Audit Trail Connection

The Inbox should make it possible for a judge to understand that an AI Agent email corresponds to an agent action.

Where appropriate, include subtle metadata such as:

```text
🤖 AI AGENT
Agent Run: RUN-84
Action: Supplier Communication
```

or:

```text
🤖 AI AGENT
Agent Run: RUN-84
Action: RFQ Request
```

If the existing agent event system already has run/action IDs, reuse them. Do not create competing IDs or modify the existing audit architecture.

---

# 18. Email Counts

Display realistic counts:

```text
Inbox       12
Starred      2
Sent         5
```

Unread emails should be visually distinguishable.

---

# 19. Responsive UI

Desktop is the primary target.

Use the existing application shell:

```text
Sidebar
   ↓
Inbox
   ↓
Toolbar
   ↓
Inbox / Sent
   ↓
Email list
   ↓
Email detail
```

Do not introduce a separate application shell.

Reuse existing components, typography, theme, spacing, buttons, cards, and icons wherever possible.

---

# 20. Do Not Overbuild

This is a simulated hackathon inbox.

Do NOT implement:

- Real Gmail authentication
- Gmail API
- OAuth
- Real supplier email accounts
- Real external email services
- Real email delivery
- Real-time external mail sync
- Real attachments
- Full Gmail composer

The goal is a convincing **enterprise simulation UI**.

---

# 21. Acceptance Criteria

### Sidebar

- [ ] Inbox appears in the sidebar.
- [ ] Inbox navigation works.
- [ ] Existing navigation remains unchanged.

### Inbox

- [ ] Gmail-style email list exists.
- [ ] At least 10 supplier/company emails are present.
- [ ] Emails are derived from the documented scenarios.
- [ ] Sender, subject, preview, and timestamp are visible.
- [ ] Read/unread state is visually distinguishable.
- [ ] Clicking an email opens its full content.

### Sent

- [ ] Sent section exists.
- [ ] Exactly 5 dummy sent emails exist.
- [ ] Exactly 4 are AI Agent emails.
- [ ] Exactly 1 is a normal human/company email.
- [ ] AI Agent emails have distinct text color and/or agent icon.
- [ ] Agent emails include original-supplier contact and alternate-supplier RFQ examples.

### Scenario coverage

- [ ] Supplier delay communication exists.
- [ ] Revised ETA communication exists.
- [ ] Partial shipment communication exists.
- [ ] Alternate supplier RFQs exist.
- [ ] Quality/certification communication exists.
- [ ] Tracking contradiction exists.
- [ ] Quantity limitation exists.
- [ ] Expedited shipping information exists.
- [ ] Emergency procurement communication exists.

### Existing system

- [ ] No database schema is changed.
- [ ] No existing IDs are changed.
- [ ] No foreign keys are changed.
- [ ] No agent logic is changed.
- [ ] No existing APIs are broken.
- [ ] No existing dashboard functionality is broken.
- [ ] No real emails are sent.

---

# 22. Final Design Principle

The Inbox is the **communication layer of the autonomous supply-chain agent**.

A judge should be able to:

1. Inject a disruption in Scenario Lab.
2. Watch the agent detect the issue.
3. Open Inbox.
4. See the supplier's incoming message.
5. See the AI Agent's outgoing email.
6. See supplier responses.
7. Return to Agent Activity.
8. Watch the agent compare options and make a recovery decision.
9. Open the audit trail and verify the sequence.

The final experience should communicate:

> **The AI agent doesn't just recommend what procurement should do. It communicates, gathers information, evaluates alternatives, and drives the simulated recovery workflow.**
