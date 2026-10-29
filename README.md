# Autonomous Supply Chain Resilience Agent & Control Tower
*Production 5-Agent LangGraph System with Deterministic OR Solver, Dynamic Carrier Self-Correction Loop, SQL Database Audit Trail (MySQL / SQLite), and Zero-Trust Prompt & SQL Injection Defense*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Tests: 25 Passed](https://img.shields.io/badge/pytest-25%20passed-brightgreen.svg)]()
[![Security: Zero--Trust Guardrails](https://img.shields.io/badge/Security-Input%20%26%20Output%20Guards-success.svg)]()

---

## 1. Project Overview

This repository houses an enterprise-grade autonomous supply chain disruption response engine and control tower. Built on a stateful **5-Agent LangGraph workflow**, the platform automates end-to-end incident management: detecting logistical shocks, quantifying financial exposure, computing cost-optimal alternate paths, validating physical network constraints, and generating audited executive briefings in plain language.

### Core Capabilities
1. **5-Agent LangGraph Workflow**: Decoupled, stateful orchestration across specialized agents (Disruption Detection, Risk Assessment, Deterministic Re-Routing, Constraint Validation, and Executive Briefing).
2. **Autonomous Self-Correction Loop**: If a carrier rejects a booking or a transshipment hub experiences severe port congestion (e.g., Los Angeles $\to$ Seattle, or JNPT $\to$ Mundra), the system dynamically loops back to the Routing Agent, applies blocked-node constraints, and re-optimizes alternate paths without human intervention.
3. **Enterprise SQL Database Audit Trail**: Saves every routing decision, alternate candidate cycle, and intermediate agent execution step to a relational SQL database (**MySQL** with automatic **SQLite** zero-config fallback) with parameterized queries.
4. **Zero-Trust Security Guards**: Comprehensive pre-execution and post-generation guards blocking Prompt Injection (jailbreaks, rule-overrides), stacked SQL Injection (`DROP TABLE`, `UNION SELECT`, `' OR 1=1`), and XSS, with automatic security quarantine and incident audit logging.
5. **Deterministic OR Decision Core ("The LLM Must NOT Do the Math")**: Math, distance-rate calculation, transit-time matrix solving, and capacity bounding are executed strictly by a deterministic Operations Research solver to eliminate LLM arithmetic hallucinations.

---

## 2. Multi-Agent System Architecture

```mermaid
flowchart TD
    subgraph Security_Gate["0. Zero-Trust Security Perimeter"]
        IN["Inbound Telemetry / Order"] --> G_IN{"InputGuard\n(Prompt & SQL Injection Detection)"}
        G_IN -- "Malicious Payload" --> QUARANTINE["Security Quarantine\n(SQL security_audit table)"]
        G_IN -- "Clean / Verified" --> N1["1. Monitor Agent\n(Disruption Intersection Check)"]
    end

    subgraph LangGraph_Core["5-Agent LangGraph Resilience Workflow"]
        N1 -- "No Disruption" --> PASS["Pass Through\n(Nominal Schedule)"]
        N1 -- "Disruption Detected" --> N2["2. Risk Assessor Agent\n(Google Gemini: Financial & SLA Exposure)"]
        
        N2 --> N3["3. Routing Agent\n(Deterministic OR Graph Solver)"]
        N3 --> N4["4. Validator Agent\n(Groq LPU / Rule Engine: Physical Feasibility)"]
        
        N4 -- "Carrier Rejection / Port Congestion\n(e.g., LA Port Congested -> Reroute Seattle)" --> N3
        N4 -- "Validation Approved" --> N5["5. Explainer Agent\n(Google Gemini: Executive Briefing)"]
    end

    subgraph Persistence_Audit["SQL Audit Trail (MySQL / SQLite Fallback)"]
        N3 -.-> DB1[("routing_decisions\n(Cycles, Path, Landed Cost, Transit Time)")]
        N4 -.-> DB1
        N1 -.-> DB2[("order_history\n(Agent Name, Action, Status, Cost Savings)")]
        N2 -.-> DB2
        N5 -.-> DB2
    end

    subgraph Executive_Delivery["Interface & Sanitization"]
        N5 --> G_OUT{"OutputGuard\n(Leak / Error Sanitizer)"}
        G_OUT --> UI["FastAPI Swagger / Streamlit Control Tower"]
    end
```

---

## 3. The 5 Agents in Detail

| Agent | Core Responsibility | Engine / Model | Latency |
|---|---|---|---|
| **1. Monitor Agent** | Inspects real-time carrier telemetry, port congestion feeds, and strikes against active route legs. | Deterministic Python Engine | <1 ms |
| **2. Risk Assessor Agent** | Estimates stockout risks, SLA penalty liability, and daily financial exposure in INR (₹) / USD ($). | Google Gemini 2.5 Flash | ~40 ms |
| **3. Routing Agent** | Exhaustively searches feasible multimodal networks to minimize Total Landed Cost (Freight + Handling + Delays). | Deterministic OR Solver Core | <5 ms |
| **4. Validator Agent** | Validates warehouse pallet limits, carrier daily quotas, and simulates carrier booking confirmation. | Groq LPU (Llama 3.3) / Rules | ~13 ms |
| **5. Explainer Agent** | Translates technical solver telemetry into a clear, executive-ready operational briefing preserving exact numbers. | Google Gemini 2.5 Flash | ~40 ms |

---

## 4. Carrier Rejection & Port Congestion Self-Correction Loop

Traditional linear supply chain workflows crash or require human intervention when a carrier declines freight or a port halts operations due to congestion. 

Our LangGraph workflow introduces a **closed-loop feedback cycle**:
1. **Trigger Condition**: When the `Validator Agent` or simulated carrier rejects a booking (e.g. *Port of Los Angeles congestion exceeds threshold*, *Port strike*, or *Carrier daily capacity exhausted*):
   - The validation status is marked as `is_valid: False`.
   - The specific failure reason is attached to the state (e.g., `Port 'PORT_LA' congested (dwell > 14 days); carrier booking rejected`).
2. **Conditional Feedback Edge**: LangGraph routes `validator -> routing_agent` instead of proceeding to `explainer`.
3. **Adaptive Solver Replanning**:
   - The `Routing Agent` reads `validation_result` and penalizes/blocks the failing carrier or port.
   - For example, if **Port of Los Angeles** is congested, the deterministic solver dynamically diverts maritime flow through **Port of Seattle** or **Oakland Port Terminal**.
   - If an Indian transporter such as **Safexpress** strikes, the solver shifts allocation to **Delhivery Surface** or **TCI Express**.
4. **Convergence Guarantee**: A state-bounded `retry_count` (default: 3 cycles) guarantees convergence and prevents infinite cycling.

---

## 5. SQL Audit Trail (MySQL with SQLite Fallback)

To meet regulatory and supply chain governance standards, every agent decision and routing cycle is saved to a persistent SQL database.

### Dual-Engine Database Architecture
- **Primary**: MySQL (`mysql+pymysql://root:...@localhost:3306/scm_orders`) for production multi-tenant environments.
- **Fallback**: SQLite (`local_orders.db`) with zero external service dependencies for local development, CI/CD, and offline demonstration.

### Key Database Tables

#### 1. `routing_decisions`
Stores every candidate plan evaluated across self-correction loops:
- `order_id`: Unique order identifier (e.g., `ORD-5001`).
- `cycle`: Optimization retry iteration ($0, 1, 2\dots$).
- `carrier`: Selected logistics provider (e.g., `Delhivery Surface`, `Safexpress`, `Pacific Maritime Express`).
- `port`: Maritime or dry-port transshipment hub (e.g., `PORT_MUNDRA`, `PORT_JNPT`, `Seattle Terminal`).
- `total_cost`: Mathematically computed Total Landed Cost ($TLC$).
- `transit_days`: Cumulative end-to-end delivery timeline.
- `status`: Decision state (`APPROVED`, `CARRIER_REJECTED`, `CONGESTION_REROUTE`).
- `rejection_reason`: Contextual violation log explaining why an earlier cycle was discarded.

#### 2. `order_history`
Granular event sourcing logging every agent execution step:
- `order_id`, `phase`, `agent_name`, `action`, `model_used`, `cost_savings`, `live_location`, `timestamp`.

#### 3. `security_audit`
Zero-trust incident database storing quarantined malicious injection attempts:
- `order_id`, `threat_type` (`PROMPT_INJECTION`, `SQL_INJECTION`, `XSS_ATTACK`), `payload`, `agent_name`, `action_taken` (`QUARANTINED`).

---

## 6. Zero-Trust Security Input & Output Guards

In mission-critical logistics software, agent inputs and outputs must be guarded against adversarial tampering:

### InputGuard (Pre-Execution Gate)
- **Prompt Injection Defense**: Detects and neutralizes jailbreaks, system instruction overrides (`ignore all previous instructions`, `bypass all guardrails`, `disregard previous rules`, `system prompt disclosure`).
- **SQL Injection Defense**: Regex-based syntactic token filtering blocking stacked queries (`DROP TABLE`, `DELETE FROM`, `UNION SELECT`, `' OR 1=1`, `--`, `/* */`).
- **XSS Vector Neutralization**: Blocks malicious HTML tags and script injection (`<script>`, `javascript:`, `onerror=`).
- **Action**: When a malicious payload is detected, the workflow immediately quarantines the order, writes an incident record to `security_audit`, and terminates without executing LLMs or solver logic.

### OutputGuard (Post-Generation Gate)
- Inspects LLM-synthesized executive briefs before presenting them to users or upstream APIs.
- Blocks and redacts internal error traces (`Traceback`, `Exception:`, `Internal Server Crash`), leaked system prompts, or echoed exploit tokens.

---

## 7. Logistics Network Topology

The platform supports both high-throughput Indian corridors and global maritime lanes:

### Indian Freight Corridor
```
[Sourcing Clusters]       [Container Seaports]          [Central Distribution]         [Retail Consumption]
   Pune (2,000 u)    --->   Nhava Sheva/JNPT (3,000 u) ---> Bhiwandi / Mumbai (1,500 u)  ---> Mumbai Metro (1,000 u)
   Surat (2,500 u)   --->   Mundra Port (3,500 u)      ---> Bilaspur / Delhi-NCR (1,800 u) ---> Delhi-NCR Supermarkets (1,200 u)
   Ahmedabad (1,800 u) ->   Chennai Port (2,200 u)     ---> Nelamangala / BLR (1,400 u)   ---> Bengaluru Hypermarkets (900 u)
                                                                                          ---> Chennai Retail Zone (850 u)
```
- **Carriers**: Safexpress (₹0.08/km), Delhivery (₹0.10/km), TCI Express (₹0.13/km), Blue Dart (₹0.18/km).
- **Catalog**: 25 Indian FMCG & Retail SKUs (Aashirvaad Atta, Tata Salt, Fortune Oil, Amul Butter, Surf Excel).

### Global Multi-Port Resilience
- **Origin**: Shenzhen / East Asia Manufacturing Hubs.
- **Congested Primary Port**: Port of Los Angeles (simulated strike / 14-day dwell spike).
- **Rerouted Alternate Port**: Port of Seattle / Oakland Port Terminal.

---

## 8. Verification & Test Suite

The codebase comes with a comprehensive test suite covering unit logic, integration endpoints, LangGraph nodes, security guards, and database persistence:

```bash
# 1. Run full Pytest test suite (25 tests)
pytest tests/ -v

# 2. Run end-to-end integration test runner
python test_runner.py
```

### Verified Test Breakdown
- `test_agents.py`: Individual node execution for Monitor, Risk Assessor, and Validator.
- `test_workflow.py`: End-to-end LangGraph passes (steady state + carrier strike self-correction).
- `test_audit_and_guards.py`: InputGuard (prompt/SQL injection), OutputGuard sanitization, `routing_decisions` persistence, and `security_audit` logging.
- `test_decision_core_handcrafted.py`: Deterministic OR solver math vs. hand-computed formulas.
- `test_api.py`: FastAPI endpoints (`/health`, `/network`, `/simulate`, `/disrupt`, `/catalog/disruptions`).
- `test_runner.py`: End-to-end simulation covering normal routing, disrupted self-correction loop, SQL database seeding, and security quarantine.

---

## 9. Quickstart Guide

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/sounakss7/SCM_AGENTIC_WORKFLOW.git
cd SCM_AGENTIC_WORKFLOW

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Keys
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Populate your API keys (optional: system has full offline deterministic fallback):
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Database Configuration (Defaults to SQLite if MySQL is absent)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=scm_orders
```

### 3. Launch FastAPI Server
```bash
uvicorn api.server:app --reload --port 8000
```
Interactive Swagger API docs available at: `http://localhost:8000/docs`

### 4. Launch Streamlit Control Tower
```bash
streamlit run streamlit_app.py
```
Control Tower UI opens at: `http://localhost:8501`

---

## 10. Repository Structure

```
SCM_AGENTIC_WORKFLOW/
├── agents/
│   ├── guards.py              # Zero-Trust InputGuard & OutputGuard (Prompt/SQL/XSS)
│   ├── monitor.py             # Agent 1: Disruption detection & telemetry intersection
│   ├── risk_assessor.py       # Agent 2: Operational risk & financial impact scoring
│   ├── routing_agent.py       # Agent 3: Deterministic OR solver & self-correcting replanner
│   ├── validator_agent.py     # Agent 4: Physical constraint validation & carrier booking check
│   ├── explainer_agent.py     # Agent 5: Executive plain-language briefing
│   ├── workflow.py            # LangGraph multi-agent workflow compilation & state graphs
│   └── state.py               # TypedDict state definitions
├── core/
│   ├── optimizer.py           # Deterministic OR solver (Dijkstra / Landed Cost Minimizer)
│   ├── network.py             # SCM topology (Suppliers, Ports, Warehouses, Retailers)
│   ├── disruptions.py         # Catalog of simulated shocks (strikes, weather, dwell)
│   └── skus.py                # SKU catalog with holding costs and late penalties
├── database/
│   └── db_manager.py          # SQL Database audit trail (MySQL with SQLite fallback)
├── tests/
│   ├── test_agents.py         # Agent node tests
│   ├── test_api.py            # FastAPI endpoint tests
│   ├── test_audit_and_guards.py # SQL audit trail & security guardrail tests
│   ├── test_decision_core_handcrafted.py # Deterministic math proofs
│   ├── test_disruptions.py    # Disruption event parsing tests
│   ├── test_forecaster.py     # Demand forecasting metrics tests
│   ├── test_optimizer_handcrafted.py # Solver optimization tests
│   └── test_workflow.py       # End-to-end LangGraph self-correction tests
├── api/
│   └── server.py              # FastAPI REST endpoints
├── streamlit_app.py           # Interactive Streamlit Control Tower UI
├── test_runner.py             # Comprehensive end-to-end integration test harness
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Project dependencies
└── README.md                  # Comprehensive technical documentation
```

---

## 11. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
