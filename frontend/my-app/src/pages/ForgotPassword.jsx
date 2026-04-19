import { useState } from "react";
import api from "../services/api";
import { ArrowLeft, Mail, KeyRound, Lock, XCircle, CheckCircle } from "lucide-react";
import ThemeToggle from "../components/ThemeToggle";

export default function ForgotPassword({ onBack }) {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const sendCode = async () => {
    setError(""); setSuccess("");
    try {
      await api.post("/auth/forgot", { email });
      setStep(2);
      setSuccess("Code sent to your email.");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send code");
    }
  };

  const verifyCode = async () => {
    setError(""); setSuccess("");
    try {
      await api.post("/auth/reset/verify", { email, code });
      setStep(3);
      setSuccess("Code verified. Please set a new password.");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid code");
    }
  };

  const resetPassword = async () => {
    setError(""); setSuccess("");
    try {
      await api.post("/auth/reset/password", {
        email,
        code,
        new_password: newPassword,
      });
      setSuccess("Password reset successful. You can sign in now.");
      setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || "Reset failed");
    }
  };

  const inputClass = "w-full p-3 pl-12 rounded-xl transition-colors " +
    "bg-gray-50 border border-gray-200 text-gray-900 placeholder-gray-400 " +
    "dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:placeholder-slate-500 " +
    "focus:outline-none focus:ring-2 focus:ring-blue-500/50";

  return (
    <div className="min-h-screen flex items-center justify-center p-4 transition-colors
                    bg-gradient-to-br from-slate-50 via-white to-slate-100
                    dark:from-gray-900 dark:via-slate-900 dark:to-gray-900">

      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      <div className="max-w-md w-full bg-white border border-gray-200 shadow-xl
                      dark:bg-slate-800/50 dark:border-slate-700 dark:shadow-none
                      p-8 rounded-2xl transition-colors">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-700
                     dark:text-slate-400 dark:hover:text-slate-200 mb-4 text-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>

        <h2 className="text-gray-900 dark:text-white text-2xl font-bold mb-4">Forgot Password</h2>

        {error && (
          <div className="mb-4 p-3 rounded-xl flex gap-2 items-center
                          bg-red-50 text-red-700 border border-red-200
                          dark:bg-red-500/10 dark:text-red-400 dark:border-transparent">
            <XCircle className="w-4 h-4" /> {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-xl flex gap-2 items-center
                          bg-green-50 text-green-700 border border-green-200
                          dark:bg-green-500/10 dark:text-green-400 dark:border-transparent">
            <CheckCircle className="w-4 h-4" /> {success}
          </div>
        )}

        {step === 1 && (
          <>
            <div className="relative mb-3">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
              <input
                className={inputClass}
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <button
              className="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 rounded-xl text-white font-semibold transition shadow-lg shadow-blue-500/25"
              onClick={sendCode}
            >
              Send Code
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <div className="relative mb-3">
              <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
              <input
                className={inputClass}
                placeholder="Enter code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
            <button
              className="w-full py-3 bg-green-500 hover:bg-green-400 rounded-xl text-white font-semibold transition shadow-lg shadow-green-500/25"
              onClick={verifyCode}
            >
              Verify Code
            </button>
          </>
        )}

        {step === 3 && (
          <>
            <div className="relative mb-3">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
              <input
                className={inputClass}
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <button
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 rounded-xl text-white font-semibold transition shadow-lg shadow-cyan-500/25"
              onClick={resetPassword}
            >
              Reset Password
            </button>
          </>
        )}

        {step === 4 && (
          <p className="text-gray-700 dark:text-slate-200">
            ✅ You can now sign in with your new password.
          </p>
        )}
      </div>
    </div>
  );
}