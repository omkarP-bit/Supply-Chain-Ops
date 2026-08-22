# Autonomous Supply Chain Recovery System

## 1. Project Overview

This project is an AI-assisted supply-chain disruption management
platform that detects operational risk, evaluates feasible suppliers,
generates recovery recommendations, validates them deterministically,
and requires human approval before any workflow is executed.

The core design principle is:

> **LLMs recommend and reason. Deterministic services establish
> operational truth. Humans authorize. Deterministic tools execute.**

The system is intentionally designed without LLMs for inventory
calculations, disruption detection, supplier eligibility, specification
matching, pricing calculations, threshold evaluation, or database truth.

------------------------------------------------------------------------

## 2. Problem

Supply-chain disruptions can cause production stoppages when:

-   A supplier delays a purchase order.
-   ERP inventory is stale or incorrect.
-   A supplier makes an unreliable shipment claim.
-   An alternate supplier does not satisfy quality/certification
    requirements.
-   Recovery procurement exceeds an approval threshold.
-   A production line is close to stopping and partial sourcing or
    rescheduling is required.

The system must detect the impact, find feasible recovery options,
explain the recommendation, and keep a human in the approval loop.

------------------------------------------------------------------------

## 3. Goals

### Primary goals

1.  Detect inventory and disruption risk using deterministic rules.
2.  Calculate production coverage from historical consumption.
3.  Detect stale or inconsistent inventory.
4.  Verify supplier claims against shipment/tracking data.
5.  Filter suppliers using hard requirements.
6.  Compare eligible suppliers using configurable scoring.
7.  Generate recovery plans such as:
    -   Single supplier sourcing.
    -   Split sourcing.
    -   Partial shipment.
    -   Existing-stock adjustment.
    -   Production rescheduling.
8.  Require human approval for every workflow.
9.  Execute only approved actions.
10. Record a complete audit trail.

### Non-goals

-   Fully autonomous procurement.
-   LLM-based database truth.
-   LLM-based inventory calculations.
-   Vector databases/RAG for structured operational data.
-   Kafka-based event infrastructure in the MVP.
-   Microservice-heavy deployment.

------------------------------------------------------------------------

# 4. Architecture

``` text
                         React Frontend
                               |
                               v
                         FastAPI Backend
                               |
                               v
                     Supervisor Agent (LLM)
                               |
              +----------------+----------------+
              |                                 |
              v                                 v
     Operational Risk Engine          Supplier Evaluation Engine
          Python + SQL                     Python + SQL
              |                                 |
              |                         Supplier capabilities
              |                         specifications
              |                         certifications
              |                         prices
              |                         stock
              |                         lead time
              |                         reliability
              |                                 |
              +----------------+----------------+
                               |
                               v
                  Recovery & Recommendation Agent
                              (LLM)
                               |
                               v
                     Plan Validation Engine
                          Python + SQL
                               |
                               v
                       What-if Simulation
                          Python + SQL
                               |
                               v
                        Human Approval
                         React UI
                               |
                    +----------+----------+
                    |                     |
                 APPROVE                REJECT
                    |                     |
                    v                     v
             Deterministic ERP       Replan / Modify
             / PO Tool Layer              |
                    |                     |
                    +----------+----------+
                               |
                               v
                    Verification & Replanning
                              Agent
                              (LLM)
                               |
                         Reality Check
                          /        \
                       PASS        FAIL
                        |            |
                       END        Replan
```

------------------------------------------------------------------------

# 5. LLM Agents

## 5.1 Supervisor Agent

### Responsibility

-   Understand the incoming incident.
-   Start the appropriate workflow.
-   Coordinate deterministic engines and the recovery agent.
-   Maintain workflow state.
-   Never directly modify the database or ERP.

### Input

-   Incident details.
-   Supplier communication when applicable.
-   Current workflow state.

### Output

A structured workflow command.

Example:

``` json
{
  "workflow": "SUPPLY_DISRUPTION",
  "material_id": "COMP-104",
  "po_id": "PO-7712"
}
```

------------------------------------------------------------------------

## 5.2 Recovery & Recommendation Agent

This combines the former Recommendation Agent and Procurement/Recovery
Agent.

### Responsibility

-   Compare already-validated supplier options.
-   Recommend the best supplier or supplier combination.
-   Generate recovery strategies.
-   Consider:
    -   Single supplier sourcing.
    -   Split sourcing.
    -   Partial shipment.
    -   Alternate suppliers.
    -   Existing usable stock.
    -   Damaged-stock pricing adjustments.
    -   Production rescheduling.
-   Explain why the recommendation is preferred.

### Critical rule

The agent does **not** decide whether a supplier is eligible.

The deterministic Supplier Evaluation Engine performs hard filtering
first.

Example:

``` text
SUP-21 -> REJECTED: invalid certification
SUP-34 -> ELIGIBLE
SUP-41 -> ELIGIBLE
SUP-52 -> REJECTED: insufficient available stock
```

The LLM receives only the validated candidates.

------------------------------------------------------------------------

## 5.3 Verification & Replanning Agent

### Responsibility

-   Interpret post-execution results.
-   Check whether the approved recovery plan achieved its objective.
-   Detect failed assumptions.
-   Trigger another recovery cycle when required.
-   Explain the reason for replanning.

All actual status values come from deterministic systems.

------------------------------------------------------------------------

# 6. Deterministic Engines

## 6.1 Operational Risk Engine

No LLM.

Queries PostgreSQL and calculates:

-   Current usable inventory.
-   30-day average stock.
-   30-day average daily consumption.
-   7-day consumption trend.
-   Days of production coverage.
-   Inventory discrepancy percentage.
-   Production orders affected.
-   Hours until production stop.
-   Supplier delay versus available coverage.

Example:

``` text
usable_stock = 390
avg_daily_consumption_30d = 90

coverage_days = 390 / 90
               = 4.33 days
```

------------------------------------------------------------------------

## 6.2 Supplier Evaluation Engine

No LLM.

Performs:

1.  Hard constraint filtering.
2.  Supplier capability matching.
3.  Specification matching.
4.  Certification validation.
5.  Stock availability validation.
6.  Lead-time feasibility.
7.  AQL validation.
8.  MOQ validation.
9.  Supplier score calculation.

### Hard constraints

A supplier is rejected if:

-   Required stock is unavailable.
-   Required certification is missing/expired.
-   Material grade is incompatible.
-   Mandatory product specification is incompatible.
-   AQL is worse than the required level.
-   Lead time cannot satisfy the recovery deadline.
-   MOQ makes the order infeasible.
-   Supplier is inactive.

------------------------------------------------------------------------

## 6.3 Plan Validation Engine

No LLM.

Checks whether a generated recovery plan is operationally valid.

Example checks:

``` text
required_quantity <= supplier_available_stock
delivery_date <= production_deadline
supplier_certification = valid
material_specification = compatible
total_cost is calculable
production impact is within constraints
```

------------------------------------------------------------------------

## 6.4 What-if Simulation Engine

No LLM.

Simulates:

-   Supplier delay.
-   Partial delivery.
-   Split sourcing.
-   Production rescheduling.
-   Inventory consumption.
-   Production stop time.
-   Recovery cost.
-   Delivery deadline.

The simulation determines whether a proposed plan actually works.

------------------------------------------------------------------------

## 6.5 Pricing Adjustment Engine

No LLM.

Used when existing stock is damaged or degraded but still technically
usable.

Flow:

``` text
Damaged Stock
      |
      v
Quality/Safety Validation
      |
   usable?
    /   \
  NO    YES
  |       |
Reject   Pricing Adjustment
             |
             v
       Recommendation
```

Never use price reduction to bypass quality or safety constraints.

------------------------------------------------------------------------

# 7. Database

## Database technology

-   PostgreSQL.
-   Run PostgreSQL in Docker.
-   Use SQLAlchemy 2.x / asyncpg from FastAPI.
-   Alembic for migrations.

## Core tables

### `materials`

``` text
material_id PK
material_code
material_name
category
unit_of_measure
criticality_level
required_quality_level
required_certification
safety_stock
reorder_point
lead_time_target_days
created_at
updated_at
```

### `material_specifications`

``` text
specification_id PK
material_id FK
material_grade
material_type
dimensions
dimension_tolerance
weight
weight_tolerance
density
surface_finish
color
chemical_composition
mechanical_properties
aql_level
inspection_standard
required_certifications
special_requirements
effective_from
effective_until
```

### `material_spec_parameters`

``` text
parameter_id PK
specification_id FK
parameter_name
parameter_type
target_value
min_value
max_value
unit
tolerance
mandatory
```

This supports exact product specifications and measurable requirements.

------------------------------------------------------------------------

### `inventory_snapshots`

``` text
snapshot_id PK
material_id FK
warehouse_id
snapshot_date
erp_quantity
physical_quantity
usable_quantity
reserved_quantity
damaged_quantity
blocked_quantity
in_transit_quantity
available_quantity
source
created_at
```

Store daily history so deterministic 30-day baselines can be calculated.

------------------------------------------------------------------------

### `inventory_movements`

``` text
movement_id PK
material_id FK
warehouse_id
movement_type
quantity
reference_type
reference_id
movement_timestamp
source_system
reason
```

Movement types:

``` text
RECEIPT
CONSUMPTION
TRANSFER
ADJUSTMENT
DAMAGE
RESERVATION
RELEASE
RETURN
```

------------------------------------------------------------------------

### `production_orders`

``` text
production_order_id PK
product_id
priority
status
planned_quantity
completed_quantity
remaining_quantity
planned_start
planned_end
production_rate_per_hour
line_id
customer_order_id
created_at
updated_at
```

------------------------------------------------------------------------

### `production_consumption`

``` text
consumption_id PK
production_order_id FK
material_id FK
quantity_consumed
consumption_timestamp
planned_quantity
actual_quantity
unit
```

------------------------------------------------------------------------

### `suppliers`

``` text
supplier_id PK
supplier_code
supplier_name
status
location
contact_details
overall_reliability_score
on_time_delivery_rate
quality_score
average_lead_time_days
payment_terms
risk_level
created_at
updated_at
```

------------------------------------------------------------------------

### `supplier_materials`

This is the central supplier capability table.

``` text
supplier_material_id PK
supplier_id FK
material_id FK
available_quantity
reserved_quantity
available_to_promise
unit_price
currency
minimum_order_quantity
maximum_order_quantity
lead_time_days
expedited_lead_time_days
quality_grade
aql_level
inspection_standard
material_grade
material_specification
measurement_tolerance
certification_required
certification_valid
certification_expiry
batch_size
production_capacity
last_updated
```

------------------------------------------------------------------------

### `purchase_orders`

``` text
po_id PK
po_number
supplier_id FK
material_id FK
ordered_quantity
received_quantity
remaining_quantity
unit_price
total_cost
order_date
expected_delivery_date
actual_delivery_date
status
priority
production_order_id
created_by
updated_at
```

------------------------------------------------------------------------

### `shipments`

``` text
shipment_id PK
po_id FK
tracking_number
shipment_status
label_created_at
pickup_at
dispatch_at
estimated_delivery
actual_delivery
carrier
last_tracking_update
tracking_location
tracking_source
```

Possible statuses:

``` text
LABEL_CREATED
PICKUP_PENDING
PICKED_UP
IN_TRANSIT
OUT_FOR_DELIVERY
DELIVERED
CANCELLED
```

------------------------------------------------------------------------

### `supplier_communications`

``` text
communication_id PK
supplier_id FK
po_id FK
message_type
message_text
claimed_status
claimed_quantity
claimed_eta
claimed_dispatch_time
received_at
channel
processed_at
```

The LLM can extract a supplier claim, but deterministic tracking data
verifies it.

------------------------------------------------------------------------

### `supplier_quotes`

``` text
quote_id PK
supplier_id FK
material_id FK
quantity
unit_price
total_price
lead_time_days
delivery_date
quality_score
certification_level
certification_valid
minimum_order_quantity
quote_expiry
availability
received_at
```

------------------------------------------------------------------------

### `supplier_performance`

``` text
performance_id PK
supplier_id FK
evaluation_date
orders_completed
orders_on_time
orders_late
average_delay_days
quality_rejection_rate
eta_change_count
claim_mismatch_count
tracking_discrepancy_count
average_response_time
reliability_score
quality_score
```

------------------------------------------------------------------------

### `risk_thresholds`

``` text
threshold_id PK
material_id FK NULL
metric_name
warning_threshold
critical_threshold
unit
comparison_operator
severity
active
effective_from
effective_until
```

Metrics:

``` text
inventory_coverage_days
inventory_discrepancy_percentage
supplier_delay_days
supplier_reliability_score
quality_rejection_rate
budget_percentage
production_hours_to_stop
delivery_delay_days
```

------------------------------------------------------------------------

### `inventory_pricing_adjustments`

``` text
adjustment_id PK
material_id FK
supplier_id FK NULL
batch_id
original_unit_price
damage_percentage
quality_degradation
adjusted_unit_price
adjustment_percentage
reason
calculation_method
valid_from
valid_until
approved_by
approval_status
created_at
```

------------------------------------------------------------------------

### `recovery_plans`

``` text
plan_id PK
incident_id FK
plan_name
plan_type
estimated_cost
estimated_delivery_days
production_impact_hours
supplier_risk_score
quality_score
robustness_score
overall_score
status
selected
created_at
```

------------------------------------------------------------------------

### `approval_requests`

``` text
approval_id PK
incident_id FK
plan_id FK
requested_amount
approval_threshold
production_impact
risk_if_rejected
alternatives_considered
requested_at
status
approved_by
decision_at
decision_reason
```

Every workflow must create an approval request before execution.

------------------------------------------------------------------------

### `audit_events`

``` text
event_id PK
incident_id FK
agent_name
event_type
action
input_data JSONB
output_data JSONB
reason
risk_level
timestamp
correlation_id
```

------------------------------------------------------------------------

# 8. PostgreSQL Partial Indexing

Use partial indexes for the high-frequency supplier eligibility queries.

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

Use `EXPLAIN ANALYZE` to verify that PostgreSQL actually uses the
indexes.

Do not add indexes blindly. Index the actual query patterns.

------------------------------------------------------------------------

# 9. Important Deterministic Metrics

## Inventory coverage

``` text
coverage_days =
usable_quantity / average_daily_consumption
```

Use:

-   30-day average as baseline.
-   7-day average to detect recent demand acceleration.
-   Current usable quantity for real-time state.

## Inventory discrepancy

``` text
discrepancy_percentage =
abs(erp_quantity - physical_quantity)
/
erp_quantity
* 100
```

## Supplier reliability

``` text
on_time_delivery_rate =
on_time_orders / completed_orders
```

Other indicators:

-   Average delay.
-   Quality rejection rate.
-   Claim mismatch count.
-   Tracking discrepancy count.
-   ETA change frequency.

------------------------------------------------------------------------

# 10. Supplier Selection

Supplier selection is a two-stage process.

## Stage 1: Hard filtering

``` text
Requirement
    |
    +-- stock available?
    +-- certification valid?
    +-- AQL acceptable?
    +-- material grade compatible?
    +-- dimensions/specifications compatible?
    +-- lead time feasible?
    +-- MOQ feasible?
    +-- supplier active?
    |
    v
Eligible suppliers
```

## Stage 2: Scoring

Default configurable score:

``` text
Quality              30%
Delivery reliability 25%
Availability          20%
Price                 15%
Lead time             10%
```

Weights can change based on incident context.

For a production-stop incident, lead time and availability should
receive higher weight.

The Recovery & Recommendation Agent receives only the eligible
candidates and their deterministic scores/data.

------------------------------------------------------------------------

# 11. Human Approval

**No workflow executes autonomously.**

Every workflow follows:

``` text
Detect
  |
Analyze
  |
Generate Recovery Plan
  |
Validate
  |
Simulate
  |
Human Approval
  |
+--------+--------+
|                 |
Approve           Reject
|                 |
Execute           Modify/Replan
|
Verify
|
Complete / Replan
```

The UI must clearly show:

-   Current risk.
-   Affected production.
-   Inventory evidence.
-   Supplier comparison.
-   Quality constraints.
-   Cost.
-   Delivery time.
-   Alternatives considered.
-   Risk if no action is taken.
-   Proposed action.
-   Approval/rejection controls.
-   Audit history.

------------------------------------------------------------------------

# 12. Security Model

The LLM must not have unrestricted database or ERP access.

Use:

``` text
LLM
 |
Structured tool request
 |
Tool/Service layer
 |
Schema validation
 |
Authorization
 |
Deterministic business rules
 |
Database / ERP
```

Use allowlisted operations.

Examples:

``` text
get_inventory_status()
get_supplier_candidates()
get_supplier_capability()
calculate_risk()
validate_plan()
simulate_plan()
create_approval_request()
execute_approved_po()
verify_execution()
```

The LLM cannot directly execute arbitrary SQL.

MCP is optional. If used, use it as a standardized tool interface, not
as a security boundary. Authorization, validation, allowlisting and
human approval remain the real controls.

------------------------------------------------------------------------

# 13. Backend

## FastAPI

Recommended structure:

``` text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── incidents.py
│   │   ├── inventory.py
│   │   ├── suppliers.py
│   │   ├── recovery.py
│   │   ├── approvals.py
│   │   └── dashboard.py
│   │
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── recovery_recommendation.py
│   │   └── verification_replanning.py
│   │
│   ├── engines/
│   │   ├── risk_engine.py
│   │   ├── supplier_engine.py
│   │   ├── validation_engine.py
│   │   ├── simulation_engine.py
│   │   └── pricing_engine.py
│   │
│   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── session.py
│   │   └── migrations/
│   │
│   ├── schemas/
│   ├── services/
│   ├── tools/
│   └── audit/
│
├── tests/
├── Dockerfile
└── requirements.txt
```

------------------------------------------------------------------------

# 14. Frontend

## React

Recommended structure:

``` text
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Incidents.jsx
│   │   ├── IncidentDetails.jsx
│   │   ├── SupplierComparison.jsx
│   │   ├── ApprovalQueue.jsx
│   │   └── AuditTrail.jsx
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   └── App.jsx
├── Dockerfile
└── package.json
```

Recommended UI screens:

1.  Control Tower Dashboard.
2.  Incident Details.
3.  Supplier Comparison.
4.  Recovery Plan Comparison.
5.  Human Approval Queue.
6.  Execution Status.
7.  Audit Trail.

------------------------------------------------------------------------

# 15. API Design

## Incident

``` http
POST /api/v1/incidents
GET  /api/v1/incidents
GET  /api/v1/incidents/{incident_id}
```

## Inventory

``` http
GET /api/v1/inventory/{material_id}
GET /api/v1/inventory/{material_id}/coverage
GET /api/v1/inventory/{material_id}/history
```

## Suppliers

``` http
GET /api/v1/suppliers
GET /api/v1/suppliers/eligible/{material_id}
GET /api/v1/suppliers/{supplier_id}
```

## Recovery

``` http
POST /api/v1/incidents/{incident_id}/analyze
POST /api/v1/incidents/{incident_id}/recommend
GET  /api/v1/incidents/{incident_id}/plans
```

## Approval

``` http
GET  /api/v1/approvals
GET  /api/v1/approvals/{approval_id}
POST /api/v1/approvals/{approval_id}/approve
POST /api/v1/approvals/{approval_id}/reject
```

## Execution

``` http
POST /api/v1/plans/{plan_id}/execute
GET  /api/v1/plans/{plan_id}/status
```

Execution endpoint must verify that an approved approval request exists.

------------------------------------------------------------------------

# 16. Async Workflow

For the MVP, do not introduce Kafka.

Use FastAPI + background worker/task execution.

Initial flow:

``` text
POST /incidents
      |
      v
Create incident
      |
      v
Return 202 Accepted
      |
      v
Run workflow asynchronously
      |
      v
Persist state in PostgreSQL
      |
      v
Frontend polls incident status
```

If workload later requires it, Redis + a task queue can be introduced
without changing the business engines.

Kafka is not required for the hackathon MVP.

------------------------------------------------------------------------

# 17. Technology Stack

  Layer                 Technology
  --------------------- -------------------------------------
  Frontend              React.js
  Backend               FastAPI
  Language              Python
  Database              PostgreSQL
  DB container          Docker
  ORM                   SQLAlchemy 2.x
  Driver                asyncpg
  Migrations            Alembic
  Agent orchestration   LangGraph
  LLM                   Configurable provider
  Validation            Pydantic
  API                   REST
  Containerization      Docker + Docker Compose
  Testing               Pytest
  Frontend testing      Vitest / React Testing Library
  HTTP client           httpx
  Database search       PostgreSQL B-tree + partial indexes
  Observability         Structured logs + audit_events

------------------------------------------------------------------------

# 18. Docker Architecture

``` text
docker-compose
|
+-- frontend
|     React
|
+-- backend
|     FastAPI
|
+-- worker
|     LangGraph workflow execution
|
+-- postgres
|     PostgreSQL
|
+-- optional: redis
      Only if async task load requires it
```

For the initial MVP, Redis can remain disabled.

------------------------------------------------------------------------

# 19. Scenario Coverage

## Scenario 1: Normal Disruption

``` text
Supplier delay
    |
Risk Engine
    |
Inventory coverage
    |
Affected production
    |
Supplier Evaluation
    |
Recovery & Recommendation
    |
Validation + Simulation
    |
Human Approval
    |
Execution
    |
Verification
```

## Scenario 2: Stale Inventory

``` text
ERP = 800
Physical = 390
    |
Risk Engine
    |
Discrepancy detected
    |
Coverage recalculated
    |
Risk increased
    |
Audit event
    |
Recovery workflow
```

## Scenario 3: Adversarial Supplier

``` text
Supplier says DISPATCHED
Tracking says LABEL_CREATED
    |
Deterministic verification
    |
Claim mismatch
    |
Supplier reliability risk increased
    |
Alternate sourcing
```

## Scenario 4: Quality Constraint

``` text
Cheap supplier
    |
Supplier Evaluation
    |
Certification/AQL/spec mismatch
    |
Rejected before recommendation
```

## Scenario 5: Budget Approval

``` text
Recovery plan
    |
Cost > approval threshold
    |
Approval brief
    |
Human approval
    |
Only then execution
```

## Scenario 6: High-Pressure Production Risk

``` text
12 hours to production stop
    |
Risk Engine
    |
Critical production prioritization
    |
Supplier candidates
    |
Recovery Agent
    |
Partial/split sourcing + rescheduling options
    |
Simulation
    |
Human Approval
    |
Execution
    |
Verification
```

------------------------------------------------------------------------

# 20. Auditability

Every important action creates an audit event.

Example:

``` json
{
  "incident_id": "INC-1001",
  "agent_name": "recovery_recommendation",
  "event_type": "RECOMMENDATION",
  "action": "RECOMMEND_SPLIT_SOURCING",
  "reason": "Single supplier cannot meet required quantity before production deadline",
  "risk_level": "CRITICAL"
}
```

The audit trail must allow the team to answer:

-   What happened?
-   What data was used?
-   What rules were triggered?
-   Which suppliers were rejected?
-   Why was a supplier recommended?
-   What did the LLM recommend?
-   What did the deterministic validator conclude?
-   Who approved the plan?
-   What was executed?
-   What happened after execution?

------------------------------------------------------------------------

# 21. Core Design Principles

1.  **No LLM for operational truth.**
2.  **Hard constraints before LLM recommendations.**
3.  **Every workflow requires human approval.**
4.  **LLM cannot directly execute arbitrary database/ERP operations.**
5.  **PostgreSQL is the source of truth for structured operational
    data.**
6.  **Historical inventory and consumption data are required for 30-day
    baselines.**
7.  **Use partial indexes for high-frequency eligibility queries.**
8.  **Validate and simulate every recovery plan before approval.**
9.  **Everything important is auditable.**
10. **Prefer a simple monolithic backend over unnecessary microservices
    for the MVP.**

------------------------------------------------------------------------

# 22. MVP

The MVP must demonstrate all six scenarios using seeded PostgreSQL data.

### Required

-   [ ] React dashboard.
-   [ ] FastAPI backend.
-   [ ] Dockerized PostgreSQL.
-   [ ] Database schema and seed data.
-   [ ] Inventory risk engine.
-   [ ] 30-day inventory/consumption calculations.
-   [ ] Supplier hard-constraint filtering.
-   [ ] Partial indexes.
-   [ ] Supplier scoring.
-   [ ] Recovery & Recommendation Agent.
-   [ ] Plan validation.
-   [ ] What-if simulation.
-   [ ] Human approval for every workflow.
-   [ ] Deterministic execution mock.
-   [ ] Verification/replanning.
-   [ ] Audit trail.
-   [ ] All six demo scenarios.

### Avoid in MVP

-   Kafka.
-   Kubernetes.
-   Complex microservices.
-   Vector database.
-   RAG.
-   Embedding search.
-   Autonomous procurement.
-   Complex ML forecasting.
-   Real ERP integration unless the hackathon explicitly provides it.

------------------------------------------------------------------------

# 23. Success Criteria

The system should demonstrate:

``` text
Correct detection
        +
Correct supplier filtering
        +
Explainable recommendation
        +
Deterministic validation
        +
Human approval
        +
Safe execution
        +
Verification
        +
Auditability
```

The strongest demo message is:

> **AI does not get to decide what is true or execute what it wants. It
> reasons over verified operational data, proposes a recovery plan,
> deterministic systems validate it, and a human authorizes execution.**
