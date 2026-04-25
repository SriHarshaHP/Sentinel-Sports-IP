"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle, Search, Eye, Activity } from "lucide-react";

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

export default function SentinelPanel() {
  const [keyword, setKeyword] = useState("");
  const [platform, setPlatform] = useState("youtube");
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeResults, setScrapeResults] = useState<ScrapeResult[]>([]);

  const handleScrape = async () => {
    if (!keyword) return;
    setIsScraping(true);
    setScrapeResults([]);

    try {
      const res = await fetch("http://localhost:8000/api/sentinel/scrape_and_check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword, platform }),
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

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-500">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
            <Activity className="text-blue-400" />
            Sentinel Drone (Live Monitoring)
          </h2>
          <p className="text-slate-400 mt-2 max-w-xl">
            Query YouTube using preset keywords. The system fetches live clips, downloads them, and runs our Fast Check (pHash) and Deep Check (Watermark) algorithms to detect IP infringement in real-time.
          </p>
        </div>
        <div className="flex bg-slate-900 border border-slate-700 rounded-lg overflow-hidden shrink-0 mt-4 md:mt-0">
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="bg-transparent px-3 py-2 text-sm text-slate-300 border-r border-slate-700 outline-none focus:bg-slate-800"
            >
              <option value="youtube" className="bg-slate-900">YouTube</option>
              <option value="tiktok" className="bg-slate-900">TikTok</option>
              <option value="instagram" className="bg-slate-900">Instagram</option>
            </select>
            <input 
              type="text" 

              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="bg-transparent px-4 py-2 text-sm text-slate-300 outline-none w-48 focus:border-blue-500"
              placeholder="e.g. NBA finals"
            />
            <button
              onClick={handleScrape}
              disabled={isScraping}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors disabled:opacity-50"
            >
              {isScraping ? <Eye className="animate-pulse w-4 h-4" /> : <Search className="w-4 h-4" />}
              {isScraping ? "Deploying..." : "Run Drone"}
            </button>
        </div>
      </div>

      <div className="flex-1 rounded-xl bg-slate-800/20 border border-slate-700/50 p-6 overflow-y-auto">
        
        {!isScraping && scrapeResults.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center opacity-50 text-slate-400 cursor-not-allowed min-h-[300px]">
            <Activity className="w-16 h-16 mb-4" />
            <p>Awaiting Sentinel Deployment</p>
          </div>
        )}

        {isScraping && (
          <div className="h-full flex flex-col items-center justify-center text-blue-400 min-h-[300px]">
            <div className="relative mb-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-20"></span>
              <Eye className="w-12 h-12 relative animate-pulse" />
            </div>
            <p className="font-medium">Scraping YouTube & Computing Hashes...</p>
            <p className="text-xs text-slate-500 mt-2">This may take a moment resolving video downloads.</p>
          </div>
        )}

        {!isScraping && scrapeResults.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Risk Map Results</h3>
            
            {scrapeResults.map((result, idx) => (
              <div key={idx} className={`p-5 rounded-lg border ${result.is_pirated ? 'bg-red-500/10 border-red-500/30' : 'bg-slate-800/60 border-slate-700'}`}>
                {result.error ? (
                  <div className="text-red-400 text-sm">Error processing {result.video?.title}: {result.error}</div>
                ) : (
                  <div className="flex flex-col md:flex-row gap-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {result.is_pirated ? (
                           <AlertTriangle className="w-5 h-5 text-red-500" />
                        ) : (
                           <CheckCircle className="w-5 h-5 text-green-500" />
                        )}
                        <h4 className="text-white font-medium line-clamp-1">{result.video.title}</h4>
                      </div>
                      <a href={result.video.url} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline">{result.video.url}</a>
                    </div>

                    <div className="flex flex-row md:flex-col gap-4 text-sm shrink-0">
                      <div className="bg-slate-900/80 px-3 py-2 rounded border border-slate-700/50 flex flex-col">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider">Fast Check</span>
                        {result.match_found_in_db ? (
                          <div className="flex flex-col">
                            <span className="text-red-400 font-semibold mt-0.5 whitespace-nowrap">Match Found</span>
                            <span className="text-[10px] text-orange-400">{result.similarity_score}% Similar</span>
                          </div>
                        ) : (
                          <span className="text-slate-300 mt-0.5">No Matches</span>
                        )}
                      </div>
                      <div className="bg-slate-900/80 px-3 py-2 rounded border border-slate-700/50 flex flex-col">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider">Deep Check</span>
                        {result.deep_check_match ? (
                          <div className="flex flex-col">
                            <span className="text-red-400 font-semibold mt-0.5">
                              {result.detected_watermark ? "Watermark Hit" : "Visual Match"}
                            </span>
                            {result.detected_watermark && <span className="text-[10px] text-red-300 font-mono">{result.detected_watermark}</span>}
                          </div>
                        ) : (
                          <span className="text-slate-300 mt-0.5">Clean</span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
