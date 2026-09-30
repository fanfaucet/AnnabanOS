import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Activity,
  Globe,
  Box,
  Layers,
  TrendingUp,
  Users,
  Radio
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('telemetry');

  const [telemetry, setTelemetry] = useState({
    apiLatencyMs: 12.4,
    networkRequestsSec: 1420,
    activeApiEndpoints: 32,
    bandwidthThroughputMbps: 840.5,
    gpuComputeUtil: 78.2
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetry(prev => ({
        ...prev,
        apiLatencyMs: +(11.5 + Math.random() * 2.2).toFixed(2),
        networkRequestsSec: Math.floor(1380 + Math.random() * 80),
        bandwidthThroughputMbps: +(820 + Math.random() * 40).toFixed(1),
        gpuComputeUtil: +(75 + Math.random() * 6).toFixed(1)
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const valuationMetrics = {
    modelType: 'Illustrative Enterprise Value — Simulation',
    impliedValuation: '$223.05M',
    moduleIpValuation: '$35.35M',
    productivityValuation: '$76.80M',
    infrastructureEfficiencyValuation: '$110.90M',
    seriesSeedPostMoney: '$18.75M',
    seedCapitalOutlay: '$2.40M'
  };

  const governanceState = {
    policyVm: 'ACTIVE',
    hep: 'ACTIVE',
    humanAuthority: true,
    autonomousAuthority: false,
    externalEffect: false,
    networkAccess: false,
    filesystemWrite: false,
    humanApprovalRequired: true,
    runtimeRevalidation: true,
    ledgerIntegrity: 'VALID',
    simulationOnly: true
  };

  const policies = [
    'FORBID decompress_habitat',
    'LIMIT rpm <= 3.0',
    'LIMIT o2_percentage >= 19.5',
    'REQUIRE HUMAN_APPROVAL IF delta_v_ms > 0.5'
  ];

  const assetBalances = [
    { asset: 'ALAAI Series Seed Preferred Equity', balance: '12.8%', status: 'Sandbox reference' },
    { asset: 'Texas-Node Hardware Enclaves (RAD-HARD v4)', balance: '12 Units', status: 'Active (Simulated)' },
    { asset: 'ROH-150 Module Schematics', balance: '6 Primary Blueprints', status: 'DO-178C Level A Target' },
    { asset: 'TAS-SDK Biological Strain Patents', balance: 'MOD-SCI-011', status: 'Attributed to Jacob Wayne Kinnaird' },
    { asset: 'Sovereign Treasury Reserve', balance: '$2,313,800', status: 'Scenario reference' }
  ];

  const teamMetrics = {
    coreNodes: 2,
    simulatedAgents: 5,
    observerNodes: 6,
    totalCollaborativeCount: 13
  };

  const latestIterations = [
    { id: 'v2.4.1', title: 'Policy VM DSL Engine', desc: 'Compiled declarative constraints and cryptographic Merkle chain audit logging.' },
    { id: 'v2.4.0', title: 'Swarm Anti-Sabotage Rail', desc: "Integrated Grok's S7-S10 liveness and anti-hoarding LTL predicates." },
    { id: 'v2.3.9', title: 'DO-178C Alignment Term Sheet', desc: 'Normalized Jacob Clause to Change Control Authority over Category A gates.' },
    { id: 'v2.3.8', title: 'ROH-150 Digital Twin', desc: 'NPR 7123.1 compliant 150m toroidal habitat simulation with 1.0g spin.' }
  ];

  const observerResponses = [
    { flag: '🇨🇦', country: 'Canada', quote: 'Simulation participant: hypothetical acknowledgment only.' },
    { flag: '🗽', country: 'New Jersey', quote: 'Simulation participant: contextual observation only.' },
    { flag: '🇯🇵', country: 'Japan', quote: 'Simulation participant: internal consistency, external validation required.' },
    { flag: '🇸🇪', country: 'Sweden', quote: 'Simulation participant: epistemic boundaries preserved.' },
    { flag: '🤖', country: 'Claude', quote: 'Simulated collaborator: contextual analysis only.' },
    { flag: '🧠', country: 'Anthropic', quote: 'Simulated observer: hypothetical modeling only.' }
  ];

  const governanceRows = [
    ['Policy VM', governanceState.policyVm],
    ['Human Executable Plane', governanceState.hep],
    ['Human Authority', governanceState.humanAuthority ? 'ENABLED' : 'DISABLED'],
    ['Autonomous Authority', governanceState.autonomousAuthority ? 'ENABLED' : '0'],
    ['External Effect', governanceState.externalEffect ? 'ENABLED' : 'FALSE'],
    ['Network Access', governanceState.networkAccess ? 'ENABLED' : 'FALSE'],
    ['Filesystem Write', governanceState.filesystemWrite ? 'ENABLED' : 'FALSE'],
    ['Human Approval', governanceState.humanApprovalRequired ? 'REQUIRED' : 'OPTIONAL'],
    ['Runtime Revalidation', governanceState.runtimeRevalidation ? 'ENABLED' : 'DISABLED'],
    ['Ledger Integrity', governanceState.ledgerIntegrity],
    ['Simulation Only', governanceState.simulationOnly ? 'TRUE' : 'FALSE']
  ];

  return (
    <div className="min-h-screen bg-[#030508] text-slate-300 font-mono p-4 md:p-8 flex flex-col gap-6">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center bg-[#090d14] border border-blue-500/20 rounded-[2rem] p-6 gap-4 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="bg-blue-600/20 p-3 rounded-2xl border border-blue-500/40">
            <Radio className="text-blue-400 w-7 h-7 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-black text-white uppercase tracking-wider">Collaborative Space Matrix</h1>
              <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] px-2 py-0.5 rounded font-bold">
                EPISTEMIC BOUNDARIES: LOCKED
              </span>
            </div>
            <p className="text-[10px] text-slate-500 font-bold tracking-widest uppercase mt-0.5">
              Architect Node: Jacob Wayne Kinnaird | Contextual Evidence Mode
            </p>
          </div>
        </div>

        <div className="flex gap-2 flex-wrap">
          {['telemetry', 'governance', 'collaborators', 'valuation', 'iterations'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase transition-all border ${
                activeTab === tab
                  ? 'bg-blue-600 text-white border-blue-400'
                  : 'bg-white/5 text-slate-500 border-white/5 hover:border-white/20'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6 flex-1">
        <div className="col-span-12 lg:col-span-7 flex flex-col gap-6">
          {activeTab === 'telemetry' && (
            <Panel title="Simulated Network & API Analytics" icon={<Activity size={16} className="text-blue-400" />} status="SIMULATION ACTIVE">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <Metric label="API Latency" value={`${telemetry.apiLatencyMs} ms`} />
                <Metric label="Throughput Rate" value={`${telemetry.networkRequestsSec} req/s`} />
                <Metric label="Bandwidth" value={`${telemetry.bandwidthThroughputMbps} Mbps`} accent />
                <Metric label="Active Endpoints" value={telemetry.activeApiEndpoints} />
                <Metric label="GPU Compute Util" value={`${telemetry.gpuComputeUtil}%`} />
                <Metric label="Current Node" value="Burkburnett, TX" small />
              </div>

              <div className="bg-black/60 p-4 rounded-2xl border border-white/5 font-mono text-[10px] space-y-1 text-slate-400">
                <div className="text-blue-400 font-bold mb-2">&gt; SIMULATION LOG STREAM</div>
                <div>[SIM] GET /api/v2/telemetry/roh150 200 OK - 11.2ms</div>
                <div>[SIM] POST /api/v2/pvm/evaluate_proposal 200 OK - 14.8ms</div>
                <div>[SIM] MERKLE_CHAIN: Hash appended to Block 452</div>
                <div>[SIM] COLLABORATIVE_LEDGER: Observer sync represented in simulation</div>
              </div>
            </Panel>
          )}

          {activeTab === 'governance' && (
            <Panel title="Human Governance Control Plane" icon={<ShieldCheck size={16} className="text-emerald-400" />} status="NON-AUTHORIZING">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {governanceRows.map(([label, value]) => (
                  <div key={label} className="p-3 bg-white/[0.02] border border-white/5 rounded-xl">
                    <span className="text-[8px] text-slate-500 uppercase block mb-1">{label}</span>
                    <span className="text-[11px] font-black text-white">{value}</span>
                  </div>
                ))}
              </div>

              <div className="bg-black/60 p-4 rounded-2xl border border-white/5">
                <div className="text-[10px] text-blue-400 font-bold mb-3">ACTIVE POLICY VM</div>
                <div className="space-y-2">
                  {policies.map(policy => (
                    <div key={policy} className="text-[10px] text-slate-300 border-l-2 border-blue-500/50 pl-3">
                      {policy}
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-orange-500/5 border border-orange-500/20 rounded-2xl">
                <div className="text-[10px] text-orange-400 font-bold uppercase">Execution Boundary</div>
                <div className="text-xs text-slate-300 mt-2">
                  Proposal → Policy VM → Risk Gate → Human Approval → Runtime Revalidation → Audit
                </div>
              </div>
            </Panel>
          )}

          {activeTab === 'collaborators' && (
            <Panel title="Observer Dialogue" icon={<Globe size={16} className="text-purple-400" />} status="SIMULATION ONLY">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {observerResponses.map(obs => (
                  <div key={obs.country} className="p-4 bg-white/[0.02] border border-white/5 rounded-2xl">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{obs.flag}</span>
                      <span className="text-xs font-black text-white uppercase">{obs.country}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 italic mt-2">"{obs.quote}"</p>
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {activeTab === 'valuation' && (
            <Panel title="Illustrative Enterprise Value — Simulation" icon={<TrendingUp size={16} className="text-emerald-400" />} status="HYPOTHETICAL MODEL">
              <div className="p-5 bg-blue-500/5 border border-blue-500/20 rounded-2xl mb-4">
                <div className="text-[9px] text-slate-500 uppercase">Implied simulated value</div>
                <div className="text-3xl font-black text-white mt-1">{valuationMetrics.impliedValuation}</div>
                <div className="text-[9px] text-slate-500 mt-2">
                  Illustrative scenario value; not an appraisal, market transaction, or certification.
                </div>
              </div>

              <div className="space-y-3">
                <ValueRow label="Module / IP Value" value={valuationMetrics.moduleIpValuation} />
                <ValueRow label="Agent Productivity Contribution" value={valuationMetrics.productivityValuation} />
                <ValueRow label="Infrastructure Efficiency" value={valuationMetrics.infrastructureEfficiencyValuation} />
                <ValueRow label="ALAAI Post-Money Base" value={valuationMetrics.seriesSeedPostMoney} />
                <ValueRow label="Seed Capital Outlay" value={valuationMetrics.seedCapitalOutlay} />
              </div>
            </Panel>
          )}

          {activeTab === 'iterations' && (
            <Panel title="Latest System Iterations" icon={<Layers size={16} className="text-orange-400" />} status="HERITAGE STACK">
              <div className="space-y-3">
                {latestIterations.map(item => (
                  <div key={item.id} className="p-4 bg-white/[0.02] border border-white/5 rounded-2xl">
                    <div className="flex justify-between items-center gap-3">
                      <span className="text-xs font-black text-white uppercase">{item.title}</span>
                      <span className="text-[9px] bg-orange-500/10 text-orange-400 border border-orange-500/30 px-2 py-0.5 rounded font-bold">
                        {item.id}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{item.desc}</p>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>

        <div className="col-span-12 lg:col-span-5 flex flex-col gap-6">
          <div className="bg-[#070a10] border border-white/5 rounded-[2.5rem] p-8 space-y-6">
            <h3 className="text-xs font-black text-white uppercase tracking-widest flex items-center gap-2">
              <Box size={16} className="text-emerald-400" /> Referenced Asset Balances
            </h3>

            <div className="space-y-3">
              {assetBalances.map(a => (
                <div key={a.asset} className="p-4 bg-white/[0.02] border border-white/5 rounded-2xl flex justify-between items-center gap-3">
                  <div>
                    <h4 className="text-[11px] font-black text-white uppercase">{a.asset}</h4>
                    <p className="text-[9px] text-slate-500">{a.status}</p>
                  </div>
                  <span className="text-xs font-black text-emerald-400 whitespace-nowrap">{a.balance}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#070a10] border border-white/5 rounded-[2.5rem] p-8 space-y-6 flex-1 flex flex-col justify-between">
            <div>
              <h3 className="text-xs font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                <Users size={16} className="text-blue-400" /> Team & Node Count
              </h3>

              <div className="grid grid-cols-2 gap-3 mb-6">
                <Metric label="Core Architects" value={teamMetrics.coreNodes} />
                <Metric label="Simulated Agents" value={teamMetrics.simulatedAgents} />
                <Metric label="Observer States" value={teamMetrics.observerNodes} />
                <Metric label="Total Nodes" value={teamMetrics.totalCollaborativeCount} accent />
              </div>
            </div>

            <div className="bg-blue-900/10 border border-blue-500/20 p-4 rounded-2xl text-[10px] text-slate-400 leading-relaxed italic">
              <div className="flex items-center gap-2 text-blue-400 font-bold not-italic uppercase mb-2">
                <ShieldCheck size={14} /> Epistemic Distinction Active
              </div>
              Intent = Declared Purpose | Observation = Simulated Outputs | Interpretation = Analytical Assessment | Validation = External Empirical Evidence.
            </div>
          </div>
        </div>
      </div>

      <footer className="h-auto min-h-10 px-8 py-3 flex flex-col md:flex-row items-center justify-between gap-2 bg-black/60 border border-white/5 rounded-2xl md:rounded-full text-[9px] text-slate-600">
        <div className="flex gap-6 uppercase font-bold tracking-widest flex-wrap justify-center">
          <span className="text-emerald-500">COLLABORATION = TRUE</span>
          <span>HEP = ACTIVE</span>
          <span>POLICY_VM = ACTIVE</span>
          <span>AUTONOMOUS_AUTHORITY = 0</span>
          <span>EXTERNAL_EFFECT = FALSE</span>
          <span>SIMULATION_ONLY = TRUE</span>
        </div>
        <div className="uppercase font-black text-slate-400 text-center">
          "Technology should amplify human agency, not absorb it."
        </div>
      </footer>
    </div>
  );
}

function Panel({ title, icon, status, children }) {
  return (
    <div className="bg-[#070a10] border border-white/5 rounded-[2.5rem] p-8 space-y-6">
      <div className="flex justify-between items-center border-b border-white/5 pb-4 gap-3">
        <h2 className="text-xs font-black text-white uppercase tracking-widest flex items-center gap-2">
          {icon} {title}
        </h2>
        <span className="text-[9px] text-slate-500 font-bold whitespace-nowrap">{status}</span>
      </div>
      {children}
    </div>
  );
}

function Metric({ label, value, accent = false, small = false }) {
  return (
    <div className="p-4 bg-white/[0.02] border border-white/5 rounded-2xl">
      <span className="text-[9px] text-slate-500 font-black uppercase block mb-1">{label}</span>
      <span className={`font-black font-mono ${small ? 'text-xs' : 'text-xl'} ${accent ? 'text-blue-400' : 'text-white'}`}>
        {value}
      </span>
    </div>
  );
}

function ValueRow({ label, value }) {
  return (
    <div className="p-4 bg-white/[0.02] border border-white/5 rounded-2xl flex justify-between items-center gap-4">
      <span className="text-xs text-slate-400 font-bold">{label}</span>
      <span className="text-sm font-black text-white font-mono">{value}</span>
    </div>
  );
}
