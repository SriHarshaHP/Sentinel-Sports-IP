"use client";

import { useState, useEffect } from "react";
import { auth } from "@/lib/firebase";
import { onAuthStateChanged, signOut, User } from "firebase/auth";
import VaultPanel from "@/components/VaultPanel";
import SentinelPanel from "@/components/SentinelPanel";
import RiskMapPanel from "@/components/RiskMapPanel";
import LoginPage from "@/components/LoginPage";
import { Shield, Activity, Lock, Search, LogOut } from "lucide-react";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"vault" | "sentinel" | "enforcement">("vault");
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [prefillKeyword, setPrefillKeyword] = useState("");

  const handleDeployDrone = (keyword: string) => {
    setPrefillKeyword(keyword);
    setActiveTab("sentinel");
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const handleLogout = async () => {
    await signOut(auth);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <Shield className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-slate-500 font-medium tracking-widest uppercase">Sentinel Initializing...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans selection:bg-red-500/30">
      {/* Background Glow */}
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-red-900/10 via-slate-950 to-slate-950"></div>
      
      {/* Navbar */}
      <nav className="relative z-10 border-b border-slate-800 bg-slate-950/50 backdrop-blur-md">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 text-red-500">
            <Shield className="w-6 h-6" />
            <h1 className="text-xl font-black tracking-tighter uppercase">Sentinel <span className="text-white">Sports IP</span></h1>
          </div>
          <div className="flex items-center gap-6">
            <div className="hidden md:flex flex-col items-end">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Authorized Operator</span>
              <span className="text-xs text-cyan-500/80 font-mono">{user.email}</span>
            </div>
            <button 
              onClick={handleLogout}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-red-500/50 hover:text-red-400 transition-all"
              title="Secure Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
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
                Risk Map
              </button>
            </div>
          </aside>

          {/* Content Area */}
          <section className="flex-1">
            <div className="rounded-2xl bg-slate-900/40 border border-slate-800/80 shadow-2xl backdrop-blur-xl p-8 min-h-[600px]">
              {activeTab === "vault" && <VaultPanel onDeployDrone={handleDeployDrone} user={user} />}
              {activeTab === "sentinel" && <SentinelPanel prefillKeyword={prefillKeyword} onClearPrefill={() => setPrefillKeyword("")} user={user} />}
              {activeTab === "enforcement" && <RiskMapPanel user={user} />}
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}

