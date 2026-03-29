
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
   GEMINI_API_KEY=your_gemini_api_key_here
3. **Run the application:**
    ```bash
    npm run dev
   npm run dev
