import React, { useMemo, useState } from "react";
import api from "../services/api";
import { Mail, XCircle, CheckCircle } from "lucide-react";
import ThemeToggle from "../components/ThemeToggle";

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
    <div className="absolute top-20 left-20 w-64 h-64 bg-blue-400/20 dark:bg-blue-500/10 rounded-full blur-3xl" />
    <div className="absolute bottom-20 right-20 w-96 h-96 bg-cyan-400/20 dark:bg-cyan-500/10 rounded-full blur-3xl" />
  </div>
);

export default function VerifyEmail({ email, onVerified, onBack }) {
  const [codeInputs, setCodeInputs] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const codeString = useMemo(() => codeInputs.join(""), [codeInputs]);
  const isComplete = codeString.length === 6 && /^\d{6}$/.test(codeString);

  const handleCodeChange = (index, value) => {
    if (!/^\d?$/.test(value)) return;
    const updated = [...codeInputs];
    updated[index] = value;
    setCodeInputs(updated);
    if (value && index < 5) {
      document.getElementById(`code-${index + 1}`)?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !codeInputs[index] && index > 0) {
      document.getElementById(`code-${index - 1}`)?.focus();
    }
  };

  const handleVerifyCode = async () => {
    setError(""); setSuccess("");
    if (!isComplete) {
      setError("Please enter the 6-digit verification code.");
      return;
    }
    setLoading(true);
    try {
      const res = await api.post("/auth/verify", {
        email: email.toLowerCase(),
        code: codeString,
      });
      setSuccess(res.data?.message || "Account verified successfully!");
      setTimeout(() => {
        // Pass the FULL user payload (which includes the JWT token) so the
        // logged-in session is authenticated. Falling back to just the email
        // would log the user in without a token, causing 403s on any
        // authenticated request (e.g. submitting the VARK quiz).
        onVerified?.(res.data?.user ?? { email: email.toLowerCase() });
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid verification code. Please try again.");
      setCodeInputs(["", "", "", "", "", ""]);
      setTimeout(() => document.getElementById("code-0")?.focus(), 50);
    }
    setLoading(false);
  };

  const handleResend = async () => {
    setError(""); setSuccess("");
    setLoading(true);
    try {
      const res = await api.post("/auth/forgot", { email: email.toLowerCase() });
      setSuccess(res.data?.message || "A new code was sent to your email.");
      setCodeInputs(["", "", "", "", "", ""]);
      setTimeout(() => document.getElementById("code-0")?.focus(), 50);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to resend code. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative transition-colors
                    bg-gradient-to-br from-slate-50 via-white to-slate-100
                    dark:from-gray-900 dark:via-slate-900 dark:to-gray-900">
      <GridBackground />

      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 mb-4 shadow-lg shadow-green-500/25">
            <Mail className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Verify Your Email
          </h1>
          <p className="text-gray-500 dark:text-slate-400">We sent a verification code to</p>
          <p className="text-blue-600 dark:text-blue-400 font-medium">{email}</p>
        </div>

        <div className="bg-white border border-gray-200 shadow-xl
                        dark:bg-slate-800/50 dark:backdrop-blur-xl dark:border-slate-700/50 dark:shadow-2xl
                        rounded-2xl p-8 transition-colors">
          {error && (
            <div className="mb-4 p-3 rounded-xl flex items-center gap-2 text-sm
                            bg-red-50 text-red-700 border border-red-200
                            dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/30">
              <XCircle className="w-4 h-4" /> {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 rounded-xl flex items-center gap-2 text-sm
                            bg-green-50 text-green-700 border border-green-200
                            dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/30">
              <CheckCircle className="w-4 h-4" /> {success}
            </div>
          )}

          <div className="mb-6">
            <label className="block text-gray-700 dark:text-slate-300 text-sm font-medium mb-4 text-center">
              Enter 6-digit code
            </label>

            <div className="flex justify-center gap-2">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <input
                  key={i}
                  id={`code-${i}`}
                  type="text"
                  maxLength={1}
                  value={codeInputs[i]}
                  onChange={(e) => handleCodeChange(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  className="w-12 h-14 text-center text-2xl font-bold rounded-xl transition-colors
                             bg-gray-50 text-gray-900 border border-gray-200
                             dark:bg-slate-900/50 dark:text-white dark:border-slate-700
                             focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
              ))}
            </div>
          </div>

          <button
            onClick={handleVerifyCode}
            disabled={loading || !isComplete}
            className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-xl hover:from-green-400 hover:to-emerald-400 transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-green-500/25"
          >
            {loading ? "Verifying..." : "Verify Account"}
          </button>

          <div className="text-center mt-4">
            <p className="text-gray-500 dark:text-slate-500 text-sm">
              Didn't receive the code?{" "}
              <button
                onClick={handleResend}
                disabled={loading}
                className="text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-medium"
              >
                Resend
              </button>
            </p>
          </div>

          <div className="mt-6 text-center">
            <button
              onClick={onBack}
              className="text-gray-500 hover:text-gray-700 dark:text-slate-500 dark:hover:text-slate-300 text-sm"
            >
              ← Back to Sign Up
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}