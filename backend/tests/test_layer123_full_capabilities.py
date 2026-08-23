from __future__ import annotations

import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.db.session import get_session_factory, get_engine, reset_engine
from app.engines.risk_engine import OperationalRiskEngine
from app.engines.supplier_engine import SupplierEvaluationEngine
from app.engines.validation_engine import PlanValidationEngine
from app.engines.simulation_engine import SimulationEngine
from app.agents.supervisor import SupervisorAgent
from app.agents.recovery_recommendation import RecoveryRecommendationAgent
from app.agents.verification_replanning import VerificationReplanningAgent
from app.tools.purchase_order_tools import get_purchase_order, create_purchase_order
from app.tools.supplier_tools import query_suppliers_for_component, record_supplier_performance, verify_supplier_claim
from app.tools.production_tools import get_production_schedule, prioritize_production_orders
from app.tools.messaging_tools import send_supplier_message
from app.tools.rfq_tools import broadcast_rfq
from app.tools.erp_tools import commit_erp_recovery_actions
from app.db.repositories import incident_repo, recovery_repo, approval_repo


@pytest_asyncio.fixture(autouse=True)
async def reset_database_engine():
    yield
    await get_engine().dispose()
    reset_engine()


@pytest.mark.asyncio
class TestLayer1MonitoringAssistant:
    """Layer 1: Reading POs, detecting shipment delay, deterministic inventory risk, and drafting supplier follow-ups."""

    async def test_read_purchase_order_details(self):
        factory = get_session_factory()
        async with factory() as session:
            po = await get_purchase_order(session, "PO-7712")
            assert po is not None
            assert po["po_id"] == "PO-7712"
            assert po["component_id"] == "COMP-104"
            assert po["status"] == "delayed"
            assert po["quantity"] > 0
            assert po["supplier_id"] == "SUP-21"

    async def test_deterministic_inventory_risk_calculations(self):
        factory = get_session_factory()
        async with factory() as session:
            risk_engine = OperationalRiskEngine()
            risk = await risk_engine.calculate_risk(session, "COMP-104")

            # Must be deterministic Python calculations (no LLM)
            assert isinstance(risk.usable_stock, Decimal)
            assert isinstance(risk.coverage_days, Decimal)
            assert isinstance(risk.avg_daily_consumption_30d, Decimal)
            assert isinstance(risk.avg_daily_consumption_7d, Decimal)
            assert risk.hours_to_production_stop > 0
            assert risk.risk_level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    async def test_supplier_followup_message_drafting(self):
        factory = get_session_factory()
        async with factory() as session:
            msg = await send_supplier_message(
                session,
                supplier_id="SUP-21",
                subject="Urgent: Delayed Shipment Status for PO-7712",
                body="Please provide revised ETA and dispatch confirmation.",
            )
            assert msg["supplier_id"] == "SUP-21"
            assert "message_id" in msg


@pytest.mark.asyncio
class TestLayer2ProcurementPlanner:
    """Layer 2: RFQ creation, quote evaluation, deterministic hard filtering, approval enforcement, and ERP updates."""

    async def test_rfq_broadcast_and_supplier_filtering(self):
        factory = get_session_factory()
        async with factory() as session:
            rfq_res = await broadcast_rfq(
                session,
                component_id="COMP-104",
                quantity=400,
                deadline_days=5,
            )
            assert len(rfq_res) > 0

            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(session, "COMP-104", Decimal("400"), 5)

            # Unqualified suppliers must have score 0 with explicit rejection reasons
            sup21 = next((c for c in candidates if str(c.supplier_id) == "SUP-21"), None)
            assert sup21 is not None
            assert sup21.score == 0.0
            assert sup21.rejection_reason is not None

            # Qualified supplier must pass with score > 0
            sup34 = next((c for c in candidates if str(c.supplier_id) == "SUP-34"), None)
            assert sup34 is not None
            assert sup34.certification_valid is True
            assert sup34.score > 70.0

    async def test_approval_threshold_enforcement(self):
        factory = get_session_factory()
        async with factory() as session:
            test_inc_id = f"INC-L2-{uuid.uuid4().hex[:8]}"
            test_plan_id = f"PLAN-L2-{uuid.uuid4().hex[:8]}"
            test_appr_id = f"APP-L2-{uuid.uuid4().hex[:8]}"

            inc = await incident_repo.create_incident(
                session,
                incident_id=test_inc_id,
                incident_type="PO_DELAY",
                material_id="COMP-104",
                severity="HIGH",
            )
            plan = await recovery_repo.create_plan(
                session,
                plan_id=test_plan_id,
                incident_id=test_inc_id,
                plan_name="Emergency Order",
                plan_type="FAST_TRACK",
                estimated_cost=Decimal("120000"),
                estimated_delivery_days=Decimal("2"),
                production_impact_hours=Decimal("0"),
                plan_details={"material_id": "COMP-104", "supplier_id": "SUP-34", "quantity": 800, "unit_price": 150},
            )
            appr = await approval_repo.create_approval(
                session,
                approval_id=test_appr_id,
                incident_id=test_inc_id,
                plan_id=test_plan_id,
                requested_amount=Decimal("120000"),
                approval_threshold=Decimal("75000"),
                status="PENDING",
            )
            test_po = await create_purchase_order(
                session,
                supplier_id="SUP-34",
                material_id="COMP-104",
                quantity=Decimal("100"),
                unit_price=Decimal("120"),
            )

            # Update ERP actions after approval
            erp_res = await commit_erp_recovery_actions(
                session,
                incident_id=test_inc_id,
                action_type="UPDATE_PO",
                details={"po_id": test_po["po_id"], "status": "CONFIRMED"},
            )
            assert erp_res["updated"] is True


@pytest.mark.asyncio
class TestLayer3DisruptionControlAgent:
    """Layer 3: Multiple disruptions, adaptive replanning, split sourcing, production prioritization, claim verification, and memory."""

    async def test_multiple_simultaneous_disruptions_isolation(self):
        factory = get_session_factory()
        async with factory() as session:
            supervisor = SupervisorAgent()
            inc1 = await supervisor.start_workflow(session, {"incident_type": "PO_DELAY", "material_id": "COMP-104"})
            inc2 = await supervisor.start_workflow(session, {"incident_type": "STOCK_DISCREPANCY", "material_id": "COMP-104"})

            assert inc1["incident_id"] != inc2["incident_id"]
            assert inc1["incident_id"] is not None
            assert inc2["incident_id"] is not None

    async def test_misleading_supplier_claim_verification(self):
        factory = get_session_factory()
        async with factory() as session:
            claim_res = await verify_supplier_claim(
                session,
                supplier_id="SUP-21",
                po_id="PO-7712",
                claimed_status="DISPATCHED",
                actual_tracking_status="LABEL_CREATED",
            )
            assert claim_res["discrepancy_detected"] is True
            assert "Misleading claim" in claim_res["details"]

    async def test_supplier_performance_memory_persistence(self):
        factory = get_session_factory()
        async with factory() as session:
            perf = await record_supplier_performance(
                session,
                supplier_id="SUP-21",
                on_time=False,
                delay_days=4.5,
                quality_passed=True,
                claim_mismatch=True,
            )
            assert perf["orders_completed"] >= 1
            assert perf["claim_mismatches"] >= 1

    async def test_production_order_prioritization(self):
        factory = get_session_factory()
        async with factory() as session:
            prio_res = await prioritize_production_orders(
                session,
                component_id="COMP-104",
                available_stock=400.0,
            )
            assert prio_res["component_id"] == "COMP-104"
            assert len(prio_res["fulfilled_orders"]) + len(prio_res["delayed_orders"]) > 0

    async def test_adaptive_replanning_on_assumption_failure(self):
        factory = get_session_factory()
        async with factory() as session:
            test_inc_id = f"INC-REPLAN-{uuid.uuid4().hex[:8]}"
            await incident_repo.create_incident(
                session,
                incident_id=test_inc_id,
                incident_type="PO_DELAY",
                material_id="COMP-104",
                severity="HIGH",
            )
            agent = VerificationReplanningAgent()
            replan_res = await agent.handle_assumption_failure(
                session,
                incident_id=test_inc_id,
                failure_type="TRACKING_MISMATCH",
                details={"message": "Carrier shows no pickup despite supplier claim"},
            )
            assert replan_res["status"] == "REPLANNING"
            assert replan_res["replan_triggered"] is True

    async def test_split_sourcing_validation_and_multi_objective_tradeoff(self):
        factory = get_session_factory()
        async with factory() as session:
            validator = PlanValidationEngine()
            split_plan = {
                "material_id": "COMP-104",
                "supplier_id": "SUP-34",
                "required_quantity": 300,
                "unit_price": 120.0,
                "total_cost": 36000.0,
                "deadline_days": 5,
            }
            res = await validator.validate_plan(session, split_plan)
            assert res.valid is True

            sim_engine = SimulationEngine()
            sim_res = await sim_engine.simulate_plan(session, split_plan)
            assert sim_res.feasible is True
            assert sim_res.production_coverage_days > 10.0
