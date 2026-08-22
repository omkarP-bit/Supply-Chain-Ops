"""
Phase 12: End-to-end scenario integration tests.

Uses subprocess-based testing (starts uvicorn, hits with requests).
Tests 6 disruption scenarios against COMP-104 seed data.
"""
import os
import sys
import subprocess
import time
import requests
import pytest

BASE_URL = "http://127.0.0.1:8951"
TIMEOUT = 15


@pytest.fixture(scope="module")
def server():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8951"],
        cwd=backend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


def _create_incident(s, **overrides) -> str:
    payload = {
        "incident_type": "SUPPLY_DISRUPTION",
        "material_id": "COMP-104",
        "po_id": "PO-7712",
        "description": "Supplier delayed",
    }
    payload.update(overrides)
    resp = s.post(f"{BASE_URL}/api/v1/incidents", json=payload)
    assert resp.status_code == 201, f"Create failed: {resp.status_code} {resp.text}"
    return resp.json()["incident_id"]


def _analyze(s, incident_id: str) -> dict:
    resp = s.post(f"{BASE_URL}/api/v1/incidents/{incident_id}/analyze")
    assert resp.status_code == 200
    return resp.json()


def _recommend(s, incident_id: str) -> list:
    resp = s.post(f"{BASE_URL}/api/v1/incidents/{incident_id}/recommend")
    assert resp.status_code == 200
    return resp.json()


class TestScenario1SupplierDelay:
    def test_supplier_delay_full_workflow(self, server):
        s = requests.Session()
        incident_id = _create_incident(s)
        analysis = _analyze(s, incident_id)
        assert "risk_report" in analysis
        assert "eligible_suppliers" in analysis
        risk = analysis["risk_report"]
        assert risk["risk_level"] == "CRITICAL", f"Expected CRITICAL risk, got {risk['risk_level']}"
        plans = _recommend(s, incident_id)
        assert len(plans) > 0, "No recovery plans generated for supplier delay"
        assert plans[0]["plan_type"] == "EMERGENCY_PROCUREMENT"


class TestScenario2StaleInventory:
    def test_stale_inventory_high_discrepancy(self, server):
        s = requests.Session()
        incident_id = _create_incident(s)
        analysis = _analyze(s, incident_id)
        risk = analysis["risk_report"]
        disc_pct = risk["discrepancy_percentage"]
        assert disc_pct > 50.0, f"Expected discrepancy > 50%, got {disc_pct}"


class TestScenario3ClaimMismatch:
    def test_claim_mismatch_analysis(self, server):
        s = requests.Session()
        incident_id = _create_incident(
            s,
            incident_type="CLAIM_MISMATCH",
            description="SUP-21 claims dispatched, tracking says label_created",
        )
        analysis = _analyze(s, incident_id)
        assert "risk_report" in analysis
        assert "eligible_suppliers" in analysis
        risk = analysis["risk_report"]
        assert risk["material_id"] == "COMP-104"


class TestScenario4QualityConstraint:
    def test_rejected_supplier_has_zero_score(self, server):
        s = requests.Session()
        incident_id = _create_incident(s)
        analysis = _analyze(s, incident_id)
        suppliers = analysis["eligible_suppliers"]
        sup21 = [x for x in suppliers if x["supplier_id"] == "SUP-21"]
        assert len(sup21) == 1, "SUP-21 should appear in eligible suppliers"
        assert sup21[0]["score"] == 0, "SUP-21 should have score 0 (rejected)"
        assert sup21[0]["rejection_reason"] is not None, (
            "SUP-21 should have a rejection reason"
        )


class TestScenario5BudgetApproval:
    def test_dashboard_approvals(self, server):
        s = requests.Session()
        resp = s.get(f"{BASE_URL}/api/v1/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "pending_approvals_count" in data
        assert isinstance(data["pending_approvals_count"], int)

    def test_approvals_list(self, server):
        s = requests.Session()
        resp = s.get(f"{BASE_URL}/api/v1/approvals")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestScenario6ProductionRisk:
    def test_production_risk_and_recovery(self, server):
        s = requests.Session()
        incident_id = _create_incident(s)
        analysis = _analyze(s, incident_id)
        risk = analysis["risk_report"]
        hours = risk["hours_to_production_stop"]
        assert hours < 200, f"Expected hours_to_production_stop < 200, got {hours}"
        plans = _recommend(s, incident_id)
        plan_types = {p["plan_type"] for p in plans}
        assert len(plan_types) >= 1, "Should have at least one plan type"
