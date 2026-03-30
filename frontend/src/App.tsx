import React, { useState } from 'react';
import { Activity, ShieldCheck, Truck, AlertTriangle, ShoppingCart } from 'lucide-react';

// Define the shape of our audit log based on the backend
interface AuditEntry {
  agent: string;
  action: string;
}

function App() {
  const [workflowStatus, setWorkflowStatus] = useState('Standby');
  const [activeErrors, setActiveErrors] = useState(0);
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [isSimulatingDisruption, setIsSimulatingDisruption] = useState(false);

  // The function to trigger the LangGraph backend
  const triggerOrder = async () => {
    setWorkflowStatus('Operational');
    setLogs([{ agent: "System", action: "Initializing workflow..." }]);
    setActiveErrors(isSimulatingDisruption ? 1 : 0);

    try {
      // Use the codespace URL or localhost
      const response = await fetch('https://glorious-xylophone-699556vv7r69crw9q-8000.app.github.dev/api/place_order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          order_id: `ORD-${Math.floor(Math.random() * 10000)}`,
          simulate_disruption: isSimulatingDisruption
        })
      });

      const data = await response.json();
      
      // Update the dashboard with the LangGraph audit trail
      if (data.state && data.state.audit_trail) {
        setLogs(data.state.audit_trail);
        setWorkflowStatus(data.state.status || 'Completed');
        if (data.state.status === "Order Fulfilled") {
            setActiveErrors(0); // Clear errors on success
        }
      }
    } catch (error) {
      console.error("Failed to connect to backend:", error);
      setLogs(prev => [...prev, { agent: "Error", action: "Failed to connect to FastAPI backend." }]);
      setWorkflowStatus('Error');
    }
  };

  // Helper to color-code agents in the log
  const getAgentColor = (agent: string) => {
    switch(agent) {
      case 'UI': return 'text-blue-400';
      case 'Intelligence': return 'text-purple-400';
      case 'Orchestration': return 'text-emerald-400';
      case 'Compliance': return 'text-amber-400';
      case 'Error': return 'text-red-400';
      default: return 'text-slate-300';
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <header className="mb-8 border-b border-slate-700 pb-4">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Truck className="text-blue-400" />
          Autonomous Enterprise SCM Dashboard
        </h1>
      </header>

      {/* Workflow Health Monitor */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Activity /> System Health</h2>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span>Status:</span>
              <span className={`font-mono ${workflowStatus === 'Completed' || workflowStatus === 'Order Fulfilled' ? 'text-green-400' : workflowStatus === 'Error' ? 'text-red-400' : 'text-yellow-400'}`}>
                {workflowStatus}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Active Disruptions:</span>
              <span className="font-mono text-red-400">{activeErrors}</span>
            </div>
          </div>
        </div>

        {/* Dynamic Execution Log */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg md:col-span-2">
          <h2 className="text-xl font-bold mb-4">Execution Log</h2>
          <div className="h-48 overflow-y-auto bg-slate-950 p-4 rounded font-mono text-sm space-y-2 flex flex-col gap-1">
            {logs.length === 0 && <p className="text-slate-500">Waiting for system activity...</p>}
            {logs.map((log, index) => (
              <div key={index} className="flex gap-3 border-b border-slate-800 pb-1">
                <span className={`font-bold min-w-[120px] ${getAgentColor(log.agent)}`}>
                  [{log.agent}]
                </span>
                <span className="text-slate-300">{log.action}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Disruption Simulation Controls */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg md:col-span-3">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><AlertTriangle /> Simulation Controls</h2>
          <div className="flex gap-4 items-center">
            <button 
              onClick={triggerOrder}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded flex items-center gap-2 transition-colors font-semibold">
              <ShoppingCart size={18} /> Run Workflow
            </button>
            
            <label className="flex items-center gap-2 cursor-pointer ml-4">
              <input 
                type="checkbox" 
                className="w-5 h-5 accent-red-500"
                checked={isSimulatingDisruption}
                onChange={(e) => setIsSimulatingDisruption(e.target.checked)}
              />
              <span className={`${isSimulatingDisruption ? 'text-red-400 font-bold' : 'text-slate-400'}`}>
                Simulate Severe Weather Disruption
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;