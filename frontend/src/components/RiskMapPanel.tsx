"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, ShieldAlert, CheckCircle, Clock, Globe, FileWarning, Search, Filter, History, Code, Image as ImageIcon } from "lucide-react";

interface Incident {
  id: string;
  video: { title: string; url: string };
  platform: string;
  is_pirated: boolean;
  match_found_in_db: boolean;
  matched_video_id: string | null;
  detected_watermark: string | null;
  deep_check_match: boolean;
  deep_matched_id: string | null;
  similarity_score: number | null;
  timestamp: string;
  status: string;
}

export default function RiskMapPanel({ user }: { user: any }) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [takingDown, setTakingDown] = useState<string | null>(null);
  const [activeNotice, setActiveNotice] = useState<string | null>(null);
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/enforcement/incidents?user_id=${user?.uid}`);
      const data = await res.json();
      if (data.incidents) {
        // Filter to only show incidents with a detected watermark or high similarity, sort newest first
        const filtered = data.incidents.filter((inc: Incident) => inc.detected_watermark || (inc.similarity_score && inc.similarity_score > 80));
        setIncidents(filtered.reverse());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const handleTakedown = async (id: string) => {
    setTakingDown(id);
    try {
      const res = await fetch("http://localhost:8000/api/enforcement/takedown", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incident_id: id }),
      });
      const data = await res.json();
      if (res.ok) {
        setIncidents((prev) =>
          prev.map((inc) => (inc.id === id ? { ...inc, status: "takedown_sent" } : inc))
        );
        if (data.dmca_notice) {
          setActiveNotice(data.dmca_notice);
          setActiveIncidentId(id);
        }
      }
    } catch (err) {
      console.error(err);
      alert("Failed to send takedown notice.");
    } finally {
      setTakingDown(null);
    }
  };

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-500 relative">
      {/* Background Risk Map Visualization (CSS patterns handled globally or via simple divs) */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(30,41,59,1)_1px,transparent_1px)]" style={{ backgroundSize: '32px 32px' }}></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(239,68,68,0.15)_0%,transparent_70%)]"></div>
        <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-red-600/10 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-red-900/10 rounded-full blur-[150px]"></div>
      </div>

      <div className="relative z-10 w-full mx-auto space-y-6 overflow-y-auto pr-2 custom-scrollbar">
        
        {/* Dashboard Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <span className="font-bold text-[10px] tracking-widest text-red-500 mb-2 block uppercase">Enforcement Protocol Alpha</span>
            <h1 className="text-[1.5rem] leading-[1.3] tracking-[-0.05em] font-bold text-white">Risk Map & Infringement Engine</h1>
          </div>

        </div>



        {/* Critical Infringements Section */}
        <div className="col-span-12">
          <div className="flex items-center justify-between mb-4 mt-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="text-red-500 w-6 h-6" />
              <h2 className="text-[1.5rem] leading-[1.3] tracking-[-0.05em] font-bold text-white uppercase">Critical Infringements</h2>
            </div>
            <div className="text-xs font-mono text-slate-500 uppercase">Sorting by Severity: Tier 1 Only</div>
          </div>

          {/* Evidence Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {loading ? (
              <div className="col-span-full h-40 flex items-center justify-center text-slate-500">Loading Intelligence...</div>
            ) : incidents.length === 0 ? (
              <div className="col-span-full h-40 flex flex-col items-center justify-center text-slate-500 opacity-50 bg-slate-900/20 border border-slate-800 rounded-lg">
                <CheckCircle className="w-12 h-12 mb-2" />
                <p className="uppercase font-bold tracking-widest text-[10px]">No critical threats detected</p>
              </div>
            ) : (
              incidents.slice(0, 6).map((incident, idx) => {
                const isSent = incident.status === "takedown_sent";
                return (
                  <div key={incident.id} className={`bg-slate-950/60 backdrop-blur-lg border overflow-hidden group transition-all duration-300 rounded-lg ${isSent ? 'border-red-500/20' : 'border-slate-800/50 hover:border-red-500/50'}`}>
                    <div className="relative h-48 bg-slate-900 overflow-hidden border-b border-slate-800">
                      <div className="absolute inset-0 bg-slate-800 flex items-center justify-center opacity-30">
                        {/* Placeholder visual if no thumbnail, we just use a tech pattern */}
                        <div className="w-full h-full bg-[url('https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000&auto=format&fit=crop')] bg-cover bg-center grayscale group-hover:grayscale-0 transition-all duration-500"></div>
                      </div>
                      
                      {isSent && (
                        <div className="absolute inset-0 flex items-center justify-center z-20">
                          <div className="bg-slate-950/90 border border-red-500 px-4 py-2 text-red-500 font-bold text-[10px] tracking-widest uppercase shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                            Takedown Sent
                          </div>
                        </div>
                      )}

                      <div className="absolute top-2 left-2 flex gap-1 z-10">
                        <span className={`text-white font-bold text-[10px] tracking-widest px-2 py-0.5 uppercase ${isSent ? 'bg-slate-800 text-slate-400' : 'bg-red-600'}`}>
                          {isSent ? 'Enforced' : 'Critical'}
                        </span>
                        {!isSent && (
                          <span className="bg-slate-900/90 text-white font-bold text-[10px] tracking-widest px-2 py-0.5 border border-slate-700 uppercase">
                            {incident.detected_watermark ? 'DNA MATCH' : 'SIMILARITY MATCH'}
                          </span>
                        )}
                      </div>
                      <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-slate-950 p-4 z-10">
                        <p className="font-mono text-xs text-red-400">ID: {incident.id.split('-')[0].toUpperCase()}</p>
                      </div>
                    </div>

                    <div className={`p-4 space-y-4 ${isSent ? 'opacity-60' : ''}`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-white uppercase mb-1 line-clamp-1" title={incident.video?.title || "Unknown"}>{incident.video?.title || "Unknown"}</h4>
                          <p className="text-xs text-slate-500">Detected on: {incident.platform || 'Unknown'}</p>
                        </div>
                        <div className="text-right shrink-0 ml-2">
                          <span className="font-bold text-[10px] tracking-widest text-slate-500 block uppercase">Status</span>
                          <span className={`font-mono text-xs ${isSent ? 'text-white' : 'text-yellow-500'}`}>{isSent ? '14:22 UTC' : 'PENDING ACTION'}</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 bg-slate-900/50 p-3 border border-slate-800 rounded">
                        <div>
                          <span className="font-bold text-[8px] tracking-widest text-slate-500 uppercase block mb-1">Proof Engine</span>
                          <div className="flex items-center gap-1 text-[10px]">
                            {incident.detected_watermark ? (
                              <><Code className="text-red-500 w-3 h-3" /><span className="font-mono text-slate-300">Fingerprint Match</span></>
                            ) : (
                              <><ImageIcon className="text-red-500 w-3 h-3" /><span className="font-mono text-slate-300">{incident.similarity_score}% Similarity</span></>
                            )}
                          </div>
                        </div>
                        <div>
                          <span className="font-bold text-[8px] tracking-widest text-slate-500 uppercase block mb-1">Severity</span>
                          <span className="font-mono text-[10px] text-red-500 font-bold tracking-widest">EXTREME</span>
                        </div>
                      </div>

                      {isSent ? (
                        <button className="w-full bg-slate-900 text-slate-500 py-2 text-[10px] font-bold uppercase tracking-widest border border-slate-800 cursor-not-allowed">
                          View Enforcement Receipt
                        </button>
                      ) : (
                        <div className="flex gap-2">
                          <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-white py-2 text-[10px] font-bold uppercase tracking-widest border border-slate-700 transition-colors">Ignore</button>
                          <button 
                            onClick={() => handleTakedown(incident.id)}
                            disabled={takingDown === incident.id}
                            className="flex-1 bg-red-600 hover:bg-red-500 text-white py-2 text-[10px] font-bold uppercase tracking-widest transition-colors shadow-[0_0_15px_rgba(239,68,68,0.2)] disabled:opacity-50 flex items-center justify-center gap-1"
                          >
                            {takingDown === incident.id ? "PROCESSING..." : "SEND TAKEDOWN"}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Forensic Data Table */}
        <div className="col-span-12 bg-slate-950/40 backdrop-blur-xl border border-slate-800/50 p-6 overflow-x-auto rounded-lg mb-8">
          <div className="flex items-center gap-2 mb-6">
            <History className="text-slate-500 w-4 h-4" />
            <h3 className="text-sm font-bold text-white uppercase tracking-widest">Forensic Activity Log</h3>
          </div>
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="text-slate-500 border-b border-slate-800">
                <th className="pb-3 font-medium uppercase tracking-widest px-2">Target Entity</th>
                <th className="pb-3 font-medium uppercase tracking-widest px-2">Detection Method</th>
                <th className="pb-3 font-medium uppercase tracking-widest px-2">Marketplace</th>
                <th className="pb-3 font-medium uppercase tracking-widest px-2">Action Status</th>
                <th className="pb-3 font-medium uppercase tracking-widest px-2 text-right">Probability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900/50">
              {incidents.slice(0, 5).map((inc, i) => (
                <tr key={i} className="hover:bg-slate-900/20 transition-colors">
                  <td className="py-4 px-2 text-white truncate max-w-[200px]">{inc.video?.title || "Unknown"}</td>
                  <td className="py-4 px-2 text-slate-400">{inc.detected_watermark ? "Watermark ID" : "Spectral Analysis"}</td>
                  <td className="py-4 px-2 text-slate-400">{inc.platform.toUpperCase()}</td>
                  <td className="py-4 px-2">
                    {inc.status === "takedown_sent" ? (
                      <span className="bg-green-500/10 text-green-500 px-2 py-0.5 rounded-full border border-green-500/20 text-[10px]">TAKEDOWN COMPLETE</span>
                    ) : (
                      <span className="bg-yellow-500/10 text-yellow-500 px-2 py-0.5 rounded-full border border-yellow-500/20 text-[10px]">REVIEW REQUIRED</span>
                    )}
                  </td>
                  <td className="py-4 px-2 text-right text-white">{inc.detected_watermark ? "0.998" : `0.${inc.similarity_score}`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* DMCA Notice Modal */}
      {activeNotice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in zoom-in duration-300">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl shadow-red-500/10">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <h3 className="text-xl font-bold text-white flex items-center gap-2 uppercase tracking-widest text-sm">
                <FileWarning className="text-red-500 w-5 h-5" />
                Legal Notice Preview
              </h3>
              <button 
                onClick={() => { setActiveNotice(null); setActiveIncidentId(null); }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="p-6 overflow-y-auto font-mono text-xs text-slate-300 bg-black/30 whitespace-pre-wrap leading-relaxed custom-scrollbar">
              {activeNotice}
            </div>
            <div className="p-6 border-t border-slate-800 flex justify-end gap-3">
              <button 
                onClick={() => window.open(`http://localhost:8000/api/enforcement/download_pdf/${activeIncidentId}`)}
                className="px-6 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold tracking-widest text-[10px] uppercase transition-all shadow-[0_0_15px_rgba(37,99,235,0.2)]"
              >
                Download Official PDF
              </button>
              <button 
                onClick={() => { setActiveNotice(null); setActiveIncidentId(null); }}
                className="px-6 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 text-white font-bold tracking-widest text-[10px] uppercase transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
