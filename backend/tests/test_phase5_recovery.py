"""
Phase 5: Recovery Agent API integration tests.

Uses subprocess-based testing (starts uvicorn, hits with requests)
because asyncpg pool connections are bound to one event loop.
"""
import os
import sys
import subprocess
import time
import requests
import pytest

BASE_URL = "http://127.0.0.1:8950"
TIMEOUT = 15


@pytest.fixture(scope="module")
def server():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8950"],
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


class TestAnalyzeIncident:
    def test_analyze_incident(self, server):
        s = requests.Session()
        incident_id = _create_incident(s)
        resp = s.post(f"{BASE_URL}/api/v1/incidents/{incident_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_report" in data
        assert "eligible_suppliers" in data
        risk = data["risk_report"]
        assert risk["material_id"] == "COMP-104"
        assert risk["risk_level"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE")
        assert risk["coverage_days"] >= 0
        assert risk["hours_to_production_stop"] >= 0
        assert len(data["eligible_suppliers"]) >= 2


class TestRecommendRecovery:
    def test_recommend_recovery(self, server):
        s = requests.Session()
        incident_id = _create_incident(s)
        resp = s.post(f"{BASE_URL}/api/v1/incidents/{incident_id}/recommend")
        assert resp.status_code == 200
        plans = resp.json()
        assert isinstance(plans, list)
        assert len(plans) > 0
        plan = plans[0]
        assert "plan_id" in plan
        assert "plan_name" in plan
        assert "plan_type" in plan
        assert plan["plan_type"] in ("EMERGENCY_PROCUREMENT", "PRODUCTION_ADJUSTMENT", "MONITORING")
        assert float(plan["overall_score"]) > 0


class TestGetPlans:
    def test_get_plans(self, server):
        s = requests.Session()
        incident_id = _create_incident(s)
        s.post(f"{BASE_URL}/api/v1/incidents/{incident_id}/recommend")
        resp = s.get(f"{BASE_URL}/api/v1/incidents/{incident_id}/plans")
        assert resp.status_code == 200
        plans = resp.json()
        assert isinstance(plans, list)
        assert len(plans) > 0


class TestIncidentNotFound:
    def test_analyze_nonexistent(self, server):
        s = requests.Session()
        resp = s.post(f"{BASE_URL}/api/v1/incidents/nonexistent/analyze")
        assert resp.status_code == 404

    def test_recommend_nonexistent(self, server):
        s = requests.Session()
        resp = s.post(f"{BASE_URL}/api/v1/incidents/nonexistent/recommend")
        assert resp.status_code == 404
