"use client";

import { useState } from "react";
import { Upload, Fingerprint, CheckCircle2, ShieldCheck, Loader2, Download } from "lucide-react";

interface VaultResult {
  status: string;
  video_id: string;
  protected_video_url: string;
  hashes_stored: number;
}

export default function VaultPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<VaultResult | null>(null);

  const handleProtect = async () => {
    if (!file) return;
    setIsUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/vault/protect", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Error protecting video");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-500">
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="text-cyan-400" />
          The Vault
        </h2>
        <p className="text-slate-400 mt-2">
          Upload and protect original media. The system will inject an invisible watermark and extract pHashes for our vector database.
        </p>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-700/50 rounded-xl bg-slate-800/20 p-8 transition-colors hover:border-cyan-500/50 hover:bg-slate-800/40">
        {!file && !result && (
          <label className="flex flex-col items-center cursor-pointer group">
            <div className="p-4 rounded-full bg-slate-800/80 text-cyan-400 group-hover:scale-110 group-hover:bg-cyan-500/20 transition-all">
              <Upload className="w-8 h-8" />
            </div>
            <span className="mt-4 text-sm font-medium text-slate-300">Select Video File</span>
            <span className="mt-1 text-xs text-slate-500">MP4, MOV up to 50MB</span>
            <input 
              type="file" 
              accept="video/*" 
              className="hidden" 
              onChange={(e) => e.target.files && setFile(e.target.files[0])} 
            />
          </label>
        )}

        {file && !result && (
          <div className="flex flex-col items-center w-full max-w-sm">
            <div className="w-full p-4 rounded-lg bg-slate-800/80 border border-slate-700 flex items-center justify-between mb-6">
              <span className="text-sm truncate mr-4 text-slate-300">{file.name}</span>
              <span className="text-xs text-slate-500 shrink-0">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
            <button
              onClick={handleProtect}
              disabled={isUploading}
              className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-lg font-semibold text-slate-950 bg-cyan-500 hover:bg-cyan-400 transition-colors disabled:opacity-50"
            >
              {isUploading ? <Loader2 className="animate-spin w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
              {isUploading ? "Encrypting & Hashing..." : "Protect Media"}
            </button>
            <button onClick={() => setFile(null)} className="mt-4 text-xs text-slate-500 hover:text-slate-300 underline underline-offset-4">Cancel</button>
          </div>
        )}

        {result && (
          <div className="flex flex-col items-center w-full max-w-md animate-in slide-in-from-bottom-4">
            <div className="p-4 rounded-full bg-green-500/20 text-green-400 mb-4 ring-4 ring-green-500/10">
              <CheckCircle2 className="w-12 h-12" />
            </div>
            <h3 className="text-lg font-medium text-white mb-6">Media Successfully Protected</h3>
            
            <div className="w-full space-y-3">
              <div className="flex justify-between items-center p-3 rounded bg-slate-900/50 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase tracking-wider">Status</span>
                <span className="text-sm text-green-400 font-medium">Secured</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded bg-slate-900/50 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase tracking-wider">Watermark ID</span>
                <span className="text-sm text-cyan-400 font-mono">ORG_789 (Invisible)</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded bg-slate-900/50 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase tracking-wider">Hashes Indexed</span>
                <div className="flex items-center gap-1 text-sm text-purple-400">
                  <Fingerprint className="w-4 h-4" />
                  <span>{result.hashes_stored} Frames</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4 mt-8 w-full">
              <a 
                href={result.protected_video_url} 
                download 
                target="_blank"
                rel="noreferrer"
                className="flex-1 flex items-center justify-center gap-2 py-2 px-6 rounded-lg font-semibold text-slate-950 bg-green-500 hover:bg-green-400 transition-colors"
              >
                <Download className="w-4 h-4" />
                Download Protected Video
              </a>
              <button
                onClick={() => { setFile(null); setResult(null); }}
                className="px-6 py-2 rounded-lg text-sm font-medium border border-slate-700 hover:bg-slate-800 transition-colors"
              >
                Protect Another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
