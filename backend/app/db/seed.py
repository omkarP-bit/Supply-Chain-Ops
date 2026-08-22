from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.materials import Material, MaterialSpecification, MaterialSpecParameter
from app.db.models.suppliers import (
    Supplier,
    SupplierMaterial,
    SupplierPerformance,
    SupplierCommunication,
)
from app.db.models.production import ProductionOrder, ProductionConsumption
from app.db.models.inventory import InventorySnapshot, InventoryMovement
from app.db.models.procurement import PurchaseOrder, Shipment
from app.db.models.risk import RiskThreshold


async def seed_db(session: AsyncSession) -> None:
    existing = await session.execute(
        select(func.count()).select_from(Material)
    )
    if existing.scalar() > 0:
        return

    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Materials
    mat_104 = Material(
        material_id="COMP-104",
        material_code="MAT-COMP-104",
        material_name="Precision Aluminum Housing",
        category="COMPONENTS",
        unit_of_measure="UNIT",
        criticality_level="CRITICAL",
        required_quality_level="AQL_1_0",
        required_certification="ISO_9001",
        safety_stock=Decimal("450.00"),
        reorder_point=Decimal("500.00"),
        lead_time_target_days=3,
    )
    mat_101 = Material(
        material_id="COMP-101",
        material_code="MAT-COMP-101",
        material_name="Standard Fastener Kit",
        category="COMPONENTS",
        unit_of_measure="KIT",
        criticality_level="MEDIUM",
        required_quality_level="AQL_2_5",
        safety_stock=Decimal("200.00"),
        reorder_point=Decimal("250.00"),
        lead_time_target_days=7,
    )
    mat_105 = Material(
        material_id="COMP-105",
        material_code="MAT-COMP-105",
        material_name="Sensor Module",
        category="ELECTRONICS",
        unit_of_measure="UNIT",
        criticality_level="HIGH",
        required_quality_level="AQL_1_0",
        required_certification="ISO_9001",
        safety_stock=Decimal("300.00"),
        reorder_point=Decimal("350.00"),
        lead_time_target_days=5,
    )
    session.add_all([mat_104, mat_101, mat_105])
    await session.flush()

    # Material Specification for COMP-104
    spec_104 = MaterialSpecification(
        material_id="COMP-104",
        material_grade="AL-6061-T6",
        dimensions="120x80x40mm",
        aql_level="AQL_1_0",
        inspection_standard="ISO_9001",
        required_certifications=["ISO_9001"],
    )
    session.add(spec_104)
    await session.flush()

    # MaterialSpecParameters for COMP-104
    params = [
        MaterialSpecParameter(
            specification_id=spec_104.specification_id,
            parameter_name="Hardness",
            parameter_type="NUMERIC",
            min_value=Decimal("95.0000"),
            max_value=Decimal("110.0000"),
            unit="HB",
            mandatory=True,
        ),
        MaterialSpecParameter(
            specification_id=spec_104.specification_id,
            parameter_name="Tensile Strength",
            parameter_type="NUMERIC",
            min_value=Decimal("290.0000"),
            max_value=Decimal("310.0000"),
            unit="MPa",
            mandatory=True,
        ),
        MaterialSpecParameter(
            specification_id=spec_104.specification_id,
            parameter_name="Surface Roughness",
            parameter_type="NUMERIC",
            min_value=Decimal("0.0000"),
            max_value=Decimal("0.8000"),
            unit="um",
            mandatory=True,
        ),
    ]
    session.add_all(params)
    await session.flush()

    # Suppliers
    sup_21 = Supplier(
        supplier_id="SUP-21",
        supplier_code="SUP-BM-021",
        supplier_name="Budget Metals Co",
        status="ACTIVE",
        overall_reliability_score=Decimal("62.00"),
        on_time_delivery_rate=Decimal("0.5800"),
        quality_score=Decimal("55.00"),
        average_lead_time_days=5,
        risk_level="HIGH",
    )
    sup_34 = Supplier(
        supplier_id="SUP-34",
        supplier_code="SUP-PA-034",
        supplier_name="Precision Alloys Ltd",
        status="ACTIVE",
        overall_reliability_score=Decimal("94.00"),
        on_time_delivery_rate=Decimal("0.9600"),
        quality_score=Decimal("92.00"),
        average_lead_time_days=2,
        risk_level="LOW",
    )
    sup_41 = Supplier(
        supplier_id="SUP-41",
        supplier_code="SUP-GC-041",
        supplier_name="Global Components Inc",
        status="ACTIVE",
        overall_reliability_score=Decimal("85.00"),
        on_time_delivery_rate=Decimal("0.8700"),
        quality_score=Decimal("84.00"),
        average_lead_time_days=4,
        risk_level="LOW",
    )
    sup_52 = Supplier(
        supplier_id="SUP-52",
        supplier_code="SUP-QP-052",
        supplier_name="QuickParts Depot",
        status="ACTIVE",
        overall_reliability_score=Decimal("78.00"),
        on_time_delivery_rate=Decimal("0.8000"),
        quality_score=Decimal("75.00"),
        average_lead_time_days=8,
        risk_level="MEDIUM",
    )
    sup_77 = Supplier(
        supplier_id="SUP-77",
        supplier_code="SUP-DP-077",
        supplier_name="Defunct Parts",
        status="INACTIVE",
        overall_reliability_score=Decimal("12.00"),
        on_time_delivery_rate=Decimal("0.1500"),
        quality_score=Decimal("20.00"),
        average_lead_time_days=30,
        risk_level="CRITICAL",
    )
    session.add_all([sup_21, sup_34, sup_41, sup_52, sup_77])
    await session.flush()

    # SupplierMaterials for COMP-104
    sm_21 = SupplierMaterial(
        supplier_id="SUP-21",
        material_id="COMP-104",
        available_quantity=Decimal("1200.00"),
        reserved_quantity=Decimal("0.00"),
        available_to_promise=Decimal("1200.00"),
        unit_price=Decimal("105.00"),
        lead_time_days=5,
        aql_level="AQL_2_5",
        material_grade="AL-6061",
        certification_valid=False,
    )
    sm_34 = SupplierMaterial(
        supplier_id="SUP-34",
        material_id="COMP-104",
        available_quantity=Decimal("900.00"),
        reserved_quantity=Decimal("50.00"),
        available_to_promise=Decimal("850.00"),
        unit_price=Decimal("120.00"),
        lead_time_days=2,
        expedited_lead_time_days=1,
        aql_level="AQL_1_0",
        material_grade="AL-6061-T6",
        certification_valid=True,
        certification_expiry=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )
    sm_41 = SupplierMaterial(
        supplier_id="SUP-41",
        material_id="COMP-104",
        available_quantity=Decimal("500.00"),
        reserved_quantity=Decimal("0.00"),
        available_to_promise=Decimal("500.00"),
        unit_price=Decimal("118.00"),
        minimum_order_quantity=Decimal("100.00"),
        maximum_order_quantity=Decimal("400.00"),
        lead_time_days=4,
        aql_level="AQL_1_0",
        certification_valid=True,
    )
    sm_52 = SupplierMaterial(
        supplier_id="SUP-52",
        material_id="COMP-104",
        available_quantity=Decimal("100.00"),
        reserved_quantity=Decimal("0.00"),
        available_to_promise=Decimal("100.00"),
        unit_price=Decimal("99.00"),
        minimum_order_quantity=Decimal("200.00"),
        lead_time_days=8,
        aql_level="AQL_4_0",
    )
    session.add_all([sm_21, sm_34, sm_41, sm_52])
    await session.flush()

    # ProductionOrders
    yesterday = today - timedelta(days=1)
    in_3d = today + timedelta(days=3)
    in_5d = today + timedelta(days=5)

    prod_882 = ProductionOrder(
        production_order_id="PROD-882",
        product_id="PROD-882",
        priority=1,
        status="IN_PROGRESS",
        planned_quantity=Decimal("2000.00"),
        completed_quantity=Decimal("950.00"),
        remaining_quantity=Decimal("1050.00"),
        planned_start=yesterday,
        planned_end=in_3d,
        production_rate_per_hour=Decimal("26.00"),
        line_id="LINE-1",
    )
    prod_885 = ProductionOrder(
        production_order_id="PROD-885",
        product_id="PROD-885",
        priority=3,
        status="PLANNED",
        planned_quantity=Decimal("1500.00"),
        completed_quantity=Decimal("0.00"),
        remaining_quantity=Decimal("1500.00"),
        planned_start=in_3d,
        planned_end=in_5d,
        production_rate_per_hour=Decimal("22.00"),
        line_id="LINE-2",
    )
    session.add_all([prod_882, prod_885])
    await session.flush()

    # ProductionConsumption
    consumption = ProductionConsumption(
        production_order_id="PROD-882",
        material_id="COMP-104",
        quantity_consumed=Decimal("950.00"),
        consumption_timestamp=now,
        unit="UNIT",
    )
    session.add(consumption)
    await session.flush()

    # InventorySnapshots for COMP-104 (days -34 to 0)
    for i in range(35):
        snap_date = today - timedelta(days=34 - i)
        if i < 34:
            qty = Decimal(str(1500 - i * 18))
            session.add(
                InventorySnapshot(
                    material_id="COMP-104",
                    warehouse_id="WH-MAIN",
                    snapshot_date=snap_date,
                    erp_quantity=qty,
                    physical_quantity=qty,
                    usable_quantity=qty,
                    available_quantity=qty,
                    source="ERP",
                )
            )
        else:
            session.add(
                InventorySnapshot(
                    material_id="COMP-104",
                    warehouse_id="WH-MAIN",
                    snapshot_date=snap_date,
                    erp_quantity=Decimal("800.00"),
                    physical_quantity=Decimal("390.00"),
                    usable_quantity=Decimal("390.00"),
                    available_quantity=Decimal("390.00"),
                    source="PHYSICAL_COUNT",
                )
            )
    await session.flush()

    # InventoryMovements for COMP-104
    for i in range(35):
        mov_date = today - timedelta(days=34 - i)
        if i >= 28:
            qty = Decimal("-100.00")
        else:
            qty = Decimal("-90.00")
        session.add(
            InventoryMovement(
                material_id="COMP-104",
                warehouse_id="WH-MAIN",
                movement_type="CONSUMPTION",
                quantity=qty,
                reference_type="PRODUCTION_ORDER",
                reference_id="PROD-882",
                movement_timestamp=mov_date.replace(hour=10, minute=0),
                source_system="ERP",
                reason="Daily production consumption",
            )
        )

    # 3 RECEIPT movements
    receipt_dates = [
        today - timedelta(days=20),
        today - timedelta(days=10),
        today - timedelta(days=5),
    ]
    for idx, rd in enumerate(receipt_dates):
        session.add(
            InventoryMovement(
                material_id="COMP-104",
                warehouse_id="WH-MAIN",
                movement_type="RECEIPT",
                quantity=Decimal("800.00"),
                reference_type="PURCHASE_ORDER",
                reference_id=f"PO-77{10 + idx}",
                movement_timestamp=rd.replace(hour=14, minute=30),
                source_system="WMS",
                reason=f"PO receipt batch {idx + 1}",
            )
        )
    await session.flush()

    # PurchaseOrder
    order_date = today - timedelta(days=7)
    expected_date = today + timedelta(days=2)

    po_7712 = PurchaseOrder(
        po_id="PO-7712",
        po_number="PO-7712",
        supplier_id="SUP-21",
        material_id="COMP-104",
        ordered_quantity=Decimal("800.00"),
        received_quantity=Decimal("0.00"),
        remaining_quantity=Decimal("800.00"),
        unit_price=Decimal("105.00"),
        total_cost=Decimal("84000.00"),
        order_date=order_date,
        expected_delivery_date=expected_date,
        status="DELAYED",
        priority="HIGH",
        production_order_id="PROD-882",
    )
    session.add(po_7712)
    await session.flush()

    # Shipment
    session.add(
        Shipment(
            shipment_id="SH-5501",
            po_id="PO-7712",
            tracking_number="TRACK-21-7712",
            shipment_status="LABEL_CREATED",
            carrier="FastFreight",
            label_created_at=now - timedelta(hours=6),
        )
    )
    await session.flush()

    # SupplierCommunication
    session.add(
        SupplierCommunication(
            supplier_id="SUP-21",
            po_id="PO-7712",
            message_type="STATUS_UPDATE",
            message_text="Order dispatched",
            claimed_status="DISPATCHED",
            claimed_quantity=Decimal("800.00"),
            claimed_eta=now + timedelta(days=1),
            received_at=now - timedelta(hours=3),
            channel="EMAIL",
        )
    )
    await session.flush()

    # SupplierPerformance
    perf_21 = SupplierPerformance(
        supplier_id="SUP-21",
        evaluation_date=now,
        orders_completed=45,
        orders_on_time=26,
        orders_late=19,
        average_delay_days=Decimal("2.30"),
        quality_rejection_rate=Decimal("0.0800"),
        eta_change_count=7,
        claim_mismatch_count=4,
        tracking_discrepancy_count=5,
        average_response_time=Decimal("4.50"),
        reliability_score=Decimal("62.00"),
        quality_score=Decimal("55.00"),
    )
    perf_34 = SupplierPerformance(
        supplier_id="SUP-34",
        evaluation_date=now,
        orders_completed=120,
        orders_on_time=115,
        orders_late=5,
        average_delay_days=Decimal("0.20"),
        quality_rejection_rate=Decimal("0.0100"),
        eta_change_count=1,
        claim_mismatch_count=0,
        tracking_discrepancy_count=0,
        average_response_time=Decimal("1.00"),
        reliability_score=Decimal("94.00"),
        quality_score=Decimal("92.00"),
    )
    session.add_all([perf_21, perf_34])
    await session.flush()

    # RiskThresholds for COMP-104
    thresholds = [
        RiskThreshold(
            material_id="COMP-104",
            metric_name="inventory_coverage_days",
            warning_threshold=Decimal("7.0000"),
            critical_threshold=Decimal("3.0000"),
            unit="days",
            comparison_operator="<",
            severity="WARNING",
            active=True,
        ),
        RiskThreshold(
            material_id="COMP-104",
            metric_name="inventory_discrepancy_percentage",
            warning_threshold=Decimal("5.0000"),
            critical_threshold=Decimal("20.0000"),
            unit="percent",
            comparison_operator="<",
            severity="WARNING",
            active=True,
        ),
        RiskThreshold(
            material_id="COMP-104",
            metric_name="supplier_reliability_score",
            warning_threshold=Decimal("75.0000"),
            critical_threshold=Decimal("50.0000"),
            unit="score",
            comparison_operator="<",
            severity="WARNING",
            active=True,
        ),
    ]
    session.add_all(thresholds)

    await session.commit()
