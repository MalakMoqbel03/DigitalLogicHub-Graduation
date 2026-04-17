import React, { useState } from "react";
import api from "../services/api";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Cpu,
  XCircle,
} from "lucide-react";

/* ==================== GRID BACKGROUND ==================== */
const GridBackground = () => (
  <div className="fixed inset-0 pointer-events-none overflow-hidden">
    <div
      className="absolute inset-0 opacity-5"
      style={{
        backgroundImage: `
          linear-gradient(rgba(59,130,246,.5) 1px, transparent 1px),
          linear-gradient(90deg, rgba(59,130,246,.5) 1px, transparent 1px)
        `,
        backgroundSize: "50px 50px",
      }}
    />
  </div>
);

/* ==================== SIGN IN ==================== */
export default function SignIn({
  onSignIn,
  onSwitchToSignUp,
  onForgotPassword,
}) {
  /* ==================== STATE ==================== */
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  /* ==================== LOGIN ==================== */
  const handleLogin = async () => {
    setError("");
    setLoading(true);

    try {
      const res = await api.post("/auth/login", {
        email: email.toLowerCase(),
        password,
      });

      onSignIn(res.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    }

    setLoading(false);
  };

  /* ==================== UI ==================== */
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4 relative">
      <GridBackground />

      <div className="max-w-md w-full bg-slate-800/50 p-8 rounded-2xl border border-slate-700 relative z-10">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 mb-4 shadow-lg shadow-blue-500/25">
            <Cpu className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Welcome Back</h1>
          <p className="text-slate-400 text-sm">
            Sign in to continue learning
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 text-red-400 rounded-xl flex gap-2 items-center">
            <XCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Form */}
        <div className="space-y-4">
          {/* Email */}
          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>

          {/* Password */}
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-12 pr-12 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Forgot Password */}
          <p className="text-right text-sm">
            <span
              className="text-blue-400 cursor-pointer hover:text-blue-300"
              onClick={onForgotPassword}
            >
              Forgot password?
            </span>
          </p>

          {/* Login Button */}
          <button
            onClick={handleLogin}
            disabled={loading || !email || !password}
            className="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:from-blue-400 hover:to-cyan-400 transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                Sign In <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-slate-500 text-sm">
            Don’t have an account?{" "}
            <button
              onClick={onSwitchToSignUp}
              className="text-blue-400 hover:text-blue-300 font-medium"
            >
              Create one
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
