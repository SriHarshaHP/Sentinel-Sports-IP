"use client";

import { useState, useEffect } from "react";
import { Upload, CheckCircle2, ShieldCheck, Loader2, Download, Activity, Search, Filter, History, Settings, Lock } from "lucide-react";

interface VaultResult {
  status: string;
  video_id: string;
  protected_video_url: string;
  hashes_stored: number;
}

interface ProtectedVideo {
  id: string;
  title: string;
  keywords: string;
  protected_url: string;
}

interface VaultPanelProps {
  onDeployDrone: (keyword: string) => void;
  user: any;
}

export default function VaultPanel({ onDeployDrone, user }: VaultPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [keywords, setKeywords] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<VaultResult | null>(null);
  const [protectedMedia, setProtectedMedia] = useState<ProtectedVideo[]>([]);

  useEffect(() => {
    if (user) fetchMedia();
  }, [user]);

  const fetchMedia = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/vault/list?user_id=${user?.uid}`);
      const data = await res.json();
      setProtectedMedia(data.videos || []);
    } catch (err) {
      console.error("Error fetching media:", err);
    }
  };

  const handleProtect = async () => {
    if (!file || !user) return;
    setIsUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    formData.append("keywords", keywords);
    formData.append("user_id", user.uid);

    try {
      const res = await fetch("http://localhost:8000/api/vault/protect", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResult(data);
      fetchMedia();
    } catch (err) {
      console.error(err);
      alert("Error protecting video");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-500 overflow-y-auto pr-2">


      {/* Central Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        
        {/* File Upload & Secured Evidence Environment */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="bg-slate-900/40 backdrop-blur-md border border-slate-700/50 relative overflow-hidden h-auto min-h-[450px] flex flex-col p-8 group">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(6,182,212,0.05),transparent)] pointer-events-none"></div>
            
            <div className="flex items-center justify-between mb-8 z-10 relative">
              <h2 className="text-[1.5rem] leading-[1.3] tracking-[-0.05em] font-bold text-white uppercase flex items-center gap-3">
                <ShieldCheck className="text-cyan-500 w-6 h-6" />
                Secured Evidence Environment
              </h2>
              <div className="flex gap-2">
                <button className="bg-slate-950/60 border border-slate-700/50 p-2 hover:bg-slate-800 transition-colors">
                  <History className="text-slate-300 w-4 h-4" />
                </button>
                <button className="bg-slate-950/60 border border-slate-700/50 p-2 hover:bg-slate-800 transition-colors">
                  <Settings className="text-slate-300 w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-800 group-hover:border-cyan-500/50 transition-all duration-500 bg-slate-950/20 z-10 relative p-6">
              {!file && !result && (
                <>
                  <Upload className="w-16 h-16 text-slate-800 group-hover:text-cyan-500 group-hover:scale-110 transition-all duration-500 mb-4" />
                  <div className="text-center">
                    <p className="text-[1.5rem] leading-[1.3] tracking-[-0.05em] font-bold text-slate-400 mb-2">Ingest Forensic Artifacts</p>
                    <p className="text-[10px] font-bold text-slate-600 uppercase tracking-[0.2em]">Select secured media</p>
                    <label className="mt-6 bg-red-600 px-8 py-3 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-red-400 transition-all shadow-[0_0_15px_rgba(239,68,68,0.2)] cursor-pointer inline-block">
                      Select Payload
                      <input 
                        type="file" 
                        accept="video/*" 
                        className="hidden" 
                        onChange={(e) => e.target.files && setFile(e.target.files[0])} 
                      />
                    </label>
                  </div>
                </>
              )}

              {file && !result && (
                <div className="w-full max-w-md animate-in fade-in duration-300">
                  <div className="p-4 rounded bg-slate-900 border border-slate-800 flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                      <Download className="w-4 h-4 text-cyan-400 rotate-180" />
                      <span className="text-sm truncate text-slate-300 font-mono">{file.name}</span>
                    </div>
                    <span className="text-xs text-slate-500 font-mono">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  
                  <div className="space-y-4 mb-6">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Asset Title</label>
                      <input 
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g. Asset_Hash_X92"
                        className="w-full bg-slate-950 border border-slate-700 px-4 py-2 text-sm text-white focus:border-cyan-500 outline-none transition-all font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Search Keywords</label>
                      <input 
                        type="text"
                        value={keywords}
                        onChange={(e) => setKeywords(e.target.value)}
                        placeholder="sports, cricket"
                        className="w-full bg-slate-950 border border-slate-700 px-4 py-2 text-sm text-white focus:border-cyan-500 outline-none transition-all font-mono"
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleProtect}
                    disabled={isUploading || !title}
                    className="w-full flex items-center justify-center gap-2 py-3 px-6 text-[10px] font-bold uppercase tracking-widest text-slate-950 bg-cyan-500 hover:bg-cyan-400 transition-colors disabled:opacity-50 shadow-[0_0_15px_rgba(6,182,212,0.2)]"
                  >
                    {isUploading ? <Loader2 className="animate-spin w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                    {isUploading ? "Applying Sentinel DNA..." : "Protect & Index Media"}
                  </button>
                  <div className="text-center mt-4">
                    <button onClick={() => setFile(null)} className="text-[10px] text-slate-500 hover:text-slate-300 uppercase tracking-widest font-bold">Cancel Operation</button>
                  </div>
                </div>
              )}

              {result && (
                <div className="flex flex-col items-center w-full animate-in zoom-in-95 duration-500">
                  <div className="p-4 rounded-full bg-green-500/20 text-green-400 mb-4 ring-4 ring-green-500/10">
                    <CheckCircle2 className="w-10 h-10" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-6 uppercase tracking-widest">Asset Secured</h3>
                  
                  <div className="w-full max-w-sm space-y-2 mb-6">
                    <div className="flex justify-between items-center p-3 bg-slate-900/50 border border-slate-800">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Sentinel DNA</span>
                      <span className="text-xs text-cyan-400 font-mono">ENCRYPTED</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-slate-900/50 border border-slate-800">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Fingerprints</span>
                      <span className="text-xs text-purple-400 font-mono">{result.hashes_stored} Vectors</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-3 w-full max-w-sm">
                    <a 
                      href={result.protected_video_url} 
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-center gap-2 py-3 px-6 text-[10px] font-bold uppercase tracking-widest text-slate-950 bg-green-500 hover:bg-green-400 transition-colors shadow-[0_0_15px_rgba(34,197,94,0.2)]"
                    >
                      <Download className="w-4 h-4" />
                      Get Protected Master
                    </a>
                    <button
                      onClick={() => { setFile(null); setResult(null); setTitle(""); setKeywords(""); }}
                      className="py-3 text-[10px] font-bold uppercase tracking-widest text-slate-300 border border-slate-700 hover:bg-slate-800 transition-colors"
                    >
                      Protect Another
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-between items-center px-2 z-10 relative">
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Hashing: ON</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Metadata Extraction</span>
                </div>
              </div>
              <span className="font-mono text-[10px] text-slate-600 uppercase">Compliance Protocol v4.2.1</span>
            </div>
          </div>
        </div>

        {/* Protected Media Inventory */}
        <div className="lg:col-span-1">
          <div className="bg-slate-900/40 backdrop-blur-md border border-slate-700/50 h-full flex flex-col min-h-[450px]">
            <div className="p-6 border-b border-slate-800/50 flex justify-between items-center">
              <h3 className="text-[10px] font-bold text-white uppercase tracking-widest">Media Inventory</h3>
              <Filter className="text-slate-500 w-4 h-4" />
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
              {!protectedMedia || protectedMedia.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center opacity-30 text-slate-500 pb-10">
                  <ShieldCheck className="w-10 h-10 mb-2" />
                  <p className="text-xs uppercase tracking-widest font-bold">No assets yet</p>
                </div>
              ) : (
                protectedMedia.map((media) => (
                  <div key={media.id} className="bg-slate-900/40 p-3 border border-slate-800 hover:border-cyan-500/50 transition-colors group">
                    <div className="flex gap-4">
                      <div className="w-16 h-16 bg-slate-950 border border-slate-800 flex items-center justify-center flex-shrink-0">
                         <ShieldCheck className="w-8 h-8 text-cyan-500/50 group-hover:text-cyan-500 transition-colors" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-mono text-white truncate uppercase">{media.title}</div>
                        <div className="text-[10px] font-bold text-slate-500 mt-1 uppercase tracking-widest">ID: {media.id.split('-')[0]}</div>
                        <div className="flex justify-between mt-2 items-center gap-2">
                          <span className="text-[9px] px-1.5 py-0.5 bg-cyan-500/10 text-cyan-500 font-bold uppercase tracking-widest">Secured</span>
                          <a 
                            href={media.protected_url} 
                            target="_blank" 
                            rel="noreferrer"
                            className="text-slate-500 hover:text-cyan-400"
                            title="Download"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => onDeployDrone(media.keywords.split(',').slice(0, 2).join(' '))}
                      className="w-full mt-3 flex items-center justify-center gap-2 py-2 border border-slate-700 bg-slate-900 hover:bg-blue-600/20 hover:border-blue-500/50 hover:text-blue-400 transition-all text-[9px] font-bold uppercase tracking-widest text-slate-400 group-hover:shadow-[0_0_10px_rgba(59,130,246,0.1)]"
                    >
                      <Activity className="w-3 h-3" />
                      Deploy Sentinel Drone
                    </button>
                  </div>
                ))
              )}
            </div>

          </div>
        </div>
      </div>


    </div>
  );
}
