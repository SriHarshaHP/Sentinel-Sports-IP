"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, CheckCircle, Search, Eye, Activity, Lock, Terminal, Wifi, Ban, Cpu, Video, ArrowRight } from "lucide-react";

interface ScrapeResult {
  video: { title: string; url: string };
  is_pirated?: boolean;
  match_found_in_db?: boolean;
  matched_video_id?: string;
  detected_watermark?: string;
  deep_check_match?: boolean;
  deep_matched_id?: string;
  similarity_score?: number;
  error?: string;
}

interface SentinelPanelProps {
  prefillKeyword?: string;
  onClearPrefill?: () => void;
  user: any;
}

export default function SentinelPanel({ prefillKeyword, onClearPrefill, user }: SentinelPanelProps) {
  const [keyword, setKeyword] = useState("");
  const [platform, setPlatform] = useState<"youtube" | "tiktok" | "instagram">("youtube");
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeResults, setScrapeResults] = useState<ScrapeResult[]>([]);
  const [vaultCount, setVaultCount] = useState<number | null>(null);

  useEffect(() => {
    if (user) fetchVaultCount();
  }, [user]);

  const fetchVaultCount = async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiBase}/api/vault/count?user_id=${user?.uid}`);
      const data = await res.json();
      setVaultCount(data.count);
    } catch (err) {
      console.error(err);
    }
  };

  const handleScrape = async (overrideKeyword?: string) => {
    const finalKeyword = (typeof overrideKeyword === 'string') ? overrideKeyword : keyword;
    if (!finalKeyword || vaultCount === 0) return;
    
    setIsScraping(true);
    setScrapeResults([]);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiBase}/api/sentinel/scrape_and_check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword: finalKeyword, platform, user_id: user.uid }),
      });
      const data = await res.json();
      if (data.results) {
        setScrapeResults(data.results);
      }
    } catch (err) {
      console.error(err);
      alert("Error running sentinel drone");
    } finally {
      setIsScraping(false);
    }
  };

  useEffect(() => {
    if (prefillKeyword && vaultCount !== null && vaultCount > 0) {
      setKeyword(prefillKeyword);
      const timer = setTimeout(() => {
        handleScrape(prefillKeyword);
        onClearPrefill?.();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [prefillKeyword, vaultCount]);

  if (vaultCount === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-500 min-h-[300px] text-center bg-slate-900/40 backdrop-blur-md border border-slate-700/50 rounded-lg">
        <Lock className="w-16 h-16 mb-4 opacity-20" />
        <h3 className="text-white font-medium mb-1">Drone Systems Locked</h3>
        <p className="text-sm max-w-xs">The Sentinel requires reference media to identify piracy. Please upload your first asset to the <span className="text-blue-400">IP Vault</span> to activate live monitoring.</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col gap-6 animate-in fade-in duration-500 overflow-y-auto pr-2 custom-scrollbar">
      
      {/* Search Input Row */}
      <div className="flex flex-col xl:flex-row justify-between items-center gap-4 bg-slate-900/40 backdrop-blur-md border border-slate-700/50 p-4 rounded-lg">
        <div className="flex items-center gap-2">
          <Activity className="text-blue-500 w-5 h-5" />
          <span className="font-bold uppercase tracking-widest text-white text-sm">Active Scan Command</span>
        </div>
        <div className="flex bg-slate-950 border border-slate-800 rounded overflow-hidden shadow-inner flex-1 max-w-xl">
          <div className="px-3 py-2 text-[10px] font-bold text-blue-500 bg-blue-500/10 border-r border-slate-800 flex items-center uppercase tracking-widest">
            YOUTUBE
          </div>
          <input 
            type="text" 
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="bg-transparent px-4 py-2 text-xs text-white outline-none flex-1 font-mono focus:bg-slate-900 transition-colors"
            placeholder="ENTER SEARCH QUERY..."
          />
          <button
            onClick={() => handleScrape()}
            disabled={isScraping}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold uppercase tracking-widest transition-colors disabled:opacity-50 border-l border-slate-800 shadow-[0_0_15px_rgba(37,99,235,0.2)]"
          >
            {isScraping ? <Eye className="animate-pulse w-3 h-3" /> : <Search className="w-3 h-3" />}
            {isScraping ? "DEPLOYING..." : "RUN DRONE"}
          </button>
        </div>
      </div>

      {/* Intercepted Signals Full View */}
      <div className="bg-slate-900/40 backdrop-blur-md rounded-lg border border-slate-700/50 flex-1 flex flex-col p-6">
        <div className="flex items-center justify-between mb-6 border-b border-slate-800/50 pb-4">
          <div className="flex items-center gap-3">
            <Wifi className="text-blue-500 w-6 h-6" />
            <h2 className="font-bold text-[1.5rem] leading-[1.3] tracking-[-0.05em] uppercase text-white">Intercepted Signals</h2>
          </div>
          {isScraping && (
             <div className="flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/30 rounded text-blue-500 text-[10px] font-bold tracking-widest uppercase">
               <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
               SCAN ACTIVE
             </div>
          )}
        </div>
        
        <div className="flex flex-col gap-4 flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4">
              {isScraping ? (
                <div className="flex flex-col items-center justify-center py-20 text-blue-500">
                  <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                  <div className="text-[10px] uppercase tracking-widest font-bold animate-pulse">Scanning Target Area...</div>
                </div>
              ) : scrapeResults.length === 0 ? (
                <div className="text-center text-slate-500 text-[10px] uppercase tracking-widest mt-10">No signals intercepted</div>
              ) : (
                scrapeResults.map((result, idx) => {
                  const isCritical = result.is_pirated || result.deep_check_match;
                  const isWarning = result.match_found_in_db && !result.deep_check_match;
                  
                  return (
                    <div key={idx} className={`p-3 rounded-lg border group transition-all ${isCritical ? 'bg-slate-900/60 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.1)]' : isWarning ? 'bg-slate-900/40 border-orange-500/30' : 'bg-slate-900/40 border-slate-800'}`}>
                      <div className="flex justify-between items-start mb-2">
                        <div className={`px-2 py-0.5 text-[9px] font-black uppercase rounded tracking-widest ${isCritical ? 'bg-red-600 text-white' : isWarning ? 'bg-orange-500 text-white' : 'bg-slate-700 text-white'}`}>
                          {isCritical ? 'THREAT: CRITICAL' : isWarning ? 'THREAT: ELEVATED' : 'THREAT: NONE'}
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">#{idx.toString().padStart(4, '0')}</span>
                      </div>
                      <div className="text-xs font-bold text-white mb-1 line-clamp-1" title={result.video.title}>{result.video.title}</div>
                      <div className={`text-xs font-mono mb-2 truncate ${isCritical ? 'text-red-400' : 'text-slate-400'}`}>
                        {result.detected_watermark ? `DNA: ${result.detected_watermark}` : 'Source: YOUTUBE'}
                      </div>
                      <div className="flex justify-between items-center text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                        <span>SIMILARITY: {result.similarity_score || 0}%</span>
                        <a href={result.video.url} target="_blank" rel="noreferrer"><ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform cursor-pointer hover:text-white" /></a>
                      </div>
                    </div>
                  );
                })
              )}
            </div>


          </div>


    </div>
  );
}
