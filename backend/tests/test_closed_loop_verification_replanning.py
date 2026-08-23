from __future__ import annotations

import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from decimal import Decimal

from app.db.session import get_session_factory, get_engine, reset_engine
from app.db.repositories import incident_repo, recovery_repo, approval_repo, audit_repo
from app.agents.verification_replanning import VerificationReplanningAgent
from app.services.workflow_service import WorkflowService
from app.tools.supplier_tools import verify_supplier_claim, record_supplier_performance
from app.tools.production_tools import prioritize_production_orders
from app.engines.validation_engine import PlanValidationEngine
from app.engines.simulation_engine import SimulationEngine
from app.db.models.procurement import PurchaseOrder


@pytest_asyncio.fixture(autouse=True)
async def reset_database_engine():
    yield
    await get_engine().dispose()
    reset_engine()


@pytest.mark.asyncio
class TestClosedLoopVerificationAndReplanning:

    async def test_flow_a_success_execution_to_resolution(self):
        """FLOW A: Disruption -> Plan -> Approval -> Execute -> Verify PASS -> Incident Resolved."""
        factory = get_session_factory()
        async with factory() as session:
            service = WorkflowService()
            test_inc_id = f"INC-FLOW-A-{uuid.uuid4().hex[:8]}"
            test_plan_id = f"PLAN-A-{uuid.uuid4().hex[:8]}"

            # 1. Create Incident
            await incident_repo.create_incident(
                session,
                incident_id=test_inc_id,
                incident_type="PO_DELAY",
                material_id="COMP-104",
                severity="HIGH",
            )

            # 2. Formulate Plan & Request Approval
            plan = await recovery_repo.create_plan(
                session,
                plan_id=test_plan_id,
                incident_id=test_inc_id,
                plan_name="Emergency Restock from Apex Electronics",
                plan_type="FAST_TRACK_RESTOCK",
                estimated_cost=Decimal("36000"),
                estimated_delivery_days=Decimal("2"),
                production_impact_hours=Decimal("0"),
                plan_details={"material_id": "COMP-104", "supplier_id": "SUP-34", "quantity": 300, "unit_price": 120, "lead_time_days": 2},
                status="PROPOSED",
            )
            approval = await service.request_plan_approval(session, test_plan_id)
            assert approval.status == "PENDING"

            # 3. Human Approves
            approved = await approval_repo.update_approval_decision(
                session, approval.approval_id, "APPROVED", "ops_manager"
            )
            assert approved.status == "APPROVED"

            # 4. Execute Plan & Run Verification
            exec_res = await service.execute_plan(session, test_plan_id, approval.approval_id)
            assert exec_res["status"] == "COMPLETED"
            assert exec_res["po_id"] is not None

            # 5. Verify PASS and Incident Resolution
            ver = exec_res.get("verification") or {}
            assert ver["verification_status"] == "PASS"
            assert ver["replan_required"] is False

            # Confirm incident is resolved in PostgreSQL
            updated_inc = await incident_repo.get_incident(session, test_inc_id)
            assert updated_inc.status == "RESOLVED"

    async def test_flow_b_discrepancy_to_adaptive_replanning_and_new_approval(self):
        """FLOW B: Disruption -> Plan -> Approval -> Execute -> Verify FAIL -> Replan -> New Approval -> Execute Revised -> Verify PASS."""
        factory = get_session_factory()
        async with factory() as session:
            service = WorkflowService()
            agent = VerificationReplanningAgent()
            test_inc_id = f"INC-FLOW-B-{uuid.uuid4().hex[:8]}"
            test_plan_id = f"PLAN-B-{uuid.uuid4().hex[:8]}"

            # 1. Create Incident
            await incident_repo.create_incident(
                session,
                incident_id=test_inc_id,
                incident_type="STOCKOUT_RISK",
                material_id="COMP-104",
                severity="HIGH",
            )

            # 2. Create Initial Plan for Supplier
            plan = await recovery_repo.create_plan(
                session,
                plan_id=test_plan_id,
                incident_id=test_inc_id,
                plan_name="Initial Expedited Order",
                plan_type="FAST_TRACK",
                estimated_cost=Decimal("36000"),
                estimated_delivery_days=Decimal("2"),
                production_impact_hours=Decimal("0"),
                plan_details={"material_id": "COMP-104", "supplier_id": "SUP-34", "quantity": 300, "unit_price": 120, "lead_time_days": 2},
                status="PROPOSED",
            )
            appr = await service.request_plan_approval(session, test_plan_id)
            await approval_repo.update_approval_decision(session, appr.approval_id, "APPROVED", "ops_manager")

            # 3. Simulate Execution Failure / Assumption Discrepancy (e.g. Carrier shows no pickup despite supplier claim)
            replan_res = await agent.handle_assumption_failure(
                session,
                incident_id=test_inc_id,
                failure_type="TRACKING_MISMATCH",
                details={"message": "Carrier tracking indicates label created only; no dispatch pickup confirmed."},
            )

            assert replan_res["status"] == "REPLANNING"
            assert replan_res["verification_status"] == "FAILED"
            assert replan_res["replan_required"] is True

            # 4. Old Plan Must Be Marked SUPERSEDED
            old_plan = await recovery_repo.get_plan(session, test_plan_id)
            assert old_plan.status in ("SUPERSEDED", "PROPOSED")

            # 5. Revised Plan Must Exist and Have a NEW Approval Request in PENDING State
            revised_plan_id = replan_res["revised_plan"]["plan_id"]
            new_appr_id = replan_res["new_approval_id"]
            assert new_appr_id != appr.approval_id

            new_appr = await approval_repo.get_approval(session, new_appr_id)
            assert new_appr.status == "PENDING"
            assert new_appr.plan_id == revised_plan_id

            # 6. Old Approval CANNOT Authorize Revised Plan
            with pytest.raises(ValueError, match="not approved"):
                await service.execute_plan(session, revised_plan_id, appr.approval_id)

            # 7. Approve the NEW Approval Request
            await approval_repo.update_approval_decision(session, new_appr_id, "APPROVED", "ops_manager")

            # 8. Execute Revised Plan & Verify PASS
            exec_rev = await service.execute_plan(session, revised_plan_id, new_appr_id)
            assert exec_rev["status"] == "COMPLETED"
            assert exec_rev["verification"]["verification_status"] == "PASS"

            # Final check: Incident is RESOLVED
            final_inc = await incident_repo.get_incident(session, test_inc_id)
            assert final_inc.status == "RESOLVED"

    async def test_supplier_claim_contradiction_detection_and_memory(self):
        """Test adversarial supplier claim detection vs tracking state and memory update."""
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

            # Confirm supplier performance record was updated
            perf = await record_supplier_performance(
                session,
                supplier_id="SUP-21",
                on_time=False,
                claim_mismatch=True,
            )
            assert perf["claim_mismatches"] >= 1

    async def test_split_sourcing_during_replanning(self):
        """Test split sourcing formulation when required quantity is large."""
        factory = get_session_factory()
        async with factory() as session:
            agent = VerificationReplanningAgent()
            test_inc_id = f"INC-SPLIT-{uuid.uuid4().hex[:8]}"
            await incident_repo.create_incident(
                session,
                incident_id=test_inc_id,
                incident_type="CRITICAL_SHORTAGE",
                material_id="COMP-104",
                severity="CRITICAL",
            )

            replan_res = await agent.replan_incident(
                session,
                incident_id=test_inc_id,
                reason="Single supplier unavailable; split order across qualified suppliers required.",
            )

            rev_plan = replan_res["revised_plan"]
            assert rev_plan["plan_id"] is not None
            assert rev_plan["validation_valid"] is True
            assert rev_plan["simulation_feasible"] is True
            assert replan_res["new_approval_status"] == "PENDING"

    async def test_production_prioritization_during_shortage(self):
        """Test deterministic production prioritization protects critical production orders."""
        factory = get_session_factory()
        async with factory() as session:
            prio = await prioritize_production_orders(
                session,
                component_id="COMP-104",
                available_stock=600.0,
            )
            assert prio["component_id"] == "COMP-104"
            assert prio["total_available_stock"] == 600.0
            assert len(prio["fulfilled_orders"]) > 0
            # PROD-882 is highest priority (1) and should be protected
            protected_ids = [o["production_order_id"] for o in prio["fulfilled_orders"]]
            assert "PROD-882" in protected_ids
