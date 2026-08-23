from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import Component, ContractSupplier, ContractPurchaseOrder, ContractProductionOrder, SupplierMessage
from app.db.models.inventory import InventorySnapshot
from app.db.models.materials import Material
from app.db.models.procurement import PurchaseOrder, Shipment
from app.db.models.production import ProductionOrder
from app.db.models.suppliers import Supplier, SupplierMaterial, SupplierPerformance, SupplierCommunication
from app.db.models.workflow import Incident, RecoveryPlan, ApprovalRequest
from app.db.repositories import incident_repo, recovery_repo, approval_repo, audit_repo
from app.audit.audit_service import log_event
from app.services.workflow_service import WorkflowService
from app.tools.supplier_tools import record_supplier_performance

workflow_service = WorkflowService()

SCENARIO_METADATA = [
    {
        "scenario_id": "SCENARIO-1",
        "name": "Normal Disruption (Supplier Delay)",
        "business_problem": "Supplier SUP-21 informs that PO-7712 for COMP-104 will be delayed by 5 days.",
        "initial_conditions": "PO: PO-7712 | Component: COMP-104 (Precision Aluminum Housing) | Supplier: SUP-21 | Delay: +5 Days | Original ETA: Sept 4",
        "expected_behavior": "Checks current inventory, calculates days of production coverage, asks SUP-21 for revised confirmation, searches alternate suppliers (SUP-34, SUP-41), compares price/quality/reliability, and creates emergency recovery plan.",
        "systems_involved": ["OperationalRiskEngine", "SupplierEvaluationEngine", "LangGraph Supervisor", "RecoveryAgent", "SimulationEngine"],
        "target_material": "COMP-104",
        "target_po": "PO-7712",
        "target_supplier": "SUP-21",
    },
    {
        "scenario_id": "SCENARIO-2",
        "name": "Stale Inventory Data (Warehouse Discrepancy)",
        "business_problem": "ERP reports 800 units of COMP-102, but a warehouse update reveals that only 390 units are usable (51.2% discrepancy).",
        "initial_conditions": "ERP Quantity: 800 units | Warehouse Usable: 390 units | Discrepancy: 51.2% | Component: COMP-102 (Brake Sensor)",
        "expected_behavior": "Detects inventory mismatch, recalculates production coverage using 390 usable units, increases risk severity to CRITICAL, replans procurement based on usable stock, and records discrepancy in audit trail.",
        "systems_involved": ["InventorySnapshot Telemetry", "OperationalRiskEngine", "Deterministic Discrepancy Gate", "RecoveryAgent"],
        "target_material": "COMP-102",
        "target_po": "PO-7735",
        "target_supplier": "SUP-34",
    },
    {
        "scenario_id": "SCENARIO-3",
        "name": "Adversarial Supplier Claim (Claim Mismatch)",
        "business_problem": "SUP-21 claims the delayed shipment has been dispatched, but tracking shows only a label was created and no pickup occurred.",
        "initial_conditions": "Supplier Claim: DISPATCHED | Carrier Tracking (TRK-7730): LABEL_CREATED / NO_PICKUP | Component: COMP-105 (Steering Sensor) | Supplier: SUP-21",
        "expected_behavior": "Does not blindly trust supplier claim. Verifies shipment status using carrier tracking data, detects claim/tracking inconsistency, marks supplier reliability risk in memory, and continues alternate sourcing.",
        "systems_involved": ["Carrier Tracking API", "SupplierPerformance Memory", "VerificationReplanningAgent", "SupplierEvaluationEngine"],
        "target_material": "COMP-105",
        "target_po": "PO-7730",
        "target_supplier": "SUP-21",
    },
    {
        "scenario_id": "SCENARIO-4",
        "name": "Quality Constraint (Hard Certification Filter)",
        "business_problem": "Cheapest alternate supplier can deliver within 3 days but does not meet the required ISO 9001 certification level.",
        "initial_conditions": "Candidate A (SUP-21): ₹95/u (ISO Expired) | Candidate B (SUP-34): ₹120/u (ISO 9001 Certified) | Component: COMP-103 (Motor Controller)",
        "expected_behavior": "Deterministically filters out non-compliant supplier with score 0.0, selects certified supplier (SUP-34) even if more expensive, and clearly explains quality constraint rationale.",
        "systems_involved": ["Hard Constraint Filter", "PlanValidationEngine", "SupplierEvaluationEngine", "RecoveryAgent"],
        "target_material": "COMP-103",
        "target_po": "PO-7740",
        "target_supplier": "SUP-21",
    },
    {
        "scenario_id": "SCENARIO-5",
        "name": "Budget Approval Required (HITL Threshold Gate)",
        "business_problem": "The only feasible recovery plan cost (₹96,000) exceeds autonomous spending threshold (₹75,000).",
        "initial_conditions": "Recovery Plan Cost: ₹96,000 | Autonomous Authority Threshold: ₹75,000 | Component: COMP-108 (Door Lock Assembly)",
        "expected_behavior": "Generates approval brief with recovery cost, production impact, and alternatives considered. Halts execution before PO creation, requests human approval, and persists pending approval state.",
        "systems_involved": ["Human Approval Gate", "LangGraph Workflow", "ApprovalRepository", "WorkflowService"],
        "target_material": "COMP-108",
        "target_po": "PO-7718",
        "target_supplier": "SUP-34",
    },
    {
        "scenario_id": "SCENARIO-6",
        "name": "High-Pressure Production Risk (Line Stop <= 12h)",
        "business_problem": "Production line will stop in 9.6 simulated hours unless partial stock is secured or production is rescheduled.",
        "initial_conditions": "Hours to Line Stop: 9.6h | Buffer: 20 units (50 u/d burn) | Order: PROD-882 (CRITICAL) | Component: COMP-101 (Battery Controller)",
        "expected_behavior": "Detects critical line stop countdown (<12h), prioritizes critical production order PROD-882, evaluates split sourcing across multiple suppliers for expedited delivery, and validates recovery feasibility.",
        "systems_involved": ["Production Scheduler", "OperationalRiskEngine", "Split-Sourcing Optimization", "SimulationEngine"],
        "target_material": "COMP-101",
        "target_po": "PO-7720",
        "target_supplier": "SUP-21",
    },
]


class ScenarioService:

    async def list_scenarios(self, session: AsyncSession) -> list[dict[str, Any]]:
        """List all 6 official scenarios with their latest execution state from the database."""
        result = []
        for meta in SCENARIO_METADATA:
            scen_id = meta["scenario_id"]
            
            # Look up latest incident for this scenario
            stmt = (
                select(Incident)
                .where(Incident.workflow_state["scenario_id"].astext == scen_id)
                .order_by(Incident.created_at.desc())
                .limit(1)
            )
            res = await session.execute(stmt)
            latest_inc = res.scalar_one_or_none()

            status = "NOT_RUN"
            last_run_at = None
            incident_id = None
            approval_status = None

            if latest_inc:
                incident_id = latest_inc.incident_id
                last_run_at = latest_inc.created_at.isoformat() if latest_inc.created_at else None
                
                # Check approval status
                appr_stmt = select(ApprovalRequest).where(ApprovalRequest.incident_id == incident_id)
                appr_res = await session.execute(appr_stmt)
                appr = appr_res.scalar_one_or_none()
                if appr:
                    approval_status = appr.status

                if latest_inc.status in ("RESOLVED", "COMPLETED"):
                    status = "RESOLVED"
                elif latest_inc.status == "REPLANNING":
                    status = "REPLANNING"
                elif approval_status == "PENDING":
                    status = "AWAITING_APPROVAL"
                elif latest_inc.status == "ANALYZING":
                    status = "RUNNING"
                elif latest_inc.status == "EXECUTING":
                    status = "EXECUTED"
                else:
                    status = latest_inc.status

            result.append({
                **meta,
                "status": status,
                "last_run_at": last_run_at,
                "latest_incident_id": incident_id,
                "approval_status": approval_status,
            })
        return result

    async def inject_scenario(self, session: AsyncSession, scenario_id: str) -> dict[str, Any]:
        """Inject real persisted disruption data, create the incident, and execute the real LangGraph agent loop."""
        scen_meta = next((s for s in SCENARIO_METADATA if s["scenario_id"] == scenario_id), None)
        if not scen_meta:
            raise ValueError(f"Invalid scenario ID: {scenario_id}")

        now = datetime.now(timezone.utc)
        incident_id = f"INC-{scenario_id}-{uuid.uuid4().hex[:6]}"
        material_id = scen_meta["target_material"]
        po_id = scen_meta["target_po"]
        supplier_id = scen_meta["target_supplier"]

        # =========================================================================
        # 1. Real State Injection in PostgreSQL
        # =========================================================================
        if scenario_id == "SCENARIO-1":
            # Scenario 1: PO-7712 5-day delay on COMP-104 by SUP-21
            await session.execute(
                update(PurchaseOrder)
                .where(PurchaseOrder.po_id == "PO-7712")
                .values(
                    status="delayed",
                    expected_delivery_date=now + timedelta(days=9),
                    updated_at=now,
                )
            )
            await session.execute(
                update(ContractPurchaseOrder)
                .where(ContractPurchaseOrder.po_id == "PO-7712")
                .values(status="delayed")
            )
            # Log real supplier communications in both models
            comm = SupplierCommunication(
                supplier_id="SUP-21",
                po_id="PO-7712",
                message_type="DELAY_NOTIFICATION",
                message_text="Logistics disruption: delivery for PO-7712 delayed by 5 days. Revised ETA: Sept 9.",
                received_at=now,
            )
            session.add(comm)

            sup_msg = SupplierMessage(
                message_id=uuid.uuid4(),
                supplier_id="SUP-21",
                direction="inbound",
                subject="Delay on PO-7712",
                body="Logistics disruption: delivery for PO-7712 delayed by 5 days. Revised ETA: Sept 9.",
                sent_at=now,
            )
            session.add(sup_msg)

            # Autonomous agent broadcasts RFQ to alternate suppliers
            agent_rfq1 = SupplierMessage(
                message_id=uuid.uuid4(),
                supplier_id="SUP-34",
                direction="outbound",
                subject="Emergency Sourcing RFQ – COMP-104 (PO-7712 Delay)",
                body="Autonomous Disruption Agent broadcast: Requesting expedited quotation and capacity reservation for 800 units of COMP-104 (Precision Aluminum Housing) due to delay on PO-7712.",
                sent_at=now + timedelta(seconds=2),
            )
            session.add(agent_rfq1)

            agent_rfq2 = SupplierMessage(
                message_id=uuid.uuid4(),
                supplier_id="SUP-41",
                direction="outbound",
                subject="Secondary Supplier RFQ – COMP-104 Allocation",
                body="Autonomous Disruption Agent broadcast: Requesting unit rate and lead-time confirmation for emergency reserve quantity.",
                sent_at=now + timedelta(seconds=3),
            )
            session.add(agent_rfq2)

            inc_type = "SUPPLIER_DELAY"
            severity = "CRITICAL"
            desc = "SUP-21 delivery delayed by 5 days on PO-7712 for critical component COMP-104."

        elif scenario_id == "SCENARIO-2":
            # Scenario 2: Stale inventory ERP = 800, warehouse usable = 390 on COMP-102
            snap = InventorySnapshot(
                material_id="COMP-102",
                warehouse_id="WH-MAIN",
                snapshot_date=now,
                erp_quantity=Decimal("800.0"),
                physical_quantity=Decimal("390.0"),
                usable_quantity=Decimal("390.0"),
                available_quantity=Decimal("390.0"),
                reserved_quantity=Decimal("0.0"),
                damaged_quantity=Decimal("0.0"),
                blocked_quantity=Decimal("0.0"),
                in_transit_quantity=Decimal("0.0"),
                source="CYCLE_COUNT_AUDIT",
            )
            session.add(snap)

            # Update Component table usable stock
            await session.execute(
                update(Component)
                .where(Component.component_id == "COMP-102")
                .values(usable_stock=Decimal("390.0"))
            )

            inc_type = "STOCK_DISCREPANCY"
            severity = "CRITICAL"
            desc = "ERP reports 800 units of COMP-102, but warehouse physical count reveals only 390 usable units (51.2% discrepancy)."

        elif scenario_id == "SCENARIO-3":
            # Scenario 3: Supplier SUP-21 claims DISPATCHED on PO-7730, tracking shows LABEL_CREATED (NO_PICKUP)
            await session.execute(
                update(Shipment)
                .where(Shipment.po_id == "PO-7730")
                .values(
                    shipment_status="LABEL_CREATED",
                    tracking_number="TRK-7730-AIR",
                    label_created_at=now - timedelta(hours=6),
                    pickup_at=None,
                    dispatch_at=None,
                    last_tracking_update=now,
                )
            )
            comm = SupplierCommunication(
                supplier_id="SUP-21",
                po_id="PO-7730",
                message_type="STATUS_UPDATE",
                message_text="Shipment for PO-7730 dispatched via carrier tracking TRK-7730-AIR on schedule.",
                received_at=now,
            )
            session.add(comm)

            sup_msg = SupplierMessage(
                message_id=uuid.uuid4(),
                supplier_id="SUP-21",
                direction="inbound",
                subject="Shipment Dispatched Telemetry – PO-7730",
                body="Shipment dispatched via carrier tracking TRK-7730-AIR on schedule.",
                sent_at=now,
            )
            session.add(sup_msg)

            # Agent inquiry regarding tracking mismatch
            agent_tracking_verify = SupplierMessage(
                message_id=uuid.uuid4(),
                supplier_id="SUP-21",
                direction="outbound",
                subject="Carrier Tracking Mismatch Inquiry – PO-7730",
                body="Autonomous Agent telemetry alert: Discrepancy detected between claim (DISPATCHED) and carrier tracking (LABEL_CREATED / NO_PICKUP on TRK-7730-AIR). Please provide valid carrier pickup receipt.",
                sent_at=now + timedelta(seconds=2),
            )
            session.add(agent_tracking_verify)

            # Record claim mismatch in supplier performance memory
            await record_supplier_performance(
                session,
                "SUP-21",
                on_time=False,
                delay_days=5.0,
                quality_passed=True,
                claim_mismatch=True,
            )

            inc_type = "CLAIM_MISMATCH"
            severity = "HIGH"
            desc = "SUP-21 claimed shipment dispatched, but carrier tracking API confirms only LABEL_CREATED with zero carrier pickup on COMP-105."

        elif scenario_id == "SCENARIO-4":
            # Scenario 4: Cheapest candidate (SUP-21) on COMP-103 has expired ISO certification
            await session.execute(
                update(SupplierMaterial)
                .where(SupplierMaterial.supplier_id == "SUP-21", SupplierMaterial.material_id == "COMP-103")
                .values(certification_valid=False)
            )
            await session.execute(
                update(ContractSupplier)
                .where(ContractSupplier.supplier_id == "SUP-21", ContractSupplier.component_id == "COMP-103")
                .values(certifications=[])
            )
            inc_type = "QUALITY_CONSTRAINT"
            severity = "HIGH"
            desc = "Cheapest candidate supplier SUP-21 offers low price for COMP-103 but lacks valid ISO 9001 certification. Deterministic constraint engine must enforce quality filter."

        elif scenario_id == "SCENARIO-5":
            # Scenario 5: Recovery cost > approval threshold (INR 75,000) on COMP-108
            inc_type = "BUDGET_APPROVAL_REQUIRED"
            severity = "HIGH"
            desc = "Emergency restock plan for COMP-108 estimated at INR 96,000 exceeds autonomous spending threshold (INR 75,000). Human manager sign-off required."

        elif scenario_id == "SCENARIO-6":
            # Scenario 6: High-pressure production risk: line stop in 9.6 hours on PROD-882 (COMP-101)
            await session.execute(
                update(Component)
                .where(Component.component_id == "COMP-101")
                .values(usable_stock=Decimal("20.0"))
            )
            await session.execute(
                update(ProductionOrder)
                .where(ProductionOrder.production_order_id == "PROD-882")
                .values(
                    priority=1,
                    status="IN_PROGRESS",
                )
            )
            await session.execute(
                update(ContractProductionOrder)
                .where(ContractProductionOrder.production_order_id == "PROD-882")
                .values(priority="CRITICAL")
            )
            inc_type = "CRITICAL_PRODUCTION_RISK"
            severity = "CRITICAL"
            desc = "Production line will halt in 9.6 hours on order PROD-882 without immediate partial delivery or split sourcing on COMP-101."

        # =========================================================================
        # 2. Persist Real Disruption Incident in PostgreSQL
        # =========================================================================
        incident = await incident_repo.create_incident(
            session,
            incident_id=incident_id,
            incident_type=inc_type,
            material_id=material_id,
            po_id=po_id,
            supplier_id=supplier_id,
            description=desc,
            severity=severity,
            status="ANALYZING",
            workflow_state={
                "scenario_id": scenario_id,
                "injected_at": now.isoformat(),
                "injected_by": "Scenario Lab Controller",
            },
        )

        await audit_repo.create_audit_event(
            session,
            incident_id=incident_id,
            agent_name="ScenarioLabService",
            event_type="SCENARIO_INJECTED",
            action="disruption_injection",
            input_data={"scenario_id": scenario_id, "material_id": material_id, "po_id": po_id},
            output_data={"incident_id": incident_id, "status": "ANALYZING"},
        )

        await session.commit()

        # =========================================================================
        # 3. Execute Real LangGraph Agent Loop / WorkflowService Pipeline
        # =========================================================================
        analysis_state = await workflow_service.analyze_incident(session, incident_id)
        recommend_state = await workflow_service.recommend_recovery(session, incident_id)

        plans = await recovery_repo.list_plans_for_incident(session, incident_id)
        valid_plans = [p for p in plans if p.status != "INVALID"]

        approval_record = None
        if valid_plans:
            top_plan = valid_plans[0]
            try:
                approval_record = await workflow_service.request_plan_approval(session, top_plan.plan_id)
            except Exception:
                existing = await approval_repo.get_pending_approval_for_plan(session, top_plan.plan_id)
                if not existing:
                    approval_record = await approval_repo.create_approval(
                        session,
                        approval_id=uuid.uuid4().hex[:16],
                        incident_id=incident_id,
                        plan_id=top_plan.plan_id,
                        requested_amount=top_plan.estimated_cost,
                        approval_threshold=Decimal("75000.00"),
                        production_impact=f"Estimated production impact: {top_plan.production_impact_hours} hours",
                        risk_if_rejected="Production disruption risk remains if this recovery plan is rejected",
                        alternatives_considered=[{"plan_type": top_plan.plan_type, "plan_name": top_plan.plan_name}],
                        status="PENDING",
                    )
                else:
                    approval_record = existing

        final_status = "AWAITING_APPROVAL" if approval_record else "PLAN_READY"
        await incident_repo.update_incident_status(session, incident_id, "AWAITING_APPROVAL" if approval_record else "OPEN")

        await session.commit()

        return {
            "success": True,
            "scenario_id": scenario_id,
            "scenario_name": scen_meta["name"],
            "incident_id": incident_id,
            "event_type": inc_type,
            "material_id": material_id,
            "timestamp": now.isoformat(),
            "workflow_status": final_status,
            "plans_generated_count": len(plans),
            "approval_id": approval_record.approval_id if approval_record else None,
            "approval_status": approval_record.status if approval_record else "NOT_REQUIRED",
        }

    async def reset_scenario(self, session: AsyncSession, scenario_id: str) -> dict[str, Any]:
        """Safely reset baseline seed data for repeatable scenario testing."""
        now = datetime.now(timezone.utc)
        if scenario_id == "SCENARIO-1":
            await session.execute(
                update(Component)
                .where(Component.component_id == "COMP-104")
                .values(usable_stock=Decimal("120.0"), safety_stock=Decimal("450.0"))
            )
            await session.execute(
                update(PurchaseOrder)
                .where(PurchaseOrder.po_id == "PO-7712")
                .values(status="in_transit")
            )
            await session.execute(
                update(ContractPurchaseOrder)
                .where(ContractPurchaseOrder.po_id == "PO-7712")
                .values(status="in_transit")
            )
        elif scenario_id == "SCENARIO-2":
            await session.execute(
                update(Component)
                .where(Component.component_id == "COMP-102")
                .values(usable_stock=Decimal("140.0"))
            )
        elif scenario_id == "SCENARIO-4":
            await session.execute(
                update(SupplierMaterial)
                .where(SupplierMaterial.supplier_id == "SUP-21", SupplierMaterial.material_id == "COMP-103")
                .values(certification_valid=True)
            )
        elif scenario_id == "SCENARIO-6":
            await session.execute(
                update(Component)
                .where(Component.component_id == "COMP-101")
                .values(usable_stock=Decimal("40.0"))
            )

        await session.commit()
        return {"success": True, "scenario_id": scenario_id, "message": f"Baseline data reset successfully for {scenario_id}"}
