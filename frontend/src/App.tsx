import { useState } from 'react';
import './App.css';

// ============= Type Definitions =============
interface AuditEntry {
  timestamp: string;
  agent: string;
  action: string;
}

interface WorkflowState {
  status: string;
  current_phase: string;
  inventory_status: string;
  detected_disruptions: string[];
  audit_trail: AuditEntry[];
}

// ============= React Component =============
const App = () => {
  const [loading, setLoading] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [simulateDisruption, setSimulateDisruption] = useState(false);

  // API URL with fallback to localhost for development
  const API_BASE_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleStartWorkflow = async () => {
    setLoading(true);
    setError(null);
    setWorkflowStatus(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/place_order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          order_id: `ORD-${Date.now()}`,
          simulate_disruption: simulateDisruption,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `API error: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      
      if (!data.state) {
        throw new Error('Invalid API response: missing state');
      }

      setWorkflowStatus({
        status: data.state.status || 'Unknown',
        current_phase: data.state.current_phase || 'Unknown',
        inventory_status: data.state.inventory_status || 'Unknown',
        detected_disruptions: data.state.detected_disruptions || [],
        audit_trail: data.state.audit_trail || [],
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Workflow error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string): string => {
    const lowerStatus = status.toLowerCase();
    if (lowerStatus.includes('fulfilled') || lowerStatus.includes('success'))
      return 'text-green-400';
    if (lowerStatus.includes('error')) return 'text-red-400';
    if (lowerStatus.includes('disruption')) return 'text-yellow-400';
    return 'text-blue-400';
  };

  const getSystemHealth = (): string => {
    if (!workflowStatus) return 'Idle';
    if (workflowStatus.status.includes('Error')) return 'Critical';
    if (workflowStatus.detected_disruptions.length > 0) return 'Warning';
    return 'Healthy';
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-800 px-6 py-6">
        <h1 className="text-4xl font-bold text-blue-400">
          🏭 Supply Chain Management System
        </h1>
        <p className="mt-2 text-gray-400">
          AI-Powered Autonomous Workflow with LLM Intelligence
        </p>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-6xl px-6 py-8">
        {/* Controls Section */}
        <section className="mb-8 space-y-4 rounded-lg border border-gray-700 bg-gray-800 p-6">
          <h2 className="text-xl font-semibold text-gray-300">Workflow Controls</h2>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <button
              onClick={handleStartWorkflow}
              disabled={loading}
              className={`rounded-lg px-6 py-3 font-semibold transition-all ${
                loading
                  ? 'cursor-not-allowed bg-gray-600 text-gray-400'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? '⏳ Processing...' : '▶️ Start Workflow'}
            </button>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={simulateDisruption}
                onChange={(e) => setSimulateDisruption(e.target.checked)}
                disabled={loading}
                className="h-4 w-4 rounded bg-gray-700"
              />
              <span className="text-gray-300">Simulate Supply Chain Disruption</span>
            </label>
          </div>
        </section>

        {/* System Health */}
        {workflowStatus && (
          <section className="mb-8 rounded-lg border border-gray-700 bg-gray-800 p-6">
            <h2 className="text-lg font-semibold text-gray-300">System Health</h2>
            <div className="mt-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Status</p>
                <p className={`text-2xl font-bold ${getStatusColor(workflowStatus.status)}`}>
                  {getSystemHealth()}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Current Phase</p>
                <p className="text-2xl font-bold text-purple-400">
                  {workflowStatus.current_phase}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Inventory</p>
                <p className="text-2xl font-bold text-teal-400">
                  {workflowStatus.inventory_status}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Error Section */}
        {error && (
          <section className="mb-8 rounded-lg border border-red-700 bg-red-900/30 p-6">
            <h2 className="text-lg font-semibold text-red-400">⚠️ Error</h2>
            <p className="mt-2 text-red-300">{error}</p>
          </section>
        )}

        {/* Disruptions Alert */}
        {workflowStatus && workflowStatus.detected_disruptions.length > 0 && (
          <section className="mb-8 rounded-lg border border-yellow-700 bg-yellow-900/30 p-6">
            <h2 className="text-lg font-semibold text-yellow-400">
              ⚠️ Supply Chain Disruptions Detected
            </h2>
            <ul className="mt-4 space-y-2">
              {workflowStatus.detected_disruptions.map((disruption, idx) => (
                <li key={idx} className="flex items-center gap-3 text-yellow-300">
                  <span className="inline-block h-2 w-2 rounded-full bg-yellow-400" />
                  {disruption}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Execution Log */}
        {workflowStatus && workflowStatus.audit_trail.length > 0 && (
          <section className="rounded-lg border border-gray-700 bg-gray-800 p-6">
            <h2 className="text-lg font-semibold text-gray-300">📋 Execution Log</h2>
            <div className="mt-4 space-y-3">
              {workflowStatus.audit_trail.map((entry, idx) => {
                let agentColor = 'text-gray-400';
                if (entry.agent === 'UI') agentColor = 'text-blue-400';
                else if (entry.agent === 'Intelligence') agentColor = 'text-green-400';
                else if (entry.agent === 'Orchestration') agentColor = 'text-purple-400';
                else if (entry.agent === 'Compliance') agentColor = 'text-teal-400';

                return (
                  <div
                    key={idx}
                    className="flex gap-4 border-l-2 border-gray-600 pl-4"
                  >
                    <div className="flex-shrink-0">
                      <span className={`font-mono font-semibold ${agentColor}`}>
                        [{entry.agent}]
                      </span>
                    </div>
                    <div className="flex-grow">
                      <p className="text-gray-300">{entry.action}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default App;
