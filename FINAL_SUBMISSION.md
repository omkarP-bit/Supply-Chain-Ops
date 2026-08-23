# Autonomous Supply Chain Disruption Control Platform
**Tata Motors Autonomous Operations | Final Hackathon Submission Document**

---

## 1. Team Details

- **Team Name**: Syntra Ops (`omkarP-bit / Team Syntra`)
- **Track**: Autonomous Supply Chain Disruption Control Agent

---

## 2. Problem Statement in Short

Automotive manufacturing operates on Just-In-Time (JIT) scheduling where a minor component delay (e.g., fasteners, housings, transmission brackets) triggers immediate vehicle assembly line halts costing up to ₹350,000/hour in idle penalties. Current Enterprise Resource Planning (ERP) systems are static: they lack autonomous reasoning to detect discrepancies, cannot autonomously negotiate or evaluate alternate multi-vendor allocations, fail to cross-verify contradictory carrier tracking telemetry, and cannot dynamically reschedule production schedules during emergency stockouts.

---

## 3. Understanding of the Problem Statement

Our team identified three fundamental challenges in autonomous supply chain resilience:

1. **The Ground Truth Dilemma**: Pure LLMs hallucinate inventory quantities, prices, and ISO certifications. Ground truth (stock levels, burn rates, lead times, budget thresholds) must be computed by **deterministic mathematical engines** and validated against PostgreSQL ACID transactions.
2. **Adversarial & Stale Telemetry**: Suppliers often claim shipments are "dispatched" when carrier tracking APIs report only `LABEL_CREATED / NO_PICKUP`, or ERP databases report inflated stock while physical warehouse bins are depleted. The system must autonomously detect discrepancies and trigger closed-loop replanning.
3. **Operational Authority & Safety**: AI agents must not autonomously commit high-value expenditures without oversight. High-risk financial commitments (> ₹75,000 threshold) require an immutable **Human-in-the-Loop (HITL)** decision gate.

**Core Design Principle**: 
> *LLMs recommend and reason. Deterministic services establish operational truth. Humans authorize. Deterministic tools execute.*

---

## 4. Idea Summary

We engineered an **Autonomous Supply Chain Disruption Control Platform** for automotive manufacturing. When a supply delay, inventory mismatch, or spike occurs:
- The system deterministically computes inventory burn rates, stockout countdowns, and affected production orders.
- It queries regional suppliers, applies strict deterministic filters (ISO-9001/IATF-16949 certification, AQL tolerance), and scores qualified options.
- The **LangGraph Multi-Agent Engine** formulates optimized recovery strategies (direct restock, multi-supplier split sourcing, or production order re-sequencing).
- It produces an interactive Human Decision Brief, executes authorized purchase orders to the simulated ERP upon sign-off, audits carrier tracking telemetry, and triggers closed-loop replanning if discrepancies emerge.

---

## 5. Proposed Solution & System Architecture

### 5.1 Multi-Agent & Deterministic Architecture

```text
[ Disruption Injection / Telemetry Sensor ]
                     ↓
       [ PostgreSQL ACID Database ]
                     ↓
       [ FastAPI Operational Layer ]
                     ↓
[ LangGraph Orchestration: Supervisor Agent ]
   ├── Operational Risk Engine (Python/SQL: Burn rate, stockout countdown, discrepancy %)
   ├── Supplier Evaluation Engine (Deterministic hard filter: ISO/AQL + Multi-criteria scoring)
   ├── Recovery & Recommendation Agent (Groq / Llama-3.1-8b reasoning & strategy formulation)
   ├── Plan Validation & Simulation Engine (What-if Monte Carlo feasibility & ₹75k budget gate)
   └── Verification & Replanning Agent (Closed-loop post-execution tracking verification)
                     ↓
[ Human-in-the-Loop Sign-Off Gate (Operations Manager) ]
                     ↓
[ Deterministic Tool Execution & ERP Commit ] → [ Immutable Audit Trail ]
```

### 5.2 Deterministic vs. LLM Responsibilities

| Subsystem | Technology | Responsibility |
| :--- | :--- | :--- |
| **Ground Truth & Risk** | Deterministic Engine (SQL/Python) | Calculates days of coverage, 7d/30d burn rate trends, line stop countdown ($T_{\text{stop}}$). |
| **Supplier Hard Filter** | Deterministic Engine | Rejects uncertified suppliers (ISO/AQL expired); computes multi-criteria score $S = 0.4Q + 0.3(100-R) + 0.3L$. |
| **Strategy Reasoning** | LLM Agent (Llama-3.1-8b via Groq) | Explains operational rationale, compares trade-offs, formulates split-sourcing allocations. |
| **Validation & Budget** | Deterministic Engine | Enforces hard constraints; checks autonomous authority threshold (₹75,000 limit). |
| **Verification & Replan**| Closed-Loop Agent | Cross-references carrier tracking API against supplier claims; triggers adaptive replanning. |

---

## 6. MVP Description & Verified Capabilities

The MVP is fully built, containerized in Docker, and tested against all 6 official benchmark scenarios.

### 6.1 Official Scenario Evaluation Matrix (100% Verified)

| Scenario | Disruption Event | Autonomous Agent Behavior | Verification Evidence | Result |
| :--- | :--- | :--- | :--- | :---: |
| **1. Normal Disruption** | `PO-7712` +5d delay on `COMP-104` | Detects buffer deficit ($<7\text{d}$), broadcasts RFQs, selects certified `SUP-34`, executes recovery PO. | `test_scenario_1_normal_disruption` | **PASS** |
| **2. Stale Inventory** | ERP = 800u vs Usable = 390u (51.2% gap) | Flags discrepancy $>20\%$, recalculates coverage to true usable stock, upgrades severity to `CRITICAL`. | `test_scenario_2_stale_inventory` | **PASS** |
| **3. Adversarial Claim** | Supplier claims dispatched; Tracking: No pickup | Detects contradiction via Carrier Tracking API, logs memory penalty, initiates adaptive replanning. | `test_scenario_3_adversarial_supplier_claim` | **PASS** |
| **4. Quality Constraint** | Lowest bidder fails ISO/AQL standards | Deterministic hard filter rejects cheapest non-compliant vendor; selects qualified alternate `SUP-34`. | `test_scenario_4_quality_constraint` | **PASS** |
| **5. Budget Approval** | Recovery plan ₹96,000 > ₹75,000 limit | Gates execution; generates Human Decision Brief; dispatches to ERP only after Operations Manager approval. | `test_scenario_5_budget_approval_required` | **PASS** |
| **6. Production Risk** | Plant stop in 9.6h; single supplier insufficient | Re-sequences assembly queue to priority order `PROD-882`; executes split sourcing (500u + 300u). | `test_scenario_6_high_pressure_production_risk` | **PASS** |

### 6.2 The 10 Strong MVP Capabilities Suite

1. **🧠 Supplier Reliability Memory**: Continuous tracking of on-time delivery rate (96.5%), quality score (94.0%), and claim mismatch history.
2. **🔄 Multi-Step Adaptive Replanning**: Closed-loop verification agent audits ERP state post-execution; triggers secondary replanning on discrepancies.
3. **🏭 Production Rescheduling**: Dynamically re-allocates remaining stock to Tier-1 order `PROD-882`, deferring non-critical runs by 48h.
4. **📦 Partial Shipment & Split-Sourcing**: Partitions demand across multiple qualified vendors (`SUP-34` + `SUP-41`) to satisfy urgent buffer requirements.
5. **💰 Budget-Aware Optimization**: Automatically gates expenditures exceeding ₹75,000.00 for management sign-off.
6. **🛡️ Adversarial Telemetry Cross-Verification**: Carrier API tracking verification cross-checks waybills against supplier claims.
7. **👤 Human-in-the-Loop Sign-Off**: Interactive approval dialog capturing manager authorization before purchase order release.
8. **📊 Visual Control Tower**: Industrial dark-mode UI with live KPI gauges (coverage, stockout countdown, risk severity).
9. **⏪ Simulation Replay & What-If Branching**: Evaluates **Branch A (Do Nothing &rarr; Plant Halt)** vs **Branch B (Autonomous Mitigation &rarr; Zero Downtime)**.
10. **🛠️ Agent Tool-Call Trace Viewer**: Live audit of LangGraph tool invocations (`calculate_risk`, `filter_suppliers`, `simulate_plan`) with millisecond latencies.

---

## 7. Technology Stack

- **Frontend**: React 18, Vite 5, Tailwind-free Vanilla CSS (Minimal Industrial Command-Center Aesthetic).
- **Backend API**: FastAPI (Python 3.13), Uvicorn, Pydantic v2, SQLAlchemy 2.0 Async, AsyncPG.
- **AI & Orchestration**: LangGraph, LangChain Core, Groq API (`llama-3.1-8b-instant`), LangSmith Tracing.
- **Database**: PostgreSQL 16 (Dockerized ACID relational store).
- **Testing & Tooling**: PyTest (20/20 Passing Integration & Scenario Tests), Docker Compose.

---

## 8. Impact, Feasibility, and Risk Handling

### 8.1 Operational Impact
- **Zero Line Downtime**: Prevents sudden vehicle line stoppages by detecting buffer stockout risks $<250\text{ms}$ after event injection.
- **100% Audit Compliance**: Every autonomous calculation, LLM recommendation, and manager decision is immutably logged.
- **Cost Reduction**: Replaces panic spot-market purchasing with optimized multi-criteria sourcing and priority re-sequencing.

### 8.2 Feasibility & Engineering Risk Mitigations

| Identified Risk | System Mitigation |
| :--- | :--- |
| **LLM Hallucination of Stock / Prices** | LLMs are restricted to reasoning and explanation; all pricing, inventory balances, and threshold checks are executed by deterministic SQL/Python engines. |
| **Simultaneous Disruption Race Conditions** | PostgreSQL row-level locks (`SELECT FOR UPDATE`) and optimistic concurrency versioning prevent double-allocation of stock. |
| **Unauthorized Capital Expenditure** | Strict hard-coded financial threshold gate (₹75,000) blocks ERP dispatch until authenticated human authorization is received. |

---

## 9. Safety & Simulation Boundary Declaration

In compliance with hackathon regulations, the platform operates in a **fully closed simulated environment**. All purchase order dispatches, carrier telemetry feeds, supplier communications, and ERP updates mutate local PostgreSQL database state. No real-world financial transactions, real ERP systems, or live supplier emails are executed.
