import pytest
import pytest_asyncio

from app.config import settings
from app.db.session import get_engine, reset_engine
from app.graph import graph


def _initial_state() -> dict:
    return {
        "incident_type": "SUPPLY_DISRUPTION",
        "material_id": "COMP-104",
        "po_id": "PO-7712",
        "supplier_id": "SUP-21",
        "description": "LangGraph database integration test",
        "severity": "HIGH",
        "risk_report": None,
        "eligible_suppliers": [],
        "proposed_plans": [],
        "selected_plan": None,
        "validation_results": [],
        "simulation_results": [],
        "verification_status": None,
        "status": "NEW",
        "logs": [],
    }


@pytest_asyncio.fixture(autouse=True)
async def reset_database_engine():
    yield
    await get_engine().dispose()
    reset_engine()


@pytest.mark.asyncio
async def test_graph_consumes_database_risk_and_supplier_data(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "llm_api_key", "")

    result = await graph.ainvoke(_initial_state())

    assert result["risk_report"]["material_id"] == "COMP-104"
    assert result["risk_report"]["erp_quantity"] == 800.0
    assert result["risk_report"]["physical_quantity"] == 390.0
    assert len(result["eligible_suppliers"]) == 4
    assert any(s["supplier_id"] == "SUP-21" for s in result["eligible_suppliers"])


@pytest.mark.asyncio
async def test_graph_uses_real_validation_and_stops_for_approval(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "llm_api_key", "")

    result = await graph.ainvoke(_initial_state())

    assert result["proposed_plans"]
    assert len(result["validation_results"]) == len(result["proposed_plans"])
    assert len(result["simulation_results"]) == len(result["proposed_plans"])
    assert all("violations" in item for item in result["validation_results"])
    assert all("coverage_after_recovery" in item for item in result["simulation_results"])
    assert result["approval_id"]
    assert result["status"] == "AWAITING_APPROVAL"
