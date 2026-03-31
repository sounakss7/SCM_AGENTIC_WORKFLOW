# 🌐 Agentic Supply Chain Workflow

[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

An advanced, autonomous multi-agent supply chain management system built for the ET Gen AI Hackathon. This platform leverages a state-of-the-art AI architecture to orchestrate supply chain operations, detect disruptions in real-time, and execute autonomous recovery strategies.

🚀 **Live Demo:** [https://scm-agentic-workflow.vercel.app/](https://scm-workflow-live.vercel.app/)  
🛠️ **AI Studio App:** [View in AI Studio](https://ai.studio/apps/46a41076-c9cb-4228-a29f-f532c51c784b)

## 📌 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Core Components](#-core-components)
- [Tech Stack](#-tech-stack)
- [Business Impact](#-business-impact)
- [Local Development Setup](#-local-development-setup)
- [Contributors](#-contributors)

---

## ✨ Features

- **Multi-Agent Orchestration:** Utilizes a StateGraph architecture to coordinate multiple specialized AI agents.
- **Dynamic Disruption Mitigation:** Employs Qdrant vector databases for historical memory to identify and resolve external disruptions (e.g., weather, port congestion) autonomously.
- **Multi-LLM Routing:** Intelligently routes decision-making tasks across leading models (Gemini, Groq, MistralAI) for optimized cost and performance.
- **Real-Time Diagnostic Analytics:** Live frontend visualization of agent health, decision confidence, and workflow metrics.
- **Automated Reporting:** Instantly generate detailed PDF executive summaries of supply chain execution and AI interventions.

---

## 🏗️ Architecture

The system operates across three core lifecycle phases: **Planning**, **Execution**, and **Monitoring & Optimization**. 

<p align="center">
  <img src="SCM_Architecture_Workflow.png" alt="Agentic Supply Chain Architecture Workflow" width="800">
</p>

---

## 🧠 Core Components & Agent Roles

### 1. 👤 User Interface (Customer Layer)
* Handles the initial order intake.
* Provides a real-time **Workflow Health Monitor** for immediate feedback.
* Displays final order fulfillment and reporting data.

### 2. 🌐 Supply Chain Intelligence Agent
* **Order Assessment:** Conducts initial demand analysis and disruption screening.
* **Continuous Monitoring:** Tracks real-time performance data and route efficiency.
* **Disruption Detection:** Identifies external threats and triggers **Autonomous Optimization**.

### 3. ⚙️ Process Orchestration Agent
* **Logistics Planning:** Manages inventory, routes, and carrier selection.
* **Autonomous Execution:** Oversees active fulfillment.
* **Self-Correction Protocols:** The core of system resilience. If an external error occurs (e.g., carrier failure), it autonomously triggers alternative supplier selection or rerouting.

### 4. 🛡️ Verification & Compliance Agent
* Runs parallel to the planning phase to ensure sourcing and routing meet regulatory frameworks.
* Locks in an immutable **Decision Audit Trail** prior to execution.

---

## 💻 Tech Stack

### Frontend
- **Framework:** React 19 / Vite
- **Styling:** TailwindCSS 4.0
- **Utilities:** Lucide React (Icons), jsPDF (Auto-Report Generation)

### Backend
- **Framework:** FastAPI / Python
- **AI/Agents:** LangGraph, LangChain (Google GenAI, Groq, MistralAI)
- **Vector Database:** Qdrant Client

---

## 📊 Business Impact Model

To quantify the value of this workflow, we modeled the impact on a mid-to-large enterprise processing **10,000 orders per month**. 

| Metric | Manual Processing | Agentic Automation | Improvement |
|--------|-------------------|--------------------|-------------|
| **Avg. Time per Order** | 45 minutes | 2 minutes | **95% Reduction** |
| **Labor Cost/Month** | $225,000 | Minimal Oversight | **~ $214,980 Saved** |
| **SLA Breach Rate** | 2% (200 orders) | < 0.1% | **$95,000 Recovered** |

**Total Estimated Value:** Combined operational savings and penalty prevention of **$309,980 per month** (over **$3.7 Million annually**).

---

## 🛠️ Local Development Setup

Follow these steps to run the application locally.

### Prerequisites
- Node.js (v18+)
- Python (3.10+)

### 1. Clone the Repository
```bash
git clone https://github.com/sounakss7/SCM_AGENTIC_WORKFLOW.git
cd SCM_AGENTIC_WORKFLOW
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```
*Create a `.env` file in the `backend` directory based on `.env.example` to include your API keys (Gemini, Groq, etc).*

Run the backend server:
```bash
# Depending on your backend entry point:
uvicorn main:app --reload
```

### 3. Frontend Setup
Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```

The application will now be running on `http://localhost:5173`.

---

## 👨‍💻 Contributors

* **Sounak Sarkar** - *Lead Developer & AI Architect* - [@sounakss7](https://github.com/sounakss7)

---

*Built with ❤️ for the ET Gen AI Hackathon*
