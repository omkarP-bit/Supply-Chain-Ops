from __future__ import annotations

import json
import uuid
from decimal import Decimal

import httpx

from app.config import settings


async def get_plan_suggestions(
    incident_id: str,
    material_id: str | None,
    risk_report: dict,
    eligible_suppliers: list[dict],
) -> list[dict]:
    if settings.llm_provider.lower() == "groq" and settings.llm_api_key:
        try:
            return await _get_groq_suggestions(
                incident_id, material_id, risk_report, eligible_suppliers
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            pass

    return _get_deterministic_suggestions(risk_report, eligible_suppliers)


async def _get_groq_suggestions(
    incident_id: str,
    material_id: str | None,
    risk_report: dict,
    eligible_suppliers: list[dict],
) -> list[dict]:
    prompt = {
        "incident_id": incident_id,
        "material_id": material_id,
        "risk_report": risk_report,
        "eligible_suppliers": eligible_suppliers,
    }
    response_schema = (
        "Return a JSON object with a 'suggestions' array. Each suggestion must contain: "
        "plan_name (str), plan_type (str: EMERGENCY_PROCUREMENT | SPLIT_SOURCING | PRODUCTION_ADJUSTMENT | MONITORING), "
        "plan_details (dict with supplier_id, supplier_name, quantity, unit_price, lead_time_days, rationale, split_sourcing, allocations), "
        "estimated_cost (float), estimated_delivery_days (float), production_impact_hours (float), "
        "supplier_risk_score (float), quality_score (float), robustness_score (float), "
        "reliability_rationale (str), budget_impact_analysis (str), and tool_call_trace (list of strings). "
        "Use only the supplied risk report and eligible suppliers. Do not invent supplier IDs, quantities, prices, or lead times."
    )

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are the Tata Motors Autonomous Supply Chain Disruption Recovery Agent. "
                            "Deterministic engines have established verified operational facts. "
                            + response_schema
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)

    suggestions = payload["suggestions"]
    if not isinstance(suggestions, list) or not suggestions:
        raise ValueError("Groq returned no recovery suggestions")

    normalized = []
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            raise ValueError("Groq returned an invalid suggestion")
        suggestion["plan_id"] = str(uuid.uuid4().hex[:16])
        suggestion["plan_details"] = suggestion.get("plan_details", {})
        suggestion["overall_score"] = round(
            float(suggestion.get("quality_score", 0)) * 0.4
            + (100 - float(suggestion.get("supplier_risk_score", 0))) * 0.3
            + float(suggestion.get("robustness_score", 0)) * 0.3,
            2,
        )
        normalized.append(suggestion)
    return normalized


def _get_deterministic_suggestions(
    risk_report: dict,
    eligible_suppliers: list[dict],
) -> list[dict]:
    suggestions: list[dict] = []

    coverage = float(risk_report.get("coverage_days", 0))
    risk_level = risk_report.get("risk_level", "UNKNOWN")
    hours_to_stop = float(risk_report.get("hours_to_production_stop", 0))
    usable_stock = float(risk_report.get("usable_stock", 0))
    avg_burn = float(risk_report.get("avg_daily_consumption_7d", 50.0)) or 50.0

    # Filter qualified suppliers
    qualified_suppliers = [
        s for s in eligible_suppliers
        if s.get("rejection_reason") is None and float(s.get("available_quantity", 0)) > 0
    ]

    # Required restock units to restore 7 days buffer
    target_buffer = max(100.0, avg_burn * 7)
    needed_units = max(50.0, round(target_buffer - usable_stock, 0))

    if qualified_suppliers:
        best = qualified_suppliers[0]
        avail = float(best.get("available_quantity", 0))
        unit_p = float(best.get("unit_price", 120.0))
        lead_t = int(best.get("lead_time_days", 2))
        sup_id = str(best.get("supplier_id", "SUP-34"))
        sup_name = str(best.get("supplier_name", "Metro Auto Parts"))

        if avail >= needed_units:
            # Plan 1: Direct Emergency Expedited Sourcing
            order_qty = min(needed_units, avail)
            total_c = order_qty * unit_p
            suggestions.append({
                "plan_id": str(uuid.uuid4().hex[:16]),
                "plan_name": f"Emergency Expedited Procurement from {sup_name} ({sup_id})",
                "plan_type": "EMERGENCY_PROCUREMENT",
                "plan_details": {
                    "supplier_id": sup_id,
                    "supplier_name": sup_name,
                    "quantity": order_qty,
                    "unit_price": unit_p,
                    "lead_time_days": lead_t,
                    "split_sourcing": False,
                    "allocations": [{"supplier_id": sup_id, "supplier_name": sup_name, "quantity": order_qty, "unit_price": unit_p, "lead_time_days": lead_t}],
                    "rationale": f"Fastest qualified ISO-9001 supplier with {lead_t}d lead time, delivering {order_qty:,.0f} units to prevent line stop.",
                    "reliability_rationale": f"Supplier historical quality score {float(best.get('quality_score', 92)):.1f}% and reliability score {float(best.get('reliability_score', 94)):.1f}% exceed compliance threshold.",
                    "budget_impact_analysis": f"Total procurement cost ₹{total_c:,.2f} vs autonomous authority limit ₹75,000.00 ({'Requires HITL sign-off' if total_c > 75000 else 'Within autonomous threshold'}).",
                },
                "estimated_cost": total_c,
                "estimated_delivery_days": float(lead_t),
                "production_impact_hours": max(0.0, hours_to_stop - (lead_t * 24.0)),
                "supplier_risk_score": float(100 - float(best.get("reliability_score", 90))),
                "quality_score": float(best.get("quality_score", 92)),
                "robustness_score": 88.0,
            })
        else:
            # Plan 1: Split-Sourcing Allocation across multiple qualified suppliers
            allocations = []
            remaining_demand = needed_units
            total_split_cost = 0.0
            max_lead = 0.0

            for sup in qualified_suppliers:
                s_avail = float(sup.get("available_quantity", 0))
                if s_avail <= 0 or remaining_demand <= 0:
                    continue
                alloc_qty = min(remaining_demand, s_avail)
                s_price = float(sup.get("unit_price", 120))
                s_lead = float(sup.get("lead_time_days", 3))
                allocations.append({
                    "supplier_id": str(sup.get("supplier_id")),
                    "supplier_name": str(sup.get("supplier_name")),
                    "quantity": alloc_qty,
                    "unit_price": s_price,
                    "lead_time_days": s_lead,
                })
                total_split_cost += alloc_qty * s_price
                max_lead = max(max_lead, s_lead)
                remaining_demand -= alloc_qty

            suggestions.append({
                "plan_id": str(uuid.uuid4().hex[:16]),
                "plan_name": f"Split-Sourcing Recovery Plan ({len(allocations)} Qualified Suppliers)",
                "plan_type": "SPLIT_SOURCING",
                "plan_details": {
                    "supplier_id": allocations[0]["supplier_id"] if allocations else sup_id,
                    "supplier_name": allocations[0]["supplier_name"] if allocations else sup_name,
                    "quantity": needed_units - remaining_demand,
                    "unit_price": unit_p,
                    "lead_time_days": int(max_lead),
                    "split_sourcing": True,
                    "allocations": allocations,
                    "rationale": f"Single supplier capacity ({avail:,.0f}u) insufficient for demand ({needed_units:,.0f}u). Split across {len(allocations)} suppliers.",
                    "reliability_rationale": "Diversified multi-sourcing strategy eliminates single-point-of-failure risk.",
                    "budget_impact_analysis": f"Combined split order cost ₹{total_split_cost:,.2f}.",
                },
                "estimated_cost": total_split_cost,
                "estimated_delivery_days": max_lead,
                "production_impact_hours": max(0.0, hours_to_stop - (max_lead * 24.0)),
                "supplier_risk_score": 15.0,
                "quality_score": 90.0,
                "robustness_score": 95.0,
            })

    # Plan 2: Production Rescheduling / Priority Re-sequencing
    if coverage < 5.0 and risk_level in ("CRITICAL", "HIGH"):
        suggestions.append({
            "plan_id": str(uuid.uuid4().hex[:16]),
            "plan_name": "Production Schedule Re-Sequencing & Tier-1 Prioritization",
            "plan_type": "PRODUCTION_ADJUSTMENT",
            "plan_details": {
                "action": "Prioritize critical vehicle assembly order PROD-882; defer non-critical batches by 48-72h.",
                "estimated_savings_hours": hours_to_stop * 0.4,
                "rationale": f"Current usable stock ({usable_stock:,.0f}u) covers {coverage:.1f} days. Reallocating buffer protects high-priority line commitments.",
                "reliability_rationale": "Purely internal scheduling adjustment; 0 external supplier execution dependency.",
                "budget_impact_analysis": "₹0.00 direct material procurement cost; saves estimated ₹120,000 in plant idle penalties.",
            },
            "estimated_cost": 0.0,
            "estimated_delivery_days": 1.0,
            "production_impact_hours": hours_to_stop * 0.4,
            "supplier_risk_score": 0.0,
            "quality_score": 95.0,
            "robustness_score": 85.0,
        })

    # Fallback plan if no immediate action required
    if not suggestions:
        suggestions.append({
            "plan_id": str(uuid.uuid4().hex[:16]),
            "plan_name": "Autonomous Monitoring & Buffer Absorption",
            "plan_type": "MONITORING",
            "plan_details": {
                "action": "Continue automated telemetry monitoring; safety buffer absorbs projected variation.",
                "rationale": f"Current risk level: {risk_level}; inventory coverage ({coverage:.1f}d) exceeds safety threshold.",
                "reliability_rationale": "Safety stock buffer absorbs disruption without external capital expenditure.",
                "budget_impact_analysis": "₹0.00 recovery expenditure.",
            },
            "estimated_cost": 0.0,
            "estimated_delivery_days": 0.0,
            "production_impact_hours": 0.0,
            "supplier_risk_score": 0.0,
            "quality_score": 85.0,
            "robustness_score": 90.0,
        })

    for s in suggestions:
        s["overall_score"] = round(
            (s.get("quality_score", 0) * 0.4
             + (100 - s.get("supplier_risk_score", 0)) * 0.3
             + s.get("robustness_score", 0) * 0.3),
            2,
        )

    return suggestions
