# Supply Chain Disruption Control Agent — Task Plan & Shared Contract

Scope for this build: a **simulated procurement & manufacturing backend** that raises the five alert types below, plus a **basic UI** with an audit trail, human escalation alerts (Approve/Reject), and a few data visualization graphs.

Tasks are listed **in order** — complete each one before starting the next, since each depends on what came before. This doc also fixes all API routes, table names, and field names up front so nothing needs renaming later.

---

## Alert types the backend must generate

| Alert type | Trigger condition |
|---|---|
| `po_delayed` | A purchase order's `expected_delivery` has passed (or status is manually set to `delayed`) while `status` is not `delivered`/`cancelled` |
| `inventory_below_safety_stock` | `usable_stock < safety_stock` for a component |
| `supplier_response_pending` | A message was sent to a supplier and no reply recorded after a configurable threshold (simulated) |
| `budget_approval_required` | An action's `estimated_cost` exceeds `approval_required_above` for that PO/component |
| `production_schedule_at_risk` | A production order's deadline is within N days AND the required component's current coverage (`usable_stock / daily_usage`) is less than days remaining |

These five map directly to what "existing systems" already show per the problem statement — this build's job is to detect and surface them reliably, then let a human act on the ones that need approval.

---

## Task list (sequential)

### Task 1 — Repo & Environment Setup
- [ ] `git init`, `.gitignore`, `.env.example`
- [ ] `docker-compose.yml` with `db` (Postgres), `backend` (FastAPI), `frontend` (React/Vite)
- [ ] Confirm `docker compose up` boots cleanly with a `/health` route on the backend and Vite dev server serving on the frontend
- [ ] `npm create vite@latest frontend -- --template react-ts`, `npm install axios react-router-dom recharts`

### Task 2 — Database Schema & Seed Data
- [ ] Create all tables from **Part 2.2** below via Alembic migration
- [ ] Seed data: 20–30 components, 10–15 suppliers, 20–30 purchase orders, 5–10 production orders, 10–15 supplier messages — include enough deliberately-bad data to trigger each of the 5 alert types at least twice (e.g. a couple of POs with past `expected_delivery`, a couple of components below `safety_stock`, one high-cost PO above threshold, one production order with a tight deadline and thin coverage)
- [ ] Seed script lives at `backend/app/seed/seed_data.py`, fixtures as JSON in `backend/app/seed/fixtures/`

### Task 3 — Core Data APIs
- [ ] Implement `GET /inventory`, `GET /inventory/{component_id}`
- [ ] Implement `GET /purchase-orders`, `GET /purchase-orders/{po_id}`, `PATCH /purchase-orders/{po_id}`
- [ ] Implement `GET /suppliers`
- [ ] Implement `GET /production-schedule`
- [ ] Implement `GET /supplier-messages` (simulated inbox/outbox for the `supplier_response_pending` check)

### Task 4 — Alert Engine
- [ ] Write one rule function per alert type in `backend/app/services/alert_rules.py` (`check_po_delayed()`, `check_inventory_below_safety_stock()`, `check_supplier_response_pending()`, `check_budget_approval_required()`, `check_production_schedule_at_risk()`)
- [ ] A scheduler/poll job (simple loop or `POST /alerts/scan` trigger for the demo) runs all five rules and writes new rows into `alerts` — never duplicate an open alert for the same entity + type
- [ ] Implement `GET /alerts`, `GET /alerts/{alert_id}`

### Task 5 — Escalation & Approval Backend
- [ ] Any alert with `requires_approval = true` (currently just `budget_approval_required`, but keep it a flag, not hardcoded) auto-creates a row in `escalations`
- [ ] Implement `GET /escalations`
- [ ] Implement `POST /escalations/{escalation_id}/resolve` with body `{ "decision": "approve" | "reject", "note": "..." }` — updates `escalations.status` and closes the linked alert

### Task 6 — Audit Trail Backend
- [ ] Every alert creation, every escalation creation, and every escalation resolution writes a row to `audit_log` (see schema in Part 2.2)
- [ ] Implement `GET /audit-log` (supports optional `entity_id` query filter)

### Task 7 — Frontend Setup & Basic Dashboard
- [ ] App shell, routing (`/dashboard`, `/escalations`, `/audit-log`)
- [ ] Dashboard page lists all open alerts grouped by type, with severity coloring

### Task 8 — Escalation UI (Approve / Reject)
- [ ] Escalations page lists pending escalations with the alert context (cost, entity, reason)
- [ ] Each row has **Approve** and **Reject** buttons calling `POST /escalations/{id}/resolve`
- [ ] Resolved escalations move out of the pending list and show their outcome

### Task 9 — Audit Trail Viewer UI
- [ ] Table/timeline view of `audit-log`, filterable by entity
- [ ] Each row shows event type, actor, before/after, timestamp

### Task 10 — Data Visualization Graphs
- [ ] Bar chart: open alerts by type (from `GET /alerts`)
- [ ] Line chart: inventory usable_stock vs safety_stock for at-risk components
- [ ] Pie/donut: escalation outcomes (approved vs rejected vs pending)
- [ ] Use `recharts`, data fetched through `frontend/src/api/`

### Task 11 — Polish & Demo Prep
- [ ] Walk through the full flow once: seed → alerts generated → escalation appears → approve/reject → audit trail reflects it → graphs update
- [ ] Fix rough edges in the UI, write a short README section on how to run the demo

---

## Part 2 — Frozen contract

### 2.1 Naming conventions

| Context | Convention | Example |
|---|---|---|
| DB tables & columns | `snake_case`, plural table names | `purchase_orders`, `usable_stock` |
| Python variables/functions | `snake_case` | `check_inventory_below_safety_stock()` |
| Pydantic schema classes | `PascalCase` | `AlertOut`, `EscalationResolveRequest` |
| API JSON fields | `snake_case`, same as DB — no translation layer | `expected_delivery`, `requires_approval` |
| API routes | `snake_case`/kebab, plural nouns | `/purchase-orders`, `/audit-log` |
| React components | `PascalCase.tsx` | `EscalationQueue.tsx` |
| React variables/props | `camelCase` (converted only at the `frontend/src/api/` fetch boundary) | `expectedDelivery` |
| Env vars | `UPPER_SNAKE_CASE` | `DATABASE_URL` |
| Git branches | `feature/<short-desc>` | `feature/alert-engine` |
| Commit messages | Conventional commits | `feat(alerts): add inventory safety stock rule` |

**Never rename a field once Task 2 is done.** Add a new field instead of repurposing one.

### 2.2 Database schema

```
components
- component_id        text PK        e.g. "COMP-104"
- name                text
- current_stock       int
- usable_stock        int
- daily_usage         int
- safety_stock        int
- warehouse           text
- last_updated        timestamptz

purchase_orders
- po_id                    text PK    e.g. "PO-7712"
- component_id             text FK -> components
- supplier_id              text FK -> suppliers
- quantity                 int
- expected_delivery        date
- status                   text       in_transit | delayed | delivered | cancelled
- unit_price                numeric
- total_value               numeric
- approval_required_above   numeric
- version                   int        -- optimistic concurrency

suppliers
- supplier_id         text PK    e.g. "SUP-42"
- supplier_name       text
- component_id        text FK -> components
- unit_price          numeric
- lead_time_days      int
- available_quantity  int
- quality_score       numeric
- reliability_score   numeric
- min_order_quantity  int
- certifications      text[]

production_orders
- production_order_id         text PK   e.g. "PROD-882"
- product                     text
- required_component          text FK -> components
- units_planned                int
- component_required_per_unit  int
- deadline                     date
- priority                     text     low | medium | high

supplier_messages
- message_id      uuid PK
- supplier_id     text FK -> suppliers
- direction       text        outbound | inbound
- subject         text
- body            text
- sent_at         timestamptz
- responded_at    timestamptz nullable

alerts
- alert_id          uuid PK
- type              text        po_delayed | inventory_below_safety_stock | supplier_response_pending | budget_approval_required | production_schedule_at_risk
- entity_type       text        purchase_order | component | supplier | production_order
- entity_id         text
- severity          text        low | medium | high
- message           text
- requires_approval boolean
- status            text        open | acknowledged | resolved
- created_at        timestamptz

escalations
- escalation_id   uuid PK
- alert_id        uuid FK -> alerts
- brief           text
- cost_delta      numeric nullable
- status          text     pending | approved | rejected
- resolved_by     text nullable
- resolved_at     timestamptz nullable
- created_at      timestamptz

audit_log
- audit_id     uuid PK
- event_type   text       alert_generated | escalation_created | escalation_resolved
- entity_type  text
- entity_id    text
- actor        text nullable   -- null for system-generated events
- before       jsonb nullable
- after        jsonb nullable
- ts           timestamptz
```

### 2.3 API routes

| Method | Path | Notes |
|---|---|---|
| GET | `/inventory` | `list[InventoryOut]` |
| GET | `/inventory/{component_id}` | `InventoryOut` |
| GET | `/purchase-orders` | `list[PurchaseOrderOut]` |
| GET | `/purchase-orders/{po_id}` | `PurchaseOrderOut` |
| PATCH | `/purchase-orders/{po_id}` | body includes `version` for optimistic concurrency |
| GET | `/suppliers` | `list[SupplierOut]` |
| GET | `/production-schedule` | `list[ProductionOrderOut]` |
| GET | `/supplier-messages` | `list[SupplierMessageOut]` |
| POST | `/alerts/scan` | runs all 5 alert rules, returns newly created alerts |
| GET | `/alerts` | optional query `status`, `type` |
| GET | `/alerts/{alert_id}` | `AlertOut` |
| GET | `/escalations` | optional query `status` |
| POST | `/escalations/{escalation_id}/resolve` | body: `{ "decision": "approve" \| "reject", "note": "..." }` |
| GET | `/audit-log` | optional query `entity_id` |

### 2.4 Key response shapes

```json
// AlertOut
{
  "alert_id": "uuid",
  "type": "budget_approval_required",
  "entity_type": "purchase_order",
  "entity_id": "PO-7712",
  "severity": "high",
  "message": "Estimated cost 168000 exceeds approval threshold 150000",
  "requires_approval": true,
  "status": "open",
  "created_at": "2026-09-01T10:00:00Z"
}
```

```json
// EscalationOut
{
  "escalation_id": "uuid",
  "alert_id": "uuid",
  "brief": "PO-7712 replacement cost exceeds threshold by 18000",
  "cost_delta": 18000,
  "status": "pending",
  "resolved_by": null,
  "resolved_at": null,
  "created_at": "2026-09-01T10:05:00Z"
}
```

```json
// AuditLogOut
{
  "audit_id": "uuid",
  "event_type": "escalation_resolved",
  "entity_type": "purchase_order",
  "entity_id": "PO-7712",
  "actor": "head_of_procurement",
  "before": { "status": "pending" },
  "after": { "status": "approved" },
  "ts": "2026-09-01T11:00:00Z"
}
```

### 2.5 Error format (all routes)
```json
{ "error": "short_code", "message": "human readable", "detail": {} }
```
