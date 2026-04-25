"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, ShieldAlert, CheckCircle, Clock, Globe, FileWarning, Search } from "lucide-react";

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

export default function RiskMapPanel() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [takingDown, setTakingDown] = useState<string | null>(null);

  const fetchIncidents = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/enforcement/incidents");
      const data = await res.json();
      if (data.incidents) {
        // Filter to only show incidents with a detected watermark, then sort newest first
        const filtered = data.incidents.filter((inc: Incident) => inc.detected_watermark);
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
      if (res.ok) {
        setIncidents((prev) =>
          prev.map((inc) => (inc.id === id ? { ...inc, status: "takedown_sent" } : inc))
        );
      }
    } catch (err) {
      console.error(err);
      alert("Failed to send takedown notice.");
    } finally {
      setTakingDown(null);
    }
  };

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-500">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
          <ShieldAlert className="text-red-400" />
          Enforcement Dashboard & Risk Map
        </h2>
        <p className="text-slate-400 mt-2 max-w-xl">
          Review detected copyright infringements from Sentinel scans. Use the Proof Engine to verify the match and initiate automated DMCA Takedown requests.
        </p>
      </div>

      <div className="flex-1 rounded-xl bg-slate-800/20 border border-slate-700/50 p-6 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-40 text-slate-400">Loading incidents...</div>
        ) : incidents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-slate-500 opacity-50">
            <CheckCircle className="w-12 h-12 mb-3" />
            <p>No infringements detected yet.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {incidents.map((incident) => (
              <div key={incident.id} className="p-5 rounded-lg border bg-slate-900/60 border-slate-700 hover:border-red-500/50 transition-colors">
                <div className="flex flex-col xl:flex-row gap-6">
                  {/* Left: Video Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                      <h4 className="text-white font-medium line-clamp-1">{incident.video?.title || "Unknown Title"}</h4>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400 mt-2 mb-3">
                      <span className="flex items-center gap-1">
                        <Globe className="w-3 h-3" /> {incident.platform || "youtube"}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {new Date(incident.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <a href={incident.video?.url} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline">
                      {incident.video?.url}
                    </a>
                  </div>

                  {/* Middle: Proof Engine */}
                  <div className="flex-1 bg-slate-950/50 p-4 rounded-lg border border-slate-800">
                    <h5 className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                      <Search className="w-3 h-3" /> Proof Engine
                    </h5>
                    <div className="space-y-2 text-sm">
                      {incident.detected_watermark ? (
                        <div className="flex justify-between items-center text-red-400">
                          <span>Invisible Watermark:</span>
                          <span className="font-mono bg-red-500/10 px-2 py-0.5 rounded">{incident.detected_watermark}</span>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center text-slate-300">
                          <span>Invisible Watermark:</span>
                          <span className="text-slate-500">Not Detected</span>
                        </div>
                      )}
                      
                      {incident.similarity_score ? (
                        <div className="flex justify-between items-center text-orange-400">
                          <span>Visual Similarity:</span>
                          <span className="font-semibold">{incident.similarity_score}%</span>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center text-slate-300">
                          <span>Visual Similarity:</span>
                          <span className="text-slate-500">N/A</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: Actions */}
                  <div className="flex flex-col items-center justify-center shrink-0 min-w-[160px] gap-2">
                    {incident.status === "takedown_sent" ? (
                      <div className="px-4 py-2 w-full text-center rounded bg-green-500/10 border border-green-500/30 text-green-400 text-sm font-medium flex items-center justify-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        Takedown Sent
                      </div>
                    ) : (
                      <button
                        onClick={() => handleTakedown(incident.id)}
                        disabled={takingDown === incident.id}
                        className="px-4 py-2 w-full rounded bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-semibold transition-colors flex items-center justify-center gap-2"
                      >
                        {takingDown === incident.id ? "Processing..." : (
                          <>
                            <FileWarning className="w-4 h-4" />
                            1-Click Takedown
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
