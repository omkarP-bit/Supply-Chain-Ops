import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy import select

from app.db.session import get_session_factory, get_engine, reset_engine
from app.db.models.contract_models import Component
from app.db.models.procurement import PurchaseOrder, Shipment
from app.db.models.suppliers import Supplier, SupplierMaterial, SupplierCommunication, SupplierPerformance
from app.db.models.workflow import Incident, RecoveryPlan, ApprovalRequest
from app.db.repositories import incident_repo, recovery_repo, approval_repo, audit_repo
from app.services.scenario_service import ScenarioService
from app.services.workflow_service import WorkflowService


@pytest_asyncio.fixture(autouse=True)
async def reset_database_engine():
    yield
    await get_engine().dispose()
    reset_engine()


@pytest.mark.asyncio
async def test_scenario_list():
    factory = get_session_factory()
    async with factory() as session:
        service = ScenarioService()
        scenarios = await service.list_scenarios(session)
        assert len(scenarios) == 6
        assert [s["scenario_id"] for s in scenarios] == [
            "SCENARIO-1",
            "SCENARIO-2",
            "SCENARIO-3",
            "SCENARIO-4",
            "SCENARIO-5",
            "SCENARIO-6",
        ]


@pytest.mark.asyncio
async def test_scenario_1_normal_disruption():
    factory = get_session_factory()
    async with factory() as session:
        service = ScenarioService()
        res = await service.inject_scenario(session, "SCENARIO-1")
        assert res["success"] is True
        assert res["scenario_id"] == "SCENARIO-1"
        assert res["material_id"] == "COMP-104"
        assert res["event_type"] == "SUPPLIER_DELAY"

        # Verify PO-7712 was updated in DB
        po = await session.get(PurchaseOrder, "PO-7712")
        assert po is not None
        assert po.status == "delayed"

        # Verify Incident and Recovery Plans were created
        incident = await incident_repo.get_incident(session, res["incident_id"])
        assert incident is not None
        assert incident.material_id == "COMP-104"

        plans = await recovery_repo.list_plans_for_incident(session, res["incident_id"])
        assert len(plans) > 0


@pytest.mark.asyncio
async def test_scenario_2_stale_inventory():
    factory = get_session_factory()
    async with factory() as session:
        service = ScenarioService()
        res = await service.inject_scenario(session, "SCENARIO-2")
        assert res["success"] is True
        assert res["scenario_id"] == "SCENARIO-2"
        assert res["event_type"] == "STOCK_DISCREPANCY"
        assert res["material_id"] == "COMP-102"

        # Verify COMP-102 usable stock in DB is 390
        comp = await session.get(Component, "COMP-102")
        assert comp is not None
        assert float(comp.usable_stock) == 390.0

        # Verify Incident recorded
        incident = await incident_repo.get_incident(session, res["incident_id"])
        assert incident is not None
        assert incident.severity == "CRITICAL"


@pytest.mark.asyncio
async def test_scenario_3_adversarial_supplier_claim():
    factory = get_session_factory()
    async with factory() as session:
        service = ScenarioService()
        res = await service.inject_scenario(session, "SCENARIO-3")
        assert res["success"] is True
        assert res["scenario_id"] == "SCENARIO-3"
        assert res["event_type"] == "CLAIM_MISMATCH"
        assert res["material_id"] == "COMP-105"

        # Verify Shipment status in DB is LABEL_CREATED
        shipment_res = await session.execute(
            select(Shipment).where(Shipment.po_id == "PO-7730")
        )
        shipment = shipment_res.scalar_one_or_none()
        assert shipment is not None
        assert shipment.shipment_status == "LABEL_CREATED"
        assert shipment.pickup_at is None


@pytest.mark.asyncio
async def test_scenario_4_quality_constraint():
    factory = get_session_factory()
    async with factory() as session:
        service = ScenarioService()
        res = await service.inject_scenario(session, "SCENARIO-4")
        assert res["success"] is True
        assert res["scenario_id"] == "SCENARIO-4"
        assert res["event_type"] == "QUALITY_CONSTRAINT"
        assert res["material_id"] == "COMP-103"

        # Verify SUP-18 has invalid certification for COMP-103
        sm_res = await session.execute(
            select(SupplierMaterial).where(
                SupplierMaterial.supplier_id == "SUP-21",
                SupplierMaterial.material_id == "COMP-103",
            )
        )
        sm = sm_res.scalar_one_or_none()
        assert sm is not None
        assert sm.certification_valid is False


@pytest.mark.asyncio
async def test_scenario_5_budget_approval_required():
    factory = get_session_factory()
    async with factory() as session:
        service = ScenarioService()
        res = await service.inject_scenario(session, "SCENARIO-5")
        assert res["success"] is True
        assert res["scenario_id"] == "SCENARIO-5"
        assert res["event_type"] == "BUDGET_APPROVAL_REQUIRED"

        # Verify approval was created and is pending
        appr_res = await session.execute(
            select(ApprovalRequest).where(ApprovalRequest.incident_id == res["incident_id"])
        )
        appr = appr_res.scalar_one_or_none()
        assert appr is not None
        assert appr.status == "PENDING"
        assert float(appr.approval_threshold) == 75000.0


@pytest.mark.asyncio
async def test_scenario_6_high_pressure_production_risk():
    factory = get_session_factory()
    async with factory() as session:
        service = ScenarioService()
        res = await service.inject_scenario(session, "SCENARIO-6")
        assert res["success"] is True
        assert res["scenario_id"] == "SCENARIO-6"
        assert res["material_id"] == "COMP-101"
        assert res["event_type"] == "CRITICAL_PRODUCTION_RISK"

        # Verify COMP-101 usable stock in DB is 20
        comp = await session.get(Component, "COMP-101")
        assert comp is not None
        assert float(comp.usable_stock) == 20.0
