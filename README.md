# Agentic Supply Chain Workflow

This repository contains the prototype for an autonomous multi-agent supply chain system, built for the ET Gen AI Hackathon.

🚀 **Live Demo:** [https://scm-agentic-workflow.vercel.app/](https://scm-agentic-workflow.vercel.app/)  
🛠️ **AI Studio App:** [View in AI Studio](https://ai.studio/apps/46a41076-c9cb-4228-a29f-f532c51c784b)

---

## 🏗️ Architecture

Below is the high-level workflow of our multi-agent supply chain system, demonstrating autonomous planning, execution, and error recovery:

<p align="center">
  <img src="SCM_Architecture_Workflow.png" alt="Agentic Supply Chain Architecture Workflow" width="800">
</p>

---
### 🧠 Core Components & Agent Roles

Our architecture utilizes a multi-agent StateGraph orchestration model divided across three distinct lifecycle phases: **Planning**, **Execution**, and **Monitoring & Optimization**.

* **👤 User Interface (Customer Layer)**
  * Handles the initial order intake.
  * Features a real-time **Workflow Health Monitor** that provides a continuous feedback loop.
  * Displays final order fulfillment and reporting data.

* **🌐 Supply Chain Intelligence Agent**
  * **Order Assessment:** Conducts initial demand analysis and disruption screening.
  * **Continuous Monitoring:** Tracks real-time performance data and route efficiency.
  * **Disruption Detection:** Identifies external threats (e.g., weather delays, port congestion) and triggers **Autonomous Optimization** to dynamically adjust plans.

* **⚙️ Process Orchestration Agent**
  * **Logistics Planning:** Checks inventory status and selects optimal routes and carriers.
  * **Autonomous Execution:** Manages the active fulfillment process.
  * **Self-Correction Protocols:** The core of the system's resilience. If external errors occur (e.g., carrier failure), it autonomously triggers **Alternative Supplier Selection** or **Autonomous Rerouting** without human intervention.
  * **Order Completion:** Ensures non-time models and dynamic adjustments are finalized.

* **🛡️ Verification & Compliance Agent**
  * Runs parallel to the planning phase to ensure all sourcing and routing decisions meet regulatory frameworks.
  * Locks in an immutable **Decision Audit Trail** before execution begins, ensuring complete transparency.

* **📦 External Entities (Simulated)**
  * Represents external endpoints for Supplier P.O. Creation, Carrier Booking, and Warehouse Picking. These nodes feed real-time success/failure signals back into the Orchestration Agent's error-handling loops.
---

## 📊 Business Impact Model

To quantify the value of this Agentic SCM Workflow, we modeled the impact on a mid-to-large enterprise processing **10,000 orders per month**. 

### Baseline Assumptions
* **Manual Processing Time:** Average 45 minutes per order (sourcing, compliance checks, carrier booking, error handling).
* **Labor Cost:** $30/hour for a Supply Chain Operations Specialist.
* **SLA Breach Rate:** 2% of orders (200/month) breach Service Level Agreements due to manual bottlenecks or unmitigated disruptions. Average penalty: $500 per breach.

### Quantified Impact
* **Time Saved:** 43 minutes per order (~7,166 hours saved/month).
* **Cost Reduced:** $214,980 cost reduction per month.
* **Revenue Recovered:** $95,000 recovered per month (by preventing SLA penalties via self-correction).
* **Total Estimated Value:** Combined operational savings and penalty prevention of **$309,980 per month** (over **$3.7 Million annually**).

---

## 💻 Run Locally

**Prerequisites:** [Node.js](https://nodejs.org/)

1. **Install dependencies:**
   ```bash
   npm install
2. **Configure Environment:**
   Create a .env.local file in the root directory of your project and set your Gemini API key:
    ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
4. **Run the application:**
    ```bash
    npm run dev
   
---

## 👨‍💻 Contributors

* **Sounak Sarkar** - *Lead Developer & AI Architect* - [@sounakss7](https://github.com/sounakss7)
