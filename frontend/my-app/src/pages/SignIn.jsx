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
  MailCheck,
} from "lucide-react";
import ThemeToggle from "../components/ThemeToggle";

/* ==================== GRID BACKGROUND ==================== */
const GridBackground = () => (
  <div className="fixed inset-0 pointer-events-none overflow-hidden">
    <div
      className="absolute inset-0 opacity-10 dark:opacity-5"
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
  onNeedVerification,
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // True when login fails specifically because the account isn't verified yet.
  const [needsVerification, setNeedsVerification] = useState(false);

  const handleLogin = async () => {
    setError("");
    setNeedsVerification(false);
    setLoading(true);

    try {
      const res = await api.post("/auth/login", {
        email: email.toLowerCase(),
        password,
      });

      onSignIn(res.data.user);
    } catch (err) {
      const detail = err.response?.data?.detail || "Login failed";
      setError(detail);
      // Backend returns "Please verify your email before logging in" (401)
      // for unverified accounts — show the resend button in that case.
      if (detail.toLowerCase().includes("verify")) {
        setNeedsVerification(true);
      }
    }

    setLoading(false);
  };

  // Send a fresh verification code, then route to the verification page.
  const handleSendVerification = async () => {
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/resend", { email: email.toLowerCase() });
    } catch (err) {
      // 429 just means a code was sent very recently — still fine to proceed.
      if (err.response?.status !== 429) {
        setError(err.response?.data?.detail || "Couldn't send the verification email.");
        setLoading(false);
        return;
      }
    }
    setLoading(false);
    onNeedVerification?.(email.toLowerCase());
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100
                    dark:from-gray-900 dark:via-slate-900 dark:to-gray-900
                    flex items-center justify-center p-4 relative transition-colors">
      <GridBackground />

      {/* Floating theme toggle in the top-right corner */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      <div className="max-w-md w-full bg-white border border-gray-200 shadow-xl
                      dark:bg-slate-800/50 dark:border-slate-700 dark:shadow-none
                      p-8 rounded-2xl relative z-10 transition-colors">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 mb-4 shadow-lg shadow-blue-500/25">
            <Cpu className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Welcome Back</h1>
          <p className="text-gray-500 dark:text-slate-400 text-sm">
            Sign in to continue learning
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200
                          dark:bg-red-500/10 dark:text-red-400 dark:border-transparent
                          rounded-xl flex gap-2 items-center">
            <XCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {needsVerification && (
          <button
            onClick={handleSendVerification}
            disabled={loading}
            className="w-full mb-4 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-xl hover:from-green-400 hover:to-emerald-400 transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-green-500/25"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <MailCheck className="w-5 h-5" /> Send verification email
              </>
            )}
          </button>
        )}

        <div className="space-y-4">
          {/* Email */}
          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 text-gray-900 placeholder-gray-400
                         dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:placeholder-slate-500
                         rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors"
            />
          </div>

          {/* Password */}
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 text-gray-900 placeholder-gray-400
                         dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:placeholder-slate-500
                         rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          <p className="text-right text-sm">
            <span
              className="text-blue-600 dark:text-blue-400 cursor-pointer hover:text-blue-500 dark:hover:text-blue-300"
              onClick={onForgotPassword}
            >
              Forgot password?
            </span>
          </p>

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

        <div className="mt-6 text-center">
          <p className="text-gray-500 dark:text-slate-500 text-sm">
            Don't have an account?{" "}
            <button
              onClick={onSwitchToSignUp}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-medium"
            >
              Create one
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}