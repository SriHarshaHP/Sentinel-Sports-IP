"use client";
import { useState } from "react";
import VaultPanel from "@/components/VaultPanel";
import SentinelPanel from "@/components/SentinelPanel";
import RiskMapPanel from "@/components/RiskMapPanel";
import { Shield, Activity, Lock, Search } from "lucide-react";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"vault" | "sentinel" | "enforcement">("vault");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans selection:bg-cyan-500/30">
      {/* Background Glow */}
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/20 via-slate-950 to-slate-950"></div>
      
      {/* Navbar */}
      <nav className="relative z-10 border-b border-slate-800 bg-slate-950/50 backdrop-blur-md">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 text-cyan-400">
            <Shield className="w-6 h-6" />
            <h1 className="text-xl font-bold tracking-widest uppercase">Sentinel IP</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            <span className="text-xs font-medium text-cyan-500/80 tracking-wider">SYSTEM ONLINE</span>
          </div>
        </div>
      </nav>

      {/* Main Layout */}
      <main className="relative z-10 container mx-auto px-6 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* Sidebar */}
          <aside className="w-full lg:w-64 shrink-0">
            <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800 backdrop-blur flex flex-col gap-2">
              <button
                onClick={() => setActiveTab("vault")}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                  activeTab === "vault"
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                <Lock className="w-5 h-5" />
                The Vault
              </button>
              
              <button
                onClick={() => setActiveTab("sentinel")}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                  activeTab === "sentinel"
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.15)]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                <Activity className="w-5 h-5" />
                The Sentinel
              </button>
              
              <button
                onClick={() => setActiveTab("enforcement")}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                  activeTab === "enforcement"
                    ? "bg-red-500/10 text-red-400 border border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.15)]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                <Search className="w-5 h-5" />
                Risk Map (Phase 3)
              </button>
            </div>
          </aside>

          {/* Content Area */}
          <section className="flex-1">
            <div className="rounded-2xl bg-slate-900/40 border border-slate-800/80 shadow-2xl backdrop-blur-xl p-8 min-h-[600px]">
              {activeTab === "vault" && <VaultPanel />}
              {activeTab === "sentinel" && <SentinelPanel />}
              {activeTab === "enforcement" && <RiskMapPanel />}
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}
