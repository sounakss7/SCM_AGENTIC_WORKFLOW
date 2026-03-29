import React, { useState, useEffect, useRef } from 'react';
import { 
  ShoppingCart, Activity, Settings, ShieldCheck, Truck, 
  AlertTriangle, CloudLightning, CheckCircle2, Play,
  FileText, RefreshCw, ChevronDown, Info, XCircle,
  ServerCrash
} from 'lucide-react';

type Phase = 'Idle' | 'Planning' | 'Execution' | 'Monitoring & Optimization' | 'Completed';
type AgentType = 'User Interface' | 'Supply Chain Intelligence' | 'Process Orchestration' | 'Verification & Compliance' | 'External Entities';
type LogType = 'info' | 'warning' | 'error' | 'success';

interface AuditEntry {
  id: string;
  timestamp: string;
  agent: AgentType;
  action: string;
  details: string;
  type: LogType;
}

const agentColors: Record<AgentType, string> = {
  'User Interface': 'text-blue-700 bg-blue-50 border-blue-200',
  'Supply Chain Intelligence': 'text-purple-700 bg-purple-50 border-purple-200',
  'Process Orchestration': 'text-emerald-700 bg-emerald-50 border-emerald-200',
  'Verification & Compliance': 'text-amber-700 bg-amber-50 border-amber-200',
  'External Entities': 'text-slate-700 bg-slate-50 border-slate-200',
};

const agentIcons: Record<AgentType, React.ReactNode> = {
  'User Interface': <ShoppingCart className="w-4 h-4" />,
  'Supply Chain Intelligence': <Activity className="w-4 h-4" />,
  'Process Orchestration': <Settings className="w-4 h-4" />,
  'Verification & Compliance': <ShieldCheck className="w-4 h-4" />,
  'External Entities': <Truck className="w-4 h-4" />,
};

const typeIcons: Record<LogType, React.ReactNode> = {
  'info': <Info className="w-4 h-4 text-blue-500" />,
  'warning': <AlertTriangle className="w-4 h-4 text-amber-500" />,
  'error': <XCircle className="w-4 h-4 text-red-500" />,
  'success': <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
};

export default function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [orderId, setOrderId] = useState('ORD-88492');
  const [simWeather, setSimWeather] = useState(false);
  const [simCarrier, setSimCarrier] = useState(false);

  const [phase, setPhase] = useState<Phase>('Idle');
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [retryCount, setRetryCount] = useState(0);
  const [activeAgent, setActiveAgent] = useState<AgentType | null>(null);

  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [auditTrail]);

  const startWorkflow = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setPhase('Planning');
    setAuditTrail([]);
    setErrors([]);
    setRetryCount(0);
    setActiveAgent(null);

    const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

    const log = (agent: AgentType, action: string, details: string, type: LogType = 'info') => {
      setActiveAgent(agent);
      setAuditTrail(prev => [...prev, {
        id: Math.random().toString(36).substring(7),
        timestamp: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        agent,
        action,
        details,
        type
      }]);
    };

    // --- PHASE 1: PLANNING ---
    log('User Interface', '1. User Places Order', `Order ${orderId} submitted for processing.`, 'info');
    await delay(1200);

    log('Supply Chain Intelligence', '2. Order Reception & Assessment', 'Performing Demand Analysis and Disruption Screening.', 'info');
    await delay(1500);

    log('Process Orchestration', '3. Sourcing & Logistics Planning', 'Executing Check Inventory Status and Select Route & Carrier.', 'info');
    await delay(1500);

    log('Verification & Compliance', '4. Auditable Verification', 'Ensuring regulatory compliance. Locking Decision Audit Trail.', 'success');
    await delay(1200);

    // --- PHASE 2: EXECUTION ---
    setPhase('Execution');
    
    log('Process Orchestration', '5. Order Fulfillment', 'Initiating fulfillment sequence.', 'info');
    await delay(1000);

    log('Process Orchestration', '6. Autonomous Execution', 'Handing off to external entities.', 'info');
    await delay(1000);

    log('External Entities', 'Supplier P.O. Creation', 'Purchase order transmitted to supplier.', 'success');
    await delay(1000);
    
    log('External Entities', 'Warehouse Picking', 'Automated picking sequence completed.', 'success');
    await delay(1000);

    let currentRetries = 0;
    let carrierSuccess = false;

    while (!carrierSuccess && currentRetries <= 3) {
      log('External Entities', 'Carrier Booking', `Attempting to book carrier (Attempt ${currentRetries + 1}).`, 'info');
      await delay(1500);

      if (simCarrier && currentRetries === 0) {
        log('External Entities', 'Error Handling', 'Simulated Carrier Error: Capacity rejected.', 'error');
        setErrors(prev => [...prev, 'Carrier capacity rejection']);
        await delay(1200);
        
        currentRetries++;
        setRetryCount(currentRetries);
        log('Process Orchestration', 'Self-Correction Protocols', 'Triggering Alternative Supplier Selection and Autonomous Rerouting.', 'warning');
        await delay(1800);
      } else {
        carrierSuccess = true;
        log('External Entities', 'Carrier Booking', 'Carrier successfully booked and confirmed.', 'success');
      }
    }

    if (!carrierSuccess) {
      log('Process Orchestration', 'Execution Failed', 'Max retries reached. Manual intervention required.', 'error');
      setPhase('Completed');
      setIsRunning(false);
      return;
    }

    // --- PHASE 3: MONITORING & OPTIMIZATION ---
    setPhase('Monitoring & Optimization');
    await delay(1200);

    log('Supply Chain Intelligence', 'Monitoring', 'Real-time performance data tracking active. Route Planning engaged.', 'info');
    await delay(1500);

    if (simWeather) {
      log('Supply Chain Intelligence', 'Disruption Detection', 'Simulated Weather Disruption: Severe storm detected on route.', 'error');
      setErrors(prev => [...prev, 'Weather disruption detected']);
      await delay(1500);

      log('Supply Chain Intelligence', 'Autonomous Optimization', 'Calculating dynamic adjustments to avoid disruption.', 'warning');
      await delay(1500);

      log('Process Orchestration', 'Self-Correction Protocols', 'Executing Autonomous Rerouting based on optimized path.', 'warning');
      await delay(1500);
    }

    log('Process Orchestration', '7. Delivery & Order Completion', 'Shipment arrived. Non-time models and dynamic adjustments verified.', 'success');
    await delay(1500);

    setPhase('Completed');
    log('User Interface', 'Order Fulfilled', 'Final Review & Reporting generated. Workflow complete.', 'success');
    setActiveAgent(null);
    setIsRunning(false);
  };

  const getPhaseStatus = (p: Phase) => {
    const phases: Phase[] = ['Planning', 'Execution', 'Monitoring & Optimization', 'Completed'];
    const currentIndex = phases.indexOf(phase === 'Idle' ? 'Planning' : phase);
    const pIndex = phases.indexOf(p);
    
    if (pIndex < currentIndex) return 'completed';
    if (pIndex === currentIndex && phase !== 'Idle') return 'active';
    return 'pending';
  };

  return (
    <div className="flex h-screen bg-slate-100 text-slate-900 font-sans overflow-hidden">
      
      {/* SIDEBAR */}
      <div className="w-80 bg-white border-r border-slate-200 flex flex-col shadow-sm z-10">
        <div className="p-6 border-b border-slate-200 bg-slate-50">
          <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-600" />
            Agentic SCM
          </h1>
          <p className="text-sm text-slate-500 mt-1">Autonomous Enterprise Workflow</p>
        </div>

        <div className="p-6 flex-1 overflow-y-auto">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Order ID</label>
              <input 
                type="text" 
                value={orderId}
                onChange={(e) => setOrderId(e.target.value)}
                disabled={isRunning}
                className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-100 disabled:text-slate-500"
              />
            </div>

            <div className="space-y-4 pt-4 border-t border-slate-200">
              <h3 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">Simulations</h3>
              
              <label className="flex items-center justify-between cursor-pointer group">
                <span className="text-sm text-slate-700 flex items-center gap-2">
                  <CloudLightning className="w-4 h-4 text-slate-400 group-hover:text-amber-500 transition-colors" />
                  Weather Disruption
                </span>
                <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                  <input type="checkbox" checked={simWeather} onChange={() => setSimWeather(!simWeather)} disabled={isRunning} className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 appearance-none cursor-pointer transition-transform duration-200 ease-in-out checked:translate-x-5 checked:border-blue-500 border-slate-300" />
                  <label className="toggle-label block overflow-hidden h-5 rounded-full bg-slate-300 cursor-pointer"></label>
                </div>
              </label>

              <label className="flex items-center justify-between cursor-pointer group">
                <span className="text-sm text-slate-700 flex items-center gap-2">
                  <ServerCrash className="w-4 h-4 text-slate-400 group-hover:text-red-500 transition-colors" />
                  Carrier Error
                </span>
                <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                  <input type="checkbox" checked={simCarrier} onChange={() => setSimCarrier(!simCarrier)} disabled={isRunning} className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 appearance-none cursor-pointer transition-transform duration-200 ease-in-out checked:translate-x-5 checked:border-blue-500 border-slate-300" />
                  <label className="toggle-label block overflow-hidden h-5 rounded-full bg-slate-300 cursor-pointer"></label>
                </div>
              </label>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-slate-200 bg-slate-50">
          <button
            onClick={startWorkflow}
            disabled={isRunning}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {isRunning ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
            {isRunning ? 'Workflow Running...' : 'Start Autonomous Workflow'}
          </button>
        </div>
      </div>

      {/* MAIN DASHBOARD */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Top Progress Bar */}
        <div className="bg-white border-b border-slate-200 px-8 py-6 shadow-sm z-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between relative">
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-100 rounded-full -z-10"></div>
              
              {(['Planning', 'Execution', 'Monitoring & Optimization'] as Phase[]).map((p, i) => {
                const status = getPhaseStatus(p);
                return (
                  <div key={p} className="flex flex-col items-center relative z-10 bg-white px-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors duration-500 ${
                      status === 'completed' ? 'bg-blue-600 border-blue-600 text-white' :
                      status === 'active' ? 'bg-blue-50 border-blue-600 text-blue-600 ring-4 ring-blue-100' :
                      'bg-white border-slate-300 text-slate-400'
                    }`}>
                      {status === 'completed' ? <CheckCircle2 className="w-6 h-6" /> : <span className="font-bold">{i + 1}</span>}
                    </div>
                    <span className={`mt-3 text-sm font-medium ${
                      status === 'active' ? 'text-blue-700' :
                      status === 'completed' ? 'text-slate-800' :
                      'text-slate-400'
                    }`}>{p}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Column: Execution Log */}
            <div className="lg:col-span-2 flex flex-col h-[600px] bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                <h2 className="font-semibold text-slate-800 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-slate-500" />
                  Dynamic Execution Log
                </h2>
                {isRunning && <span className="flex items-center gap-2 text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full"><span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span> Processing</span>}
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/50">
                {auditTrail.length === 0 && !isRunning && (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4">
                    <Settings className="w-12 h-12 opacity-20" />
                    <p>System idle. Start workflow to begin simulation.</p>
                  </div>
                )}
                
                {auditTrail.map((entry) => (
                  <div key={entry.id} className="flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    <div className="flex flex-col items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center border ${agentColors[entry.agent]} shadow-sm`}>
                        {agentIcons[entry.agent]}
                      </div>
                      <div className="w-px h-full bg-slate-200 my-2"></div>
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono text-slate-400">{entry.timestamp}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${agentColors[entry.agent]}`}>
                          {entry.agent}
                        </span>
                      </div>
                      <div className={`p-4 rounded-lg border shadow-sm ${
                        entry.type === 'error' ? 'bg-red-50 border-red-200' :
                        entry.type === 'warning' ? 'bg-amber-50 border-amber-200' :
                        entry.type === 'success' ? 'bg-emerald-50 border-emerald-200' :
                        'bg-white border-slate-200'
                      }`}>
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5">{typeIcons[entry.type]}</div>
                          <div>
                            <h4 className={`text-sm font-bold ${
                              entry.type === 'error' ? 'text-red-800' :
                              entry.type === 'warning' ? 'text-amber-800' :
                              entry.type === 'success' ? 'text-emerald-800' :
                              'text-slate-800'
                            }`}>{entry.action}</h4>
                            <p className={`text-sm mt-1 ${
                              entry.type === 'error' ? 'text-red-700' :
                              entry.type === 'warning' ? 'text-amber-700' :
                              entry.type === 'success' ? 'text-emerald-700' :
                              'text-slate-600'
                            }`}>{entry.details}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            </div>

            {/* Right Column: Health Monitor & Audit Trail */}
            <div className="space-y-8">
              
              {/* Health Monitor */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
                  <h2 className="font-semibold text-slate-800 flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-slate-500" />
                    Workflow Health Monitor
                  </h2>
                </div>
                <div className="p-6 space-y-6">
                  
                  <div>
                    <p className="text-sm text-slate-500 mb-1">System Status</p>
                    <div className="flex items-center gap-2">
                      {phase === 'Idle' ? <span className="flex items-center gap-2 text-slate-600 font-medium"><div className="w-2.5 h-2.5 rounded-full bg-slate-400"></div> Standby</span> :
                       phase === 'Completed' ? <span className="flex items-center gap-2 text-emerald-600 font-medium"><div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div> Completed</span> :
                       errors.length > 0 ? <span className="flex items-center gap-2 text-amber-600 font-medium"><div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></div> Self-Correcting</span> :
                       <span className="flex items-center gap-2 text-blue-600 font-medium"><div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></div> Operational</span>
                      }
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Active Errors</p>
                      <p className={`text-2xl font-bold ${errors.length > 0 ? 'text-red-600' : 'text-slate-800'}`}>{errors.length}</p>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Retries</p>
                      <p className={`text-2xl font-bold ${retryCount > 0 ? 'text-amber-600' : 'text-slate-800'}`}>{retryCount} <span className="text-sm font-normal text-slate-400">/ 3</span></p>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-slate-500 mb-2">Active Agent</p>
                    {activeAgent ? (
                      <div className={`flex items-center gap-3 p-3 rounded-lg border ${agentColors[activeAgent]}`}>
                        {agentIcons[activeAgent]}
                        <span className="text-sm font-semibold">{activeAgent}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50 text-slate-400">
                        <Settings className="w-4 h-4" />
                        <span className="text-sm font-medium">None</span>
                      </div>
                    )}
                  </div>

                  {/* Self-Correction Alerts */}
                  {errors.length > 0 && (
                    <div className="pt-4 border-t border-slate-200 space-y-3">
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Active Protocols</p>
                      {errors.map((err, idx) => (
                        <div key={idx} className="bg-amber-50 border border-amber-200 p-3 rounded-lg flex items-start gap-3 animate-in fade-in zoom-in duration-300">
                          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                          <div>
                            <p className="text-sm font-bold text-amber-800">Self-Correction Engaged</p>
                            <p className="text-xs text-amber-700 mt-1">Responding to: {err}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              </div>

              {/* Audit Trail Expander */}
              <details className="group bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden" open={phase === 'Completed'}>
                <summary className="flex items-center justify-between p-5 font-semibold text-slate-800 cursor-pointer list-none bg-slate-50 hover:bg-slate-100 transition-colors">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-slate-500" />
                    Decision Audit Trail
                  </div>
                  <span className="transition duration-300 group-open:rotate-180 text-slate-400">
                    <ChevronDown className="w-5 h-5" />
                  </span>
                </summary>
                <div className="border-t border-slate-200 max-h-[400px] overflow-y-auto">
                  {auditTrail.length === 0 ? (
                    <p className="p-6 text-sm text-slate-500 text-center">No audit records available.</p>
                  ) : (
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-50 sticky top-0 border-b border-slate-200">
                        <tr>
                          <th className="px-4 py-3 font-medium text-slate-500">Time</th>
                          <th className="px-4 py-3 font-medium text-slate-500">Agent</th>
                          <th className="px-4 py-3 font-medium text-slate-500">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {auditTrail.map((entry) => (
                          <tr key={entry.id} className="hover:bg-slate-50 transition-colors">
                            <td className="px-4 py-3 text-slate-500 font-mono text-xs whitespace-nowrap">{entry.timestamp}</td>
                            <td className="px-4 py-3 font-medium text-slate-700">{entry.agent}</td>
                            <td className="px-4 py-3 text-slate-600">{entry.action}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </details>

            </div>
          </div>
        </div>
      </div>
      
      {/* Custom styles for toggle switch */}
      <style dangerouslySetInnerHTML={{__html: `
        .toggle-checkbox:checked {
          right: 0;
          border-color: #3b82f6;
        }
        .toggle-checkbox:checked + .toggle-label {
          background-color: #bfdbfe;
        }
      `}} />
    </div>
  );
}
