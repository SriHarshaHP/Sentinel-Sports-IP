"use client";

import { useState } from "react";
import { auth } from "@/lib/firebase";
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, sendEmailVerification } from "firebase/auth";
import { Shield, Lock, Mail, ArrowRight, CheckCircle } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setVerificationSent(false);
    
    // Strict Email Regex Validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid corporate email address.");
      return;
    }

    if (password.length < 6) {
      setError("Security requirement: Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        await createUserWithEmailAndPassword(auth, email, password);
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
    } catch (err: any) {
      console.error(err.code);
      switch (err.code) {
        case "auth/invalid-email":
          setError("The email address format is invalid.");
          break;
        case "auth/email-already-in-use":
          setError("ACCOUNT ALREADY EXISTS. PLEASE SIGN IN INSTEAD.");
          break;
        case "auth/user-disabled":
          setError("This account has been disabled by an administrator.");
          break;
        case "auth/user-not-found":
          setError("No Sentinel account found with this email.");
          break;
        case "auth/wrong-password":
          setError("Incorrect password for this operator.");
          break;
        case "auth/email-already-in-use":
          setError("This email is already registered in the Sentinel database.");
          break;
        case "auth/weak-password":
          setError("Password is too weak. Use a stronger combination.");
          break;
        default:
          setError("Authentication system error. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4 font-[family-name:var(--font-geist-sans)]">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-red-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-red-500/20">
            <Shield className="text-white w-10 h-10" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter">
            SENTINEL <span className="text-red-500">SPORTS IP</span>
          </h1>
          <p className="text-slate-400 mt-1 text-center text-sm font-medium">
            Forensic Intelligence & Piracy Enforcement
          </p>
        </div>



        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-5 h-5 text-slate-500" />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-3 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-all"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 w-5 h-5 text-slate-500" />
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-3 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-all"
                required
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs animate-in fade-in zoom-in duration-300">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-red-600/10 disabled:opacity-50"
          >
            {loading ? "Authenticating..." : isRegister ? "Create Account" : "Login to Sentinel"}
            {!loading && <ArrowRight className="w-4 h-4" />}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-slate-800 text-center">
          <button 
            onClick={() => setIsRegister(!isRegister)}
            className="text-slate-400 hover:text-white text-sm transition-colors"
          >
            {isRegister ? "Already have an account? Sign in" : "New to Sentinel? Request access"}
          </button>
        </div>
      </div>
    </div>
  );
}
