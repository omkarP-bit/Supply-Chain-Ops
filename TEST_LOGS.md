# TEST_LOGS.md — Autonomous Supply Chain Recovery System

## Full Test Suite Results

### RUN: 2026-08-22 (latest)

```
tests/test_phase0_setup.py::test_health_endpoint_ok PASSED               [  1%]
tests/test_phase0_setup.py::test_openapi_available PASSED                [  3%]
tests/test_phase0_setup.py::test_database_url_configured PASSED          [  4%]
tests/test_phase0_setup.py::test_httpx_async_health PASSED               [  6%]
tests/test_phase12_scenarios.py::TestScenario1SupplierDelay::test_supplier_delay_full_workflow PASSED [  8%]
tests/test_phase12_scenarios.py::TestScenario2StaleInventory::test_stale_inventory_high_discrepancy PASSED [  9%]
tests/test_phase12_scenarios.py::TestScenario3ClaimMismatch::test_claim_mismatch_analysis PASSED [ 11%]
tests/test_phase12_scenarios.py::TestScenario4QualityConstraint::test_rejected_supplier_has_zero_score PASSED [ 12%]
tests/test_phase12_scenarios.py::TestScenario5BudgetApproval::test_dashboard_approvals PASSED [ 14%]
tests/test_phase12_scenarios.py::TestScenario5BudgetApproval::test_approvals_list PASSED [ 16%]
tests/test_phase12_scenarios.py::TestScenario6ProductionRisk::test_production_risk_and_recovery PASSED [ 17%]
tests/test_phase1_db.py::TestDatabaseSchema::test_materials_table_exists PASSED [ 19%]
tests/test_phase1_db.py::TestDatabaseSchema::test_comp104_seeded PASSED  [ 20%]
tests/test_phase1_db.py::TestDatabaseSchema::test_material_spec_seeded PASSED [ 22%]
tests/test_phase1_db.py::TestDatabaseSchema::test_at_least_3_materials PASSED [ 24%]
tests/test_phase1_db.py::TestSupplierSeeding::test_sup21_seeded PASSED   [ 25%]
tests/test_phase1_db.py::TestSupplierSeeding::test_sup34_reliability PASSED [ 27%]
tests/test_phase1_db.py::TestSupplierSeeding::test_sup77_inactive PASSED [ 29%]
tests/test_phase1_db.py::TestSupplierSeeding::test_4_supplier_materials PASSED [ 30%]
tests/test_phase1_db.py::TestSupplierSeeding::test_sup21_cert_invalid PASSED [ 32%]
tests/test_phase1_db.py::TestSupplierSeeding::test_sup34_cert_valid PASSED [ 33%]
tests/test_phase1_db.py::TestSupplierSeeding::test_sup52_insufficient_stock PASSED [ 35%]
tests/test_phase1_db.py::TestInventorySeeding::test_35_snapshots PASSED  [ 37%]
tests/test_phase1_db.py::TestInventorySeeding::test_today_stale_inventory PASSED [ 38%]
tests/test_phase1_db.py::TestInventorySeeding::test_discrepancy_percentage PASSED [ 40%]
tests/test_phase1_db.py::TestProductionOrders::test_prod882_critical PASSED [ 41%]
tests/test_phase1_db.py::TestPurchaseOrder::test_po7712_delayed PASSED   [ 43%]
tests/test_phase1_db.py::TestRiskThresholds::test_3_thresholds PASSED    [ 45%]
tests/test_phase2_indexes.py::TestPartialIndexes::test_eligible_supplier_index_exists PASSED [ 46%]
tests/test_phase2_indexes.py::TestPartialIndexes::test_active_supplier_index_exists PASSED [ 48%]
tests/test_phase2_indexes.py::TestPartialIndexes::test_supplier_material_available_index_exists PASSED [ 50%]
tests/test_phase2_indexes.py::TestPartialIndexes::test_supplier_certification_index_exists PASSED [ 51%]
tests/test_phase2_indexes.py::TestPartialIndexes::test_eligible_query_uses_index PASSED [ 53%]
tests/test_phase3_risk_engine.py::TestRiskEngineInventory::test_get_current_inventory PASSED [ 54%]
tests/test_phase3_risk_engine.py::TestRiskEngineConsumption::test_calculate_consumption_30d PASSED [ 56%]
tests/test_phase3_risk_engine.py::TestRiskEngineConsumption::test_calculate_consumption_7d PASSED [ 58%]
tests/test_phase3_risk_engine.py::TestRiskEngineCoverage::test_calculate_coverage PASSED [ 59%]
tests/test_phase3_risk_engine.py::TestRiskEngineDiscrepancy::test_calculate_discrepancy PASSED [ 61%]
tests/test_phase3_risk_engine.py::TestRiskEngineAffectedOrders::test_find_affected_production_orders PASSED [ 62%]
tests/test_phase3_risk_engine.py::TestRiskEngineHoursToStop::test_hours_to_stop PASSED [ 64%]
tests/test_phase3_risk_engine.py::TestRiskEngineCalculateRisk::test_calculate_risk PASSED [ 66%]
tests/test_phase3_risk_engine.py::TestRiskEngineCalculateRisk::test_trend_accelerating PASSED [ 67%]
tests/test_phase4_supplier_engine.py::TestSupplierCandidates::test_get_candidates PASSED [ 69%]
tests/test_phase4_supplier_engine.py::TestSupplierCandidates::test_sup21_rejected PASSED [ 70%]
tests/test_phase4_supplier_engine.py::TestSupplierCandidates::test_sup34_eligible PASSED [ 72%]
tests/test_phase4_supplier_engine.py::TestSupplierCandidates::test_sup41_eligible PASSED [ 74%]
tests/test_phase4_supplier_engine.py::TestSupplierCandidates::test_sup52_rejected PASSED [ 75%]
tests/test_phase4_supplier_engine.py::TestSupplierCandidates::test_sup77_rejected PASSED [ 77%]
tests/test_phase4_supplier_engine.py::TestSupplierScoring::test_scores_ordering PASSED [ 79%]
tests/test_phase4_supplier_engine.py::TestSupplierScoring::test_supplier_score_weights PASSED [ 80%]
tests/test_phase5_recovery.py::TestAnalyzeIncident::test_analyze_incident PASSED [ 82%]
tests/test_phase5_recovery.py::TestRecommendRecovery::test_recommend_recovery PASSED [ 83%]
tests/test_phase5_recovery.py::TestGetPlans::test_get_plans PASSED       [ 85%]
tests/test_phase5_recovery.py::TestIncidentNotFound::test_analyze_nonexistent PASSED [ 87%]
tests/test_phase5_recovery.py::TestIncidentNotFound::test_recommend_nonexistent PASSED [ 88%]
tests/test_phase6_validation.py::TestPlanValidation::test_valid_plan PASSED [ 90%]
tests/test_phase6_validation.py::TestPlanValidation::test_invalid_quantity PASSED [ 91%]
tests/test_phase6_validation.py::TestPlanValidation::test_invalid_lead_time PASSED [ 92%]
tests/test_phase6_validation.py::TestPlanValidation::test_invalid_cert PASSED [ 95%]
tests/test_phase7_simulation.py::TestSimulation::test_simulate_plan PASSED [ 96%]
tests/test_phase7_simulation.py::TestSimulation::test_simulation_feasibility PASSED [ 98%]
tests/test_phase7_simulation.py::TestSimulation::test_simulation_with_partial PASSED [100%]

======================= 62 passed, 4 warnings in 10.52s ========================
```

### Phase Summary

| Phase | Description | Tests | Status |
|-------|-------------|-------|--------|
| Phase 0 | Project Setup | 4 | PASSED |
| Phase 1 | Database Foundation | 17 | PASSED |
| Phase 2 | Partial Indexes | 5 | PASSED |
| Phase 3 | Risk Engine | 9 | PASSED |
| Phase 4 | Supplier Engine | 8 | PASSED |
| Phase 5 | Recovery API | 5 | PASSED |
| Phase 6 | Validation Engine | 4 | PASSED |
| Phase 7 | Simulation Engine | 3 | PASSED |
| Phase 12 | Scenario Tests | 7 | PASSED |
| **Total** | | **62** | **ALL PASSED** |

### Key Bug Fixes Applied (This Session)

1. **uuid.UUID for material_id**: API routes (`recovery.py`, `inventory.py`, `suppliers.py`) were calling `uuid.UUID(material_id)` but material IDs are strings like "COMP-104". Fixed by passing strings directly.
2. **Missing commits in repos**: All repository `create_*` and `update_*` functions called `session.flush()` but never `session.commit()`, causing data to be invisible to subsequent requests. Added `await session.commit()` to all repos.
3. **asyncpg event loop binding**: TestClient creates new event loops per request; asyncpg pool connections are bound to one loop. Fixed by using subprocess-based integration tests (uvicorn + requests) for Phase 5 and Phase 12.
4. **inventory.py coverage endpoint**: Fixed same uuid.UUID bug and confirmed inventory snapshot, coverage, and history endpoints work correctly.

### API Endpoints Verified Working

- `GET /health` — Database status check
- `POST /api/v1/incidents` — Create incident (201)
- `POST /api/v1/incidents/{id}/analyze` — Risk analysis with supplier candidates
- `POST /api/v1/incidents/{id}/recommend` — Recovery plan generation
- `GET /api/v1/incidents/{id}/plans` — List recovery plans
- `GET /api/v1/dashboard` — Dashboard with active incidents, production at risk
- `GET /api/v1/suppliers` — List all suppliers
- `GET /api/v1/suppliers/eligible/{material_id}` — Filtered eligible suppliers
- `GET /api/v1/approvals` — Pending approval queue
- `GET /api/v1/inventory/{material_id}` — Latest inventory snapshot
- `GET /api/v1/inventory/{material_id}/coverage` — Coverage analysis
- `GET /api/v1/inventory/{material_id}/history` — 35-day history
- `GET /api/v1/audit` — Audit trail events

---

## Phase 11: React Control Tower Frontend

### Build Result

```
vite v5.4.21 building for production...
transforming...
✓ 44 modules transformed.
dist/index.html                  0.34 kB │ gzip:  0.25 kB
dist/assets/index-CsS-iidB.js  186.97 kB │ gzip: 59.37 kB
✓ built in 582ms
```

### Pages Created

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Stats cards (active incidents, critical risk, pending approvals, production at risk), production at risk material badges, recent incidents table |
| Incidents | `/incidents` | Full incident list with type, material, severity badge, status badge, creation time |
| Incident Details | `/incidents/:id` | Full incident view with material info, inventory coverage stats, Analyze Risk / Get Recommendations buttons, risk analysis results, eligible suppliers table, recovery plans cards |
| Supplier Comparison | `/suppliers` | All suppliers with quality/reliability scores, eligibility filter (all/eligible/rejected), per-material eligibility data (score, price, lead time, certification) |
| Approvals | `/approvals` | Pending approval queue with Approve/Reject actions |
| Audit Trail | `/audit` | Timeline view of all audit events with event type dots, agent names, timestamps, output data |

### Components

| Component | File | Description |
|-----------|------|-------------|
| Layout | `src/components/Layout.jsx` | Sidebar nav + main content area |
| RiskBadge | `src/components/RiskBadge.jsx` | Colored badge for CRITICAL/HIGH/MEDIUM/LOW/NONE |
| StatusBadge | `src/components/StatusBadge.jsx` | Colored badge for workflow statuses |
| UI (Card, StatCard, Table, Loading, Error) | `src/components/UI.jsx` | Reusable UI primitives |

### API Client

`src/services/api.js` — Covers all backend endpoints: health, dashboard, incidents CRUD, analysis, recommendations, plans, inventory (snapshot/coverage/history), suppliers (list/eligible/detail), approvals (list/detail/approve/reject), audit events.

### Additional Backend

- Added `GET /api/v1/audit` endpoint (`backend/app/api/audit.py`) for audit trail queries
- Registered in `main.py`
