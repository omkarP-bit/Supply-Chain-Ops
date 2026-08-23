import pytest
import pytest_asyncio

from app.config import settings
from app.db.repositories import approval_repo
from app.db.session import get_engine, get_session_factory, reset_engine
from app.graph import graph
from app.services.workflow_service import WorkflowService


@pytest_asyncio.fixture(autouse=True)
async def reset_database_engine():
    yield
    await get_engine().dispose()
    reset_engine()


@pytest.mark.asyncio
async def test_rejected_plan_cannot_execute_then_approved_plan_executes(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "llm_api_key", "")

    state = {
        "incident_type": "SUPPLY_DISRUPTION",
        "material_id": "COMP-104",
        "po_id": "PO-7712",
        "supplier_id": "SUP-21",
        "description": "approval workflow integration test",
        "severity": "HIGH",
        "risk_report": None,
        "eligible_suppliers": [],
        "proposed_plans": [],
        "selected_plan": None,
        "validation_results": [],
        "simulation_results": [],
        "verification_status": None,
        "approval_id": None,
        "status": "NEW",
        "logs": [],
    }
    result = await graph.ainvoke(state)
    plan_id = result["selected_plan"]["plan_id"]
    first_approval_id = result["approval_id"]
    assert first_approval_id

    factory = get_session_factory()
    service = WorkflowService()
    async with factory() as session:
        rejected = await approval_repo.update_approval_decision(
            session, first_approval_id, "REJECTED", "test-user", "too expensive"
        )
        assert rejected.status == "REJECTED"
        with pytest.raises(ValueError, match="not approved"):
            await service.execute_plan(session, plan_id, first_approval_id)

        second = await service.request_plan_approval(session, plan_id)
        assert second.status == "PENDING"
        approved = await approval_repo.update_approval_decision(
            session, second.approval_id, "APPROVED", "test-user", "approved"
        )
        assert approved.status == "APPROVED"
        execution = await service.execute_plan(session, plan_id, second.approval_id)

    assert execution["status"] == "COMPLETED"
    assert execution["po_id"]
