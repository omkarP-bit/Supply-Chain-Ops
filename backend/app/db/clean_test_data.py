import sys
import asyncio
from sqlalchemy import text

sys.path.insert(0, 'backend')
from app.db.session import get_session_factory


async def clean_database():
    async with get_session_factory()() as s:
        # 1. Clear test executions, verifications, approvals, plans, incidents, audit events
        tables_to_clear = [
            'approval_requests',
            'recovery_plans',
            'incidents',
            'audit_events',
            'escalations',
            'alerts',
            'supplier_messages',
            'supplier_communications',
        ]
        for tbl in tables_to_clear:
            await s.execute(text(f'DELETE FROM {tbl}'))
            print(f'Cleared table: {tbl}')

        # 2. Reset components to healthy baseline stock
        await s.execute(text('UPDATE components SET usable_stock = current_stock WHERE current_stock > 0'))
        await s.execute(text("UPDATE components SET usable_stock = 480, safety_stock = 450 WHERE component_id = 'COMP-104'"))
        await s.execute(text("UPDATE components SET usable_stock = 300, safety_stock = 200 WHERE component_id = 'COMP-101'"))
        await s.execute(text("UPDATE components SET usable_stock = 250, safety_stock = 150 WHERE component_id = 'COMP-102'"))
        await s.execute(text("UPDATE components SET usable_stock = 400, safety_stock = 250 WHERE component_id = 'COMP-103'"))
        await s.execute(text("UPDATE components SET usable_stock = 350, safety_stock = 200 WHERE component_id = 'COMP-105'"))
        await s.execute(text("UPDATE components SET usable_stock = 300, safety_stock = 180 WHERE component_id = 'COMP-108'"))

        # 3. Reset PO statuses to healthy in_transit / CONFIRMED
        await s.execute(text("UPDATE purchase_orders SET status = 'CONFIRMED' WHERE status != 'CONFIRMED'"))
        await s.execute(text("UPDATE contract_purchase_orders SET status = 'in_transit' WHERE status != 'in_transit'"))

        # 4. Reset supplier certifications
        await s.execute(text('UPDATE supplier_materials SET certification_valid = true WHERE certification_valid = false'))
        await s.execute(text("UPDATE contract_suppliers SET certifications = '[\"ISO-9001\", \"IATF-16949\"]'::jsonb WHERE certifications IS NULL OR certifications = '[]'::jsonb"))

        # 5. Reset production order priorities
        await s.execute(text("UPDATE production_orders SET priority = 5, status = 'PLANNED' WHERE production_order_id = 'PROD-882'"))
        await s.execute(text("UPDATE contract_production_orders SET priority = 'NORMAL' WHERE production_order_id = 'PROD-882'"))

        await s.commit()
        print('Database cleaned and reset to pristine baseline successfully!')


if __name__ == '__main__':
    asyncio.run(clean_database())
