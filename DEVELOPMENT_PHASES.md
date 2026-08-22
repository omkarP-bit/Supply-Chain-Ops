# Development by Phase

## Development Strategy

Build vertically rather than building every database table, agent, and
UI screen independently.

Each phase should produce a working increment that can be demonstrated.

Priority:

``` text
Time to Build
     ↓
Reliability
     ↓
Judging Impact
     ↓
Complexity
```

------------------------------------------------------------------------

# Phase 0 --- Project Setup

## Goal

Create the runnable development environment.

### Tasks

-   [ ] Create Git repository.
-   [ ] Create `backend/`.
-   [ ] Create `frontend/`.
-   [ ] Create `docker-compose.yml`.
-   [ ] Add PostgreSQL container.
-   [ ] Add FastAPI container.
-   [ ] Add React container.
-   [ ] Configure `.env`.
-   [ ] Add `.env.example`.
-   [ ] Add `.gitignore`.
-   [ ] Add README.
-   [ ] Add health endpoints.
-   [ ] Add Docker health checks.

### Expected result

``` text
docker compose up
```

starts:

``` text
React
FastAPI
PostgreSQL
```

and:

``` text
GET /health
```

returns success.

------------------------------------------------------------------------

# Phase 1 --- Database Foundation

## Goal

Build the operational source of truth.

### Tables

Implement first:

-   [ ] materials
-   [ ] material_specifications
-   [ ] material_spec_parameters
-   [ ] suppliers
-   [ ] supplier_materials
-   [ ] inventory_snapshots
-   [ ] inventory_movements
-   [ ] production_orders
-   [ ] production_consumption

Then:

-   [ ] purchase_orders
-   [ ] shipments
-   \[supplier_communications\]
-   \[supplier_quotes\]
-   [ ] supplier_performance
-   [ ] risk_thresholds
-   [ ] recovery_plans
-   [ ] approval_requests
-   [ ] inventory_pricing_adjustments
-   [ ] audit_events

### Tasks

-   [ ] SQLAlchemy models.
-   [ ] Alembic migrations.
-   [ ] Foreign keys.
-   [ ] Unique constraints.
-   [ ] Check constraints where appropriate.
-   [ ] Timestamps.
-   [ ] Seed data.

### Seed data must include

At minimum:

``` text
COMP-104
SUP-21
SUP-34
SUP-41
PO-7712
Multiple production orders
30+ days inventory history
30+ days consumption history
Supplier specifications
Supplier certifications
Supplier stock
Supplier prices
Supplier performance
Shipment tracking states
```

------------------------------------------------------------------------

# Phase 2 --- PostgreSQL Performance

## Goal

Make supplier discovery deterministic and fast.

### Partial indexes

Implement:

``` sql
CREATE INDEX idx_supplier_material_available
ON supplier_materials (material_id, available_quantity)
WHERE available_quantity > 0;
```

``` sql
CREATE INDEX idx_supplier_certification_valid
ON supplier_materials (material_id, supplier_id)
WHERE certification_valid = TRUE;
```

``` sql
CREATE INDEX idx_active_suppliers
ON suppliers (supplier_id)
WHERE status = 'ACTIVE';
```

``` sql
CREATE INDEX idx_eligible_supplier_material
ON supplier_materials (material_id, supplier_id)
WHERE available_quantity > 0
  AND certification_valid = TRUE;
```

### Tasks

-   [ ] Add indexes.
-   [ ] Write representative supplier queries.
-   [ ] Run `EXPLAIN ANALYZE`.
-   [ ] Confirm expected index usage.
-   [ ] Add only indexes supported by actual query patterns.

### Expected result

Supplier eligibility can be retrieved quickly using PostgreSQL rather
than an LLM search process.

------------------------------------------------------------------------

# Phase 3 --- Operational Risk Engine

## Goal

Replace the old Inventory Agent and Disruption Analysis Agent with one
deterministic engine.

### Implement

``` text
OperationalRiskEngine
```

### Functions

``` python
get_current_inventory()
calculate_average_consumption_30d()
calculate_average_consumption_7d()
calculate_inventory_coverage()
calculate_inventory_discrepancy()
find_affected_production_orders()
calculate_hours_to_production_stop()
evaluate_thresholds()
calculate_risk()
```

### Example

``` text
ERP stock = 800
Physical stock = 390
Average consumption = 90/day

Coverage = 390 / 90
         = 4.33 days
```

### Output

Use structured Pydantic models:

``` json
{
  "material_id": "COMP-104",
  "risk_level": "CRITICAL",
  "usable_stock": 390,
  "coverage_days": 4.33,
  "inventory_discrepancy": true,
  "affected_orders": ["PROD-882"]
}
```

### Tests

-   [ ] Normal inventory.
-   [ ] Low inventory.
-   [ ] Stale inventory.
-   [ ] High consumption trend.
-   [ ] Production-stop scenario.
-   [ ] Supplier delay longer than inventory coverage.

------------------------------------------------------------------------

# Phase 4 --- Supplier Evaluation Engine

## Goal

Build deterministic supplier matching.

### Pipeline

``` text
Material Requirement
       |
       v
Active Supplier Filter
       |
       v
Stock Filter
       |
       v
Certification Filter
       |
       v
AQL Filter
       |
       v
Material Grade Filter
       |
       v
Specification Filter
       |
       v
Lead-Time Filter
       |
       v
MOQ Filter
       |
       v
Eligible Suppliers
```

### Implement

``` python
get_supplier_candidates()
check_stock()
check_certification()
check_aql()
check_material_grade()
check_specification_match()
check_lead_time()
check_moq()
calculate_supplier_score()
```

### Supplier score

Initial weights:

``` text
Quality               30%
Delivery reliability  25%
Availability          20%
Price                 15%
Lead time             10%
```

Make weights configurable.

### Tests

-   [ ] Cheap but uncertified supplier.
-   [ ] Certified supplier.
-   [ ] Insufficient stock.
-   [ ] Invalid AQL.
-   [ ] Expired certification.
-   [ ] Wrong material grade.
-   [ ] Cannot meet deadline.
-   [ ] Valid supplier with higher price.

------------------------------------------------------------------------

# Phase 5 --- Recovery & Recommendation Agent

## Goal

Implement the single LLM agent that combines recommendation and recovery
planning.

### Input

Only verified structured information:

``` text
Incident
Risk report
Eligible suppliers
Supplier scores
Inventory state
Production impact
Budget constraints
```

### Agent responsibilities

-   [ ] Compare eligible suppliers.
-   [ ] Explain trade-offs.
-   [ ] Recommend supplier.
-   [ ] Generate multiple recovery plans.
-   [ ] Consider split sourcing.
-   [ ] Consider partial shipment.
-   [ ] Consider existing stock.
-   [ ] Consider damaged-stock pricing.
-   [ ] Consider production rescheduling.

### Example plans

``` text
Plan A:
800 units from SUP-34

Plan B:
600 units from SUP-34
200 units from SUP-41

Plan C:
Use existing usable stock
+
400 units from SUP-34
+
reschedule low-priority production
```

### Important

The LLM must not:

-   Execute SQL.
-   Decide certification validity.
-   Override AQL.
-   Override inventory constraints.
-   Create a PO directly.
-   Bypass human approval.

------------------------------------------------------------------------

# Phase 6 --- Plan Validation Engine

## Goal

Prove that an LLM-generated plan is actually feasible.

### Validate

-   [ ] Quantity availability.
-   [ ] Certification.
-   [ ] Material specification.
-   [ ] AQL.
-   [ ] Lead time.
-   [ ] Production deadline.
-   [ ] Budget.
-   [ ] MOQ.
-   [ ] Supplier status.
-   [ ] Inventory impact.

### Output

``` json
{
  "valid": true,
  "violations": [],
  "warnings": []
}
```

If invalid:

``` json
{
  "valid": false,
  "violations": [
    "SUP-41 cannot deliver 800 units before production deadline"
  ]
}
```

------------------------------------------------------------------------

# Phase 7 --- What-if Simulation

## Goal

Compare recovery plans before presenting them for approval.

### Simulate

-   [ ] Inventory after recovery.
-   [ ] Production coverage.
-   [ ] Delivery date.
-   [ ] Production stop.
-   [ ] Partial shipments.
-   [ ] Split sourcing.
-   [ ] Rescheduling.
-   [ ] Total cost.
-   [ ] Remaining risk.

### Example output

``` text
Plan A
Cost: ₹96,000
Delivery: 2.5 days
Production impact: 0 hours
Risk: LOW

Plan B
Cost: ₹89,000
Delivery: 4 days
Production impact: 3 hours
Risk: MEDIUM
```

The simulation is deterministic.

------------------------------------------------------------------------

# Phase 8 --- Human Approval Workflow

## Goal

Make human authorization mandatory.

### Approval UI

Show:

-   [ ] Incident summary.
-   [ ] Risk severity.
-   [ ] Inventory evidence.
-   [ ] Production impact.
-   [ ] Supplier comparison.
-   [ ] Quality/certification evidence.
-   [ ] Cost.
-   [ ] Delivery time.
-   [ ] Alternatives.
-   [ ] Risk of no action.
-   [ ] Recommended plan.
-   [ ] Simulation result.

### Actions

``` text
APPROVE
REJECT
REQUEST MODIFICATION
```

### Security rule

No execution endpoint works unless:

``` text
approval.status == APPROVED
```

------------------------------------------------------------------------

# Phase 9 --- Deterministic Execution Layer

## Goal

Execute only approved actions.

For the hackathon, use a mock ERP/procurement service if a real ERP is
unavailable.

### Tools

``` python
create_purchase_order()
update_purchase_order()
reserve_inventory()
create_partial_order()
split_purchase_order()
reschedule_production()
update_risk_status()
```

### Security

Each tool must:

-   Validate Pydantic input.
-   Verify authorization.
-   Verify approval.
-   Verify current database state.
-   Perform one specific operation.
-   Create an audit event.

Never expose arbitrary SQL or arbitrary code execution to the LLM.

------------------------------------------------------------------------

# Phase 10 --- Verification & Replanning Agent

## Goal

Close the feedback loop.

### After execution

Deterministic services collect:

``` text
PO status
Shipment status
Inventory
Production status
```

The Verification Agent receives structured results and determines
whether another workflow is necessary.

### Example

``` text
Expected:
600 units dispatched

Actual:
200 units dispatched

       |
       v

Verification
       |
       v

Recovery objective not achieved
       |
       v

Trigger replanning
```

------------------------------------------------------------------------

# Phase 11 --- React Control Tower

## Goal

Create the judging/demo interface.

### Dashboard

Show:

-   Active incidents.
-   Risk levels.
-   Production-at-risk.
-   Inventory coverage.
-   Pending approvals.
-   Recovery status.

### Incident Details

Show:

-   Incident.
-   Timeline.
-   Inventory state.
-   Production impact.
-   Supplier evidence.
-   Risk calculation.
-   Recovery plans.

### Supplier Comparison

Columns:

``` text
Supplier
Available stock
Price
Lead time
AQL
Certification
Quality
Reliability
Score
```

### Approval Queue

Show:

``` text
Incident
Recommended plan
Cost
Risk
Production impact
Alternatives
Approve / Reject
```

### Audit Trail

Show every important event chronologically.

------------------------------------------------------------------------

# Phase 12 --- Scenario Testing

Implement six deterministic demo scenarios.

## Scenario 1

Supplier delays PO by 5 days.

Expected:

``` text
Detect disruption
→ Calculate coverage
→ Identify affected production
→ Find alternatives
→ Generate recovery plan
→ Validate
→ Simulate
→ Human approval
→ Execute
→ Verify
```

## Scenario 2

ERP = 800, usable = 390.

Expected:

``` text
Detect discrepancy
→ Recalculate coverage
→ Increase risk
→ Replan
→ Audit
```

## Scenario 3

Supplier claims dispatched.

Tracking says label created.

Expected:

``` text
Detect mismatch
→ Increase supplier risk
→ Do not trust claim
→ Continue alternate sourcing
```

## Scenario 4

Cheapest supplier fails certification.

Expected:

``` text
Supplier rejected deterministically
→ Certified supplier preferred
```

## Scenario 5

Recovery cost exceeds threshold.

Expected:

``` text
Approval request
→ No execution before approval
```

## Scenario 6

Production stops in 12 hours.

Expected:

``` text
Prioritize critical production
→ Partial/split sourcing
→ Rescheduling alternatives
→ Simulation
→ Human approval
→ Execution
```

------------------------------------------------------------------------

# Phase 13 --- Security & Reliability

## Security checklist

-   [ ] No arbitrary SQL from LLM.
-   [ ] Tool allowlist.
-   [ ] Pydantic validation.
-   [ ] Role-based approval.
-   [ ] Every workflow requires approval.
-   [ ] Execution checks approval state.
-   [ ] Audit all state-changing operations.
-   [ ] Secrets only through environment variables.
-   [ ] Database credentials not exposed to frontend.
-   [ ] CORS configured.
-   [ ] SQLAlchemy parameterized queries.

## Reliability checklist

-   [ ] Database transactions.
-   [ ] Idempotent execution operations.
-   [ ] Workflow state persisted.
-   [ ] Failed execution recorded.
-   [ ] Retry only safe/idempotent operations.
-   [ ] Simulation before approval.
-   [ ] Verification after execution.

------------------------------------------------------------------------

# Phase 14 --- Demo Optimization

## Goal

Make the architecture understandable in under two minutes.

### Demo sequence

1.  Start with a supplier disruption.
2.  Show inventory coverage.
3.  Show production impact.
4.  Show supplier candidates.
5.  Show why invalid suppliers were rejected.
6.  Show Recovery & Recommendation Agent.
7.  Show multiple recovery plans.
8.  Show deterministic validation.
9.  Show simulation.
10. Show human approval.
11. Approve.
12. Show deterministic execution.
13. Show verification.
14. Show audit trail.

### Key message

> **AI recommends. Deterministic systems verify. Humans authorize.
> Systems execute.**

------------------------------------------------------------------------

# Phase 15 --- Final Hardening

-   [ ] Run all six scenarios repeatedly.
-   [ ] Test invalid inputs.
-   [ ] Test supplier data inconsistencies.
-   [ ] Test stale inventory.
-   [ ] Test approval bypass attempts.
-   [ ] Test duplicate execution.
-   [ ] Test failed execution.
-   [ ] Test rejected approval.
-   [ ] Test replanning.
-   [ ] Test database restart.
-   [ ] Test Docker restart.
-   [ ] Verify audit trail.
-   [ ] Verify partial-index performance.
-   [ ] Remove unnecessary LLM calls.
-   [ ] Remove unused dependencies.
-   [ ] Prepare seeded demo database.
-   [ ] Prepare final architecture diagram.
-   [ ] Prepare 3-minute and 7-minute demos.

------------------------------------------------------------------------

# Final Build Order

If time becomes limited, follow this exact priority:

``` text
1. Docker + PostgreSQL + FastAPI
        ↓
2. Schema + seed data
        ↓
3. Inventory/Risk Engine
        ↓
4. Supplier Evaluation Engine
        ↓
5. Partial indexes + query optimization
        ↓
6. Recovery & Recommendation Agent
        ↓
7. Validation + Simulation
        ↓
8. Human Approval
        ↓
9. Deterministic Execution
        ↓
10. Verification/Replanning
        ↓
11. React Control Tower
        ↓
12. Scenario polish
        ↓
13. Security + demo hardening
```

Do not start with the frontend or LLM agents. The deterministic database
and decision layer is the foundation of the project.
