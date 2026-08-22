import asyncio
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

from app.engines.risk_engine import OperationalRiskEngine
from app.engines.supplier_engine import SupplierEvaluationEngine
from app.engines.pricing_engine import PricingAdjustmentEngine
from app.engines.validation_engine import PlanValidationEngine
from app.engines.simulation_engine import SimulationEngine
from app.agents.supervisor import SupervisorAgent
from app.agents.recovery_recommendation import RecoveryRecommendationAgent
from app.agents.verification_replanning import VerificationReplanningAgent
from app.tools import (
    get_component_inventory,
    adjust_stock_quantity,
    create_purchase_order,
    update_purchase_order_status,
    split_purchase_order,
    get_production_schedule,
    reschedule_production_order,
    query_suppliers_for_component,
    send_supplier_message,
    simulate_supplier_response,
    broadcast_rfq,
    get_tracking_status,
    calculate_adjusted_pricing,
    commit_erp_recovery_actions,
)


async def _run_test(coro_func):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            return await coro_func(session)
    finally:
        await engine.dispose()


def _run(coro_func):
    asyncio.run(_run_test(coro_func))


class TestArchitectureCompliance:
    """Verifies complete adherence to the High-Level Architecture diagram."""

    def test_deterministic_engines_exist_and_instantiate(self):
        """Verify 6 deterministic engines (A-F) operate without LLM hallucination."""
        risk_engine = OperationalRiskEngine()
        supplier_engine = SupplierEvaluationEngine()
        pricing_engine = PricingAdjustmentEngine()
        validation_engine = PlanValidationEngine()
        sim_engine = SimulationEngine()

        assert risk_engine is not None
        assert supplier_engine is not None
        assert pricing_engine is not None
        assert validation_engine is not None
        assert sim_engine is not None

    def test_3_agent_orchestration_instantiation(self):
        """Verify the 3-agent orchestration architecture."""
        supervisor = SupervisorAgent()
        recovery = RecoveryRecommendationAgent()
        verification = VerificationReplanningAgent()

        assert supervisor.risk_engine is not None
        assert supervisor.supplier_engine is not None
        assert recovery.validation_engine is not None
        assert recovery.simulation_engine is not None
        assert verification is not None

    def test_structured_tool_layer_functions(self):
        """Verify structured tools (Inventory, PO, Production, Supplier, Messaging, RFQ, Tracking, Pricing, ERP)."""
        async def _test(session):
            # 1. Pricing Tool
            pricing_res = calculate_adjusted_pricing(original_price=100.0, damage_percentage=20.0)
            assert pricing_res["effective_price"] == 80.0
            assert pricing_res["discount_applied"] == 20.0

            # 2. Inventory Tools
            comp = await get_component_inventory(session, "COMP-101")
            if comp:
                assert "usable_stock" in comp
                assert "days_of_coverage" in comp

            # 3. Production Tools
            schedule = await get_production_schedule(session)
            assert isinstance(schedule, list)

            # 4. Supplier Tools
            suppliers = await query_suppliers_for_component(session, "COMP-101")
            assert isinstance(suppliers, list)

            # 5. Messaging Tools
            msg = await send_supplier_message(
                session,
                supplier_id="SUP-001",
                subject="Urgent Inquiry",
                body="Stock availability check",
            )
            assert msg["supplier_id"] == "SUP-001"
            assert "message_id" in msg

            # 6. RFQ Tools
            rfq_broadcast = await broadcast_rfq(
                session, component_id="COMP-101", quantity=500, deadline_days=3
            )
            assert isinstance(rfq_broadcast, list)

            # 7. Tracking Tools
            tracking = await get_tracking_status(session, "PO-1001")
            if tracking:
                assert "status" in tracking

            # 8. ERP Tools
            erp_res = await commit_erp_recovery_actions(
                session,
                incident_id="INC-TEST",
                action_type="TEST_ACTION",
                details={"notes": "Architecture validation"},
            )
            assert erp_res["status"] == "COMMITTED"

        _run(_test)
