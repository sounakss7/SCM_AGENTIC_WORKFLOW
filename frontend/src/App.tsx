import { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Box,
  CheckCircle2,
  Cpu,
  Factory,
  Layers,
  Play,
  RefreshCw,
  ServerCrash,
  TerminalSquare,
  FileText,
  X,
  Zap,
  BrainCircuit,
  Settings,
  ShieldCheck,
  Truck,
  Map,
  DollarSign,
  MapPin,
  Search
} from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import './App.css';

// ============= Type Definitions =============
interface AuditEntry {
  timestamp: string;
  agent: string;
  action: string;
  model_used?: string;
}

interface WorkflowState {
  status: string;
  current_phase: string;
  inventory_status: string;
  route_selected: string;
  carrier_status: string;
  optimization_cycles: number;
  detected_disruptions: string[];
  audit_trail: AuditEntry[];
  cost_savings: string;
  live_location: string;
  order_id?: string;
}

// ============= React Component =============
const App = () => {
  const [loading, setLoading] = useState(false);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [simulateDisruption, setSimulateDisruption] = useState(false);
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [customOrderId, setCustomOrderId] = useState('');

  // API URL with fallback to localhost for development
  const API_BASE_URL = import.meta.env.VITE_API_URL || '';

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
          order_id: customOrderId.trim() || `ORD-${Date.now()}`,
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
        route_selected: data.state.route_selected || 'Standard',
        carrier_status: data.state.carrier_status || 'Pending',
        optimization_cycles: data.state.optimization_cycles || 0,
        detected_disruptions: data.state.detected_disruptions || [],
        audit_trail: data.state.audit_trail || [],
        cost_savings: data.state.cost_savings || '$0.00',
        live_location: data.state.live_location || 'Tracking...',
        order_id: data.order_id || customOrderId.trim() || `ORD-${Date.now()}`,
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

  const generatePDFReport = () => {
    if (!workflowStatus) return;

    const doc = new jsPDF();

    // Header
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(67, 56, 202); // Indigo-700
    doc.text("SCM Agentic Workflow Report", 14, 25);

    // Metadata
    doc.setFontSize(11);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(80, 80, 80);
    doc.text(`Generated at: ${new Date().toLocaleString()}`, 14, 35);
    doc.text(`Overall Health Status: ${workflowStatus.status}`, 14, 43);
    doc.text(`Inventory State: ${workflowStatus.inventory_status}`, 14, 51);

    let currentY = 62;

    // Disruptions
    if (workflowStatus.detected_disruptions.length > 0) {
      doc.setFont("helvetica", "bold");
      doc.setTextColor(220, 38, 38); // Red-600
      doc.text("! Detected Supply Chain Disruptions", 14, currentY);
      doc.setFont("helvetica", "normal");
      currentY += 8;
      workflowStatus.detected_disruptions.forEach((d) => {
        doc.text(`• ${d}`, 18, currentY);
        currentY += 7;
      });
      currentY += 6;
    }

    // Audit Trail Table
    doc.setFont("helvetica", "bold");
    doc.setTextColor(15, 23, 42); // Slate-900
    doc.text("Multi-Agent Intelligence Audit Trail", 14, currentY + 4);

    const tableData = workflowStatus.audit_trail.map(entry => [
      entry.timestamp,
      entry.agent,
      entry.model_used || 'Standard Engine',
      entry.action
    ]);

    autoTable(doc, {
      startY: currentY + 10,
      head: [['Timestamp', 'Agent Node', 'AI Engine', 'Executed Action']],
      body: tableData,
      theme: 'grid',
      headStyles: { fillColor: [67, 56, 202], textColor: 255 },
      styles: { fontSize: 9, cellPadding: 4, overflow: 'linebreak' },
      columnStyles: {
        0: { cellWidth: 25 },
        1: { cellWidth: 25 },
        2: { cellWidth: 35 },
        3: { cellWidth: 'auto' }
      }
    });

    const fileName = `SCM_Protocol_Report_${Date.now()}.pdf`;
    doc.save(fileName);
  };

  const getStatusColor = (status: string): string => {
    const lowerStatus = status.toLowerCase();
    if (lowerStatus.includes('fulfilled') || lowerStatus.includes('success'))
      return 'text-emerald-400';
    if (lowerStatus.includes('error')) return 'text-rose-400';
    if (lowerStatus.includes('disruption')) return 'text-amber-400';
    return 'text-indigo-400';
  };

  const getSystemHealth = (): string => {
    if (!workflowStatus) return 'Idle';
    if (workflowStatus.status.includes('Error')) return 'Critical';
    if (workflowStatus.detected_disruptions.length > 0) return 'Warning';
    return 'Healthy';
  };

  const renderAgentIcon = (agent: string) => {
    switch (agent) {
      case 'UI': return <Layers className="w-5 h-5 text-indigo-400" />;
      case 'Intelligence': return <Cpu className="w-5 h-5 text-emerald-400" />;
      case 'Orchestration': return <Activity className="w-5 h-5 text-fuchsia-400" />;
      case 'Compliance': return <CheckCircle2 className="w-5 h-5 text-teal-400" />;
      default: return <ServerCrash className="w-5 h-5 text-rose-400" />;
    }
  };

  return (
    <div className="min-h-screen text-slate-100 font-sans pb-16">

      {/* Log Terminal Modal Overlay */}
      {isLogModalOpen && workflowStatus && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in zoom-in-95 duration-200">
          <div className="bg-[#0A0A10] border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden ring-1 ring-white/10">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80">
              <div className="flex items-center gap-3">
                <TerminalSquare className="w-5 h-5 text-emerald-400" />
                <h3 className="text-white font-bold tracking-wide">Live Diagnostics Console</h3>
              </div>
              <button
                onClick={() => setIsLogModalOpen(false)}
                className="p-1.5 rounded-full hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors"
                title="Close Terminal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Terminal View area */}
            <div className="p-6 overflow-y-auto font-mono text-sm flex-grow">
              <div className="space-y-3">
                <div className="text-slate-500 mb-6 pb-4 border-b border-slate-800">
                  $ tail -f /var/log/scm-agentic-cluster.log<br />
                  [SYS] Initializing secure LLM routing streams... OK.<br />
                  [SYS] Connected to embedded Qdrant Vector memory block... OK.<br />
                  [SYS] Multi-Agent Pipeline standing by.
                </div>
                {workflowStatus.audit_trail.map((entry, idx) => (
                  <div key={idx} className="pb-3 border-b border-slate-800/50 last:border-0 hover:bg-slate-800/30 p-2 -mx-2 rounded transition-colors group">
                    <div className="flex flex-wrap gap-3 items-start">
                      <span className="text-slate-500 shrink-0">[{entry.timestamp}]</span>
                      <span className={`font-bold shrink-0 ${entry.agent === 'UI' ? 'text-indigo-400' :
                          entry.agent === 'Intelligence' ? 'text-emerald-400' :
                            entry.agent === 'Orchestration' ? 'text-fuchsia-400' :
                              'text-teal-400'
                        }`}>
                        [{entry.agent.toUpperCase()}_NODE]:
                      </span>
                      <span className="text-slate-300 break-words group-hover:text-emerald-50 transition-colors">
                        {entry.action}
                      </span>
                    </div>
                  </div>
                ))}
                {!loading && <div className="text-emerald-500/50 animate-pulse pt-4 flex gap-2"><span>$</span><span className="w-2 h-4 bg-emerald-500 inline-block mt-0.5"></span></div>}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="bg-slate-900/80 px-6 py-4 border-t border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400 font-mono flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Terminal connected. Read-only output.
              </span>
              <button
                onClick={() => setIsLogModalOpen(false)}
                className="text-xs font-bold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 px-5 py-2.5 rounded-xl transition-colors shadow-lg"
              >
                Close Console
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Premium Header */}
      <header className="sticky top-0 z-40 glass-panel border-b-0 border-x-0 rounded-none bg-slate-900/80 mb-10 px-6 py-5 shadow-2xl">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-fuchsia-600 rounded-xl shadow-lg ring-1 ring-white/10">
              <Factory className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-purple-300 to-fuchsia-200 tracking-tight">
                SCM Agentic Workflow
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-1 font-medium tracking-wide">
                AI-Powered Autonomous System with LLM Intelligence
              </p>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800/80 border border-slate-700/50 text-xs font-medium text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            System Online
          </div>
        </div>
      </header>

      {/* Main Content Dashboard */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 space-y-8">

        {/* Top Control Panel */}
        <section className="glass-panel p-6 sm:p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 group-hover:bg-indigo-500/20 transition-all duration-700"></div>

          <div className="relative z-10 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <Play className="w-5 h-5 text-indigo-400" /> Control Center
              </h2>
              <p className="text-slate-400 text-sm max-w-md leading-relaxed">
                Initialize the autonomous agent cluster to assess constraints, monitor inventory, and detect real-time transit disruptions.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              {/* Order ID Tracker Input */}
              <div className="flex items-center gap-2 bg-slate-900/60 p-1.5 pl-3 rounded-2xl border border-slate-700/50 shadow-inner">
                 <Search className="w-4 h-4 text-slate-500" />
                 <input
                   type="text"
                   placeholder="Enter Custom Order ID"
                   value={customOrderId}
                   onChange={(e) => setCustomOrderId(e.target.value)}
                   disabled={loading}
                   className="bg-transparent border-none text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-0 w-44"
                 />
              </div>

              {/* Export & Log Buttons */}
              {workflowStatus && !loading && (
                <div className="flex items-center gap-3 animate-in fade-in slide-in-from-left-4 duration-500">
                  <button
                    onClick={() => setIsLogModalOpen(true)}
                    className="flex items-center gap-2 rounded-xl px-5 py-3 bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-all hover:-translate-y-0.5 shadow-lg"
                    title="View Raw Agent Logs"
                  >
                    <TerminalSquare className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-bold">Terminal Logs</span>
                  </button>
                  <button
                    onClick={generatePDFReport}
                    className="flex items-center gap-2 rounded-xl px-5 py-3 bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-all hover:-translate-y-0.5 shadow-lg"
                    title="Download PDF Report"
                  >
                    <FileText className="w-4 h-4 text-fuchsia-400" />
                    <span className="text-sm font-bold">Export PDF</span>
                  </button>
                </div>
              )}

              {/* Main Workflow Execute Box */}
              <div className="flex items-center gap-5 bg-slate-900/60 p-2 pl-5 rounded-2xl border border-slate-700/50 shadow-inner">
                <label className="flex items-center gap-3 cursor-pointer group/toggle">
                  <div className="relative flex items-center">
                    <input
                      type="checkbox"
                      checked={simulateDisruption}
                      onChange={(e) => setSimulateDisruption(e.target.checked)}
                      disabled={loading}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500 group-hover/toggle:ring-2 ring-amber-500/30 transition-all"></div>
                  </div>
                  <span className="text-sm font-medium text-slate-300 group-hover/toggle:text-amber-200 transition-colors">
                    Inject Threats
                  </span>
                </label>

                <button
                  onClick={handleStartWorkflow}
                  disabled={loading}
                  className={`flex items-center min-w-[200px] justify-center gap-2 rounded-xl px-7 py-3.5 font-bold shadow-xl transition-all duration-300 transform outline-none focus:ring-4 ${loading
                      ? 'cursor-not-allowed bg-slate-800 text-slate-500 border border-slate-700 scale-95'
                      : 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5 focus:ring-indigo-500/30 ring-offset-2 ring-offset-slate-900'
                    }`}
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      <span>Executing Protocol...</span>
                    </>
                  ) : (
                    <>
                      <Activity className="w-5 h-5" />
                      <span>Initialize Agents</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Global Error Banner */}
        {error && (
          <div className="glass-panel border-rose-500/30 bg-rose-950/30 p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-rose-500/20 rounded-full">
                <AlertTriangle className="w-6 h-6 text-rose-400" />
              </div>
              <div>
                <h3 className="text-rose-200 font-bold">System Failure</h3>
                <p className="text-rose-300/80 text-sm mt-0.5 break-all">{error}</p>
              </div>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-white text-sm bg-rose-900/50 hover:bg-rose-800 px-4 py-2 rounded-lg transition-colors"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Dynamic Workflow Dashboard */}
        {workflowStatus && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in zoom-in-95 duration-500">

            {/* Health & Metrics Column */}
            <div className="lg:col-span-1 space-y-6">

              <div className="glass-card p-6 relative overflow-hidden">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-slate-400 font-semibold text-sm uppercase tracking-wider">Health Status</h3>
                  <div className={`p-1.5 rounded-full ${workflowStatus.status.includes('Error') ? 'bg-rose-500/20' : workflowStatus.detected_disruptions.length > 0 ? 'bg-amber-500/20' : 'bg-emerald-500/20'}`}>
                    <Activity className={`w-4 h-4 ${workflowStatus.status.includes('Error') ? 'text-rose-400' : workflowStatus.detected_disruptions.length > 0 ? 'text-amber-400' : 'text-emerald-400'}`} />
                  </div>
                </div>
                <div className="flex items-end gap-3">
                  <p className={`text-4xl font-extrabold tracking-tight ${getStatusColor(workflowStatus.status)}`}>
                    {getSystemHealth()}
                  </p>
                  {loading && (
                    <div className="w-3 h-3 rounded-full bg-indigo-500 animate-pulse-ring mb-2"></div>
                  )}
                </div>
                <p className="text-slate-500 text-sm mt-2 flex items-center gap-1.5 truncate">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 inline-block"></span>
                  State: <span className="text-slate-300 font-medium truncate">{workflowStatus.status}</span>
                </p>
              </div>

              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-slate-400 font-semibold text-sm uppercase tracking-wider">Current Phase</h3>
                  <RefreshCw className={`w-4 h-4 text-purple-400 ${loading ? 'animate-spin' : ''}`} />
                </div>
                <p className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-fuchsia-400 mb-2">
                  {workflowStatus.current_phase}
                </p>
                <div className="w-full bg-slate-800 rounded-full h-1.5 mt-4">
                  <div className={`h-1.5 rounded-full transition-all duration-1000 ${workflowStatus.current_phase === 'Compliance' ? 'w-full bg-emerald-500' :
                      workflowStatus.current_phase === 'Execution' ? 'w-3/4 bg-fuchsia-500' :
                        'w-1/3 bg-indigo-500'
                    }`}></div>
                </div>
              </div>

              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-slate-400 font-semibold text-sm uppercase tracking-wider">Inventory</h3>
                  <Box className="w-4 h-4 text-teal-400" />
                </div>
                <p className="text-2xl font-bold text-teal-400">
                  {workflowStatus.inventory_status}
                </p>
                <div className="mt-4 pt-4 border-t border-slate-700/50">
                   <div className="flex items-center justify-between mb-2">
                     <span className="text-xs text-slate-500 uppercase font-semibold">Logistics Route</span>
                     <Map className="w-3.5 h-3.5 text-orange-400" />
                   </div>
                   <p className="text-sm font-bold text-orange-400 truncate" title={workflowStatus.route_selected}>
                     {workflowStatus.route_selected}
                   </p>
                </div>
                <div className="mt-3">
                   <div className="flex items-center justify-between mb-1">
                     <span className="text-xs text-slate-500 uppercase font-semibold">Carrier API</span>
                     <Truck className="w-3.5 h-3.5 text-blue-400" />
                   </div>
                   <div className="flex items-center gap-2">
                     <p className={`text-sm font-bold ${workflowStatus.carrier_status.includes('Reject') || workflowStatus.carrier_status.includes('Fail') ? 'text-rose-400' : 'text-blue-400'}`}>
                       {workflowStatus.carrier_status}
                     </p>
                     {workflowStatus.optimization_cycles > 0 && (
                        <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 text-[10px] font-bold rounded-full animate-pulse">
                          Auto-Recovered
                        </span>
                     )}
                   </div>
                </div>
              </div>

              {/* Premium Live Tracking Widget */}
              <div className="glass-card overflow-hidden border border-slate-700/50 relative group">
                 <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/10 blur-3xl rounded-full transition-all duration-700 translate-x-1/2 -translate-y-1/2 group-hover:bg-blue-500/20"></div>
                 
                 <div className="p-6 relative z-10">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-blue-500/20 rounded-lg shadow-inner border border-blue-500/20">
                          <MapPin className="w-4 h-4 text-blue-400" />
                        </div>
                        <h3 className="text-slate-100 font-bold tracking-wide">Live GPS Telemetry</h3>
                      </div>
                      <span className="text-[10px] uppercase tracking-widest font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span> Target Lock
                      </span>
                    </div>

                    {/* Dynamic Map/Timeline Visualization */}
                    <div className="relative h-20 w-full bg-slate-900/60 rounded-xl mb-5 overflow-hidden border border-slate-700/50 shadow-inner flex items-center px-4">
                       {/* Background Map Grid Pattern */}
                       <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)", backgroundSize: "16px 16px" }}></div>
                       
                       {/* Dotted route path */}
                       <div className="absolute top-1/2 left-8 right-8 h-[2px] border-t-2 border-dashed border-slate-700/80 -translate-y-1/2"></div>
                       
                       {/* Route Nodes */}
                       <div className="absolute top-1/2 left-[10%] w-3 h-3 rounded-full bg-slate-600 border-2 border-slate-800 -translate-y-1/2 -translate-x-1/2 z-10"></div>
                       <div className="absolute top-1/2 left-[50%] w-3 h-3 rounded-full bg-slate-600 border-2 border-slate-800 -translate-y-1/2 -translate-x-1/2 z-10"></div>
                       <div className="absolute top-1/2 left-[90%] w-3 h-3 rounded-full bg-slate-600 border-2 border-slate-800 -translate-y-1/2 -translate-x-1/2 z-10"></div>

                       {/* Pulsing Tracker Dot */}
                       <div className={`absolute top-1/2 -translate-y-1/2 flex flex-col items-center transition-all duration-[1500ms] ease-out z-20 ${
                         workflowStatus.live_location.includes('System') || workflowStatus.live_location.includes('Intake') ? 'left-[0%]' : 
                         workflowStatus.live_location.includes('Origin') || workflowStatus.live_location.includes('Packing') ? 'left-[10%]' : 
                         workflowStatus.live_location.includes('Reject') || workflowStatus.live_location.includes('Port') || workflowStatus.live_location.includes('Secondary') ? 'left-[50%]' : 
                         'left-[90%]'
                       }`}>
                          <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center -translate-x-1/2">
                             <div className="absolute w-full h-full rounded-full border border-blue-400/30 animate-ping"></div>
                             <div className="w-3.5 h-3.5 bg-blue-400 rounded-full shadow-[0_0_15px_rgba(96,165,250,0.9)] z-10"></div>
                          </div>
                       </div>
                    </div>

                    <p className="text-sm font-semibold text-slate-400 flex items-center gap-2 bg-slate-900/40 p-3 rounded-lg border border-slate-800/50">
                      <span className="text-xs uppercase tracking-wider text-slate-500">Vector:</span>
                      <span className="text-blue-300 drop-shadow-sm font-bold tracking-wide truncate">{workflowStatus.live_location}</span>
                    </p>
                 </div>
                 
                 {/* Premium Financial Footer */}
                 <div className="bg-gradient-to-r from-slate-900 via-slate-900/95 to-slate-900 px-6 py-4 border-t border-slate-800 flex justify-between items-center relative overflow-hidden">
                    <div className="absolute left-0 bottom-0 top-0 w-1 bg-gradient-to-b from-emerald-400 to-teal-600"></div>
                    <div className="flex items-center gap-4 relative z-10">
                       <div className="p-2.5 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-inner">
                         <DollarSign className="w-5 h-5 text-emerald-400" />
                       </div>
                       <div>
                          <p className="text-[10px] uppercase font-black text-slate-400 tracking-widest mb-0.5">Financial Impact Delta</p>
                          <p className="text-xl sm:text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-300 tracking-tight drop-shadow-sm">
                            {workflowStatus.cost_savings}
                          </p>
                       </div>
                    </div>
                 </div>
              </div>

            </div>

            {/* Details Column */}
            <div className="lg:col-span-2 space-y-6 flex flex-col">

              {/* Disruptions Warning block */}
              {workflowStatus.detected_disruptions.length > 0 && (
                <div className="glass-panel border-amber-500/30 bg-amber-950/20 p-6 flex-shrink-0 animate-in slide-in-from-right-8 duration-500">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-amber-500/20 rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                    </div>
                    <h3 className="text-lg font-bold text-amber-300">
                      Disruptions Detected
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                    {workflowStatus.detected_disruptions.map((disruption, idx) => (
                      <div key={idx} className="bg-amber-900/40 border border-amber-700/50 rounded-lg p-3 flex items-start gap-3">
                        <span className="relative flex h-3 w-3 mt-1">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                        </span>
                        <span className="text-amber-100 text-sm font-medium leading-relaxed">{disruption}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Advanced Audit Trail */}
              {workflowStatus.audit_trail.length > 0 && (
                <div className="glass-panel p-6 sm:p-8 flex-grow flex flex-col overflow-hidden">
                  <div className="flex flex-wrap items-center justify-between mb-8 gap-4">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      Agent Event Matrix
                    </h2>
                    <span className="px-3 py-1 bg-slate-800 rounded-full text-xs font-semibold text-slate-400 border border-slate-700 shadow-inner">
                      {workflowStatus.audit_trail.length} Executions
                    </span>
                  </div>

                  <div className="relative flex-grow overflow-hidden before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
                    <div className="space-y-8 relative py-4">
                      {workflowStatus.audit_trail.map((entry, idx) => {
                        return (
                          <div
                            key={idx}
                            className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active animate-in fade-in slide-in-from-bottom-4 duration-700 fill-mode-both"
                            style={{ animationDelay: `${idx * 150}ms` }}
                          >
                            <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-slate-900 bg-slate-800 text-slate-500 group-[.is-active]:text-emerald-50 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 transition-transform duration-300 hover:scale-110">
                              {renderAgentIcon(entry.agent)}
                            </div>

                            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-card p-4 hover:border-indigo-500/50 relative overflow-hidden">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-bold text-slate-200 text-sm">
                                  {entry.agent} Controller
                                </span>
                                <time className="text-xs font-mono text-slate-500">{entry.timestamp}</time>
                              </div>
                              <p className="text-slate-300 text-sm leading-relaxed pt-1">
                                {entry.action}
                              </p>
                              
                              {/* Advanced Telemetry Badge */}
                              {entry.model_used && (
                                <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950/60 border border-slate-700 shadow-inner">
                                  {entry.model_used.includes("Groq") && <Zap className="w-3.5 h-3.5 text-amber-400" />}
                                  {entry.model_used.includes("Mistral") && <BrainCircuit className="w-3.5 h-3.5 text-cyan-400" />}
                                  {entry.model_used.includes("Guard") && <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
                                  {entry.model_used.includes("Deterministic") && <Settings className="w-3.5 h-3.5 text-slate-400" />}
                                  {entry.model_used.includes("Graph Node") && <Layers className="w-3.5 h-3.5 text-fuchsia-400" />}
                                  <span className="text-[11px] font-mono tracking-wider font-semibold text-slate-300 uppercase">
                                    {entry.model_used}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

            </div>

          </div>
        )}
      </main>
    </div>
  );
};

export default App;
