import { useState } from 'react';
import './App.css';

interface AuditEntry {
  agent: string;
  action: string;
}

interface WorkflowState {
  status: string;
  phase: string;
  disruptions: string[];
  audit_trail: AuditEntry[];
}

const App = () => {
  const [loading, setLoading] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [simulateDisruption, setSimulateDisruption] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleStartWorkflow = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/place_order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: `ORD-${Date.now()}`,
          simulate_disruption: simulateDisruption
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setWorkflowStatus({
        status: data.state?.status || 'Processing',
        phase: data.state?.current_phase || 'Unknown',
        disruptions: data.state?.detected_disruptions || [],
        audit_trail: data.state?.audit_trail || []
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🏭 Supply Chain Management System</h1>
        <p>AI-Powered Autonomous Workflow with LLM Intelligence</p>
      </header>

      <main className="app-main">
        <section className="controls">
          <button 
            onClick={handleStartWorkflow} 
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? 'Processing...' : 'Start Workflow'}
          </button>
          
          <label className="checkbox-label">
            <input 
              type="checkbox" 
              checked={simulateDisruption}
              onChange={(e) => setSimulateDisruption(e.target.checked)}
              disabled={loading}
            />
            Simulate Disruption
          </label>
        </section>

        {error && (
          <section className="error-section">
            <h2>⚠️ Error</h2>
            <p>{error}</p>
          </section>
        )}

        {workflowStatus && (
          <section className="status-section">
            <div className="status-card">
              <h2>Workflow Status</h2>
              <div className="status-details">
                <p><strong>Status:</strong> <span className={`status-${workflowStatus.status.toLowerCase()}`}>{workflowStatus.status}</span></p>
                <p><strong>Phase:</strong> {workflowStatus.phase}</p>
                
                {workflowStatus.disruptions.length > 0 && (
                  <div className="disruptions-section">
                    <strong>⚠️ Disruptions Detected:</strong>
                    <ul>
                      {workflowStatus.disruptions.map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {workflowStatus.audit_trail.length > 0 && (
              <div className="audit-card">
                <h3>📋 Audit Trail</h3>
                <ul className="audit-list">
                  {workflowStatus.audit_trail.map((entry, i) => (
                    <li key={i} className={`audit-item audit-${entry.agent.toLowerCase()}`}>
                      <strong>[{entry.agent}]:</strong> {entry.action}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
};

export default App;
