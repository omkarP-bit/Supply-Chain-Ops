import os
import sys
import subprocess
import time
import requests
import pytest

BASE_URL = "http://127.0.0.1:8955"
TIMEOUT = 15


@pytest.fixture(scope="module")
def server():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8955"],
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


class TestContractCoreData:
    def test_inventory_list(self, server):
        s = requests.Session()
        resp = s.get(f"{BASE_URL}/inventory")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 20
        comp_104 = next(i for i in items if i["component_id"] == "COMP-104")
        assert comp_104["usable_stock"] in (120, 390, 480)
        assert comp_104["safety_stock"] == 450

    def test_inventory_single(self, server):
        s = requests.Session()
        resp = s.get(f"{BASE_URL}/inventory/COMP-104")
        assert resp.status_code == 200
        data = resp.json()
        assert data["component_id"] == "COMP-104"
        assert data["name"] == "Precision Aluminum Housing"

    def test_purchase_orders_list(self, server):
        s = requests.Session()
        resp = s.get(f"{BASE_URL}/purchase-orders")
        assert resp.status_code == 200
        pos = resp.json()
        assert len(pos) >= 10
        po_7712 = next(p for p in pos if p["po_id"] == "PO-7712")
        assert po_7712["status"] == "delayed"

    def test_purchase_order_patch_and_optimistic_concurrency(self, server):
        s = requests.Session()
        # Fetch current PO
        resp = s.get(f"{BASE_URL}/purchase-orders/PO-7718")
        assert resp.status_code == 200
        po = resp.json()
        current_version = po["version"]

        # 1. Patch with correct version
        patch_resp = s.patch(
            f"{BASE_URL}/purchase-orders/PO-7718",
            json={"version": current_version, "status": "delivered"},
        )
        assert patch_resp.status_code == 200
        updated = patch_resp.json()
        assert updated["status"] == "delivered"
        assert updated["version"] == current_version + 1

        # 2. Patch with stale version -> should return 409 Conflict
        stale_resp = s.patch(
            f"{BASE_URL}/purchase-orders/PO-7718",
            json={"version": current_version, "status": "in_transit"},
        )
        assert stale_resp.status_code == 409

    def test_production_schedule(self, server):
        s = requests.Session()
        resp = s.get(f"{BASE_URL}/production-schedule")
        assert resp.status_code == 200
        orders = resp.json()
        assert len(orders) >= 5
        prod_882 = next(o for o in orders if o["production_order_id"] == "PROD-882")
        assert prod_882["required_component"] == "COMP-104"

    def test_supplier_messages(self, server):
        s = requests.Session()
        resp = s.get(f"{BASE_URL}/supplier-messages")
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) >= 5


class TestAlertEngineAndEscalations:
    def test_alert_scan_triggers_5_rules(self, server):
        s = requests.Session()
        # Trigger alert scan
        scan_resp = s.post(f"{BASE_URL}/alerts/scan")
        assert scan_resp.status_code == 200

        # Query all alerts
        alerts_resp = s.get(f"{BASE_URL}/alerts")
        assert alerts_resp.status_code == 200
        alerts = alerts_resp.json()
        assert len(alerts) >= 5

        alert_types = {a["type"] for a in alerts}
        assert "po_delayed" in alert_types or "inventory_below_safety_stock" in alert_types
        assert "budget_approval_required" in alert_types or "production_schedule_at_risk" in alert_types

    def test_escalations_and_resolve(self, server):
        s = requests.Session()
        # Get pending escalations
        resp = s.get(f"{BASE_URL}/escalations?status=pending")
        assert resp.status_code == 200
        escalations = resp.json()
        assert len(escalations) >= 1

        esc = escalations[0]
        esc_id = esc["escalation_id"]

        # Resolve escalation (Approve)
        res_resp = s.post(
            f"{BASE_URL}/escalations/{esc_id}/resolve",
            json={"decision": "approve", "note": "Approved by Procurement Director"},
        )
        assert res_resp.status_code == 200
        resolved = res_resp.json()
        assert resolved["status"] == "approved"

        # Verify in audit log
        audit_resp = s.get(f"{BASE_URL}/audit-log")
        assert audit_resp.status_code == 200
        logs = audit_resp.json()
        assert any(l["event_type"] == "escalation_resolved" for l in logs)
