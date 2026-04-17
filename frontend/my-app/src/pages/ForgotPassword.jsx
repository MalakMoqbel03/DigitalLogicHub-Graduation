import { useState } from "react";
import api from "../services/api";

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

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800/50 p-8 rounded-2xl border border-slate-700">
        <button onClick={onBack} className="text-slate-400 mb-4">← Back</button>

        <h2 className="text-white text-2xl font-bold mb-4">Forgot Password</h2>

        {error && <p className="text-red-400 mb-3">{error}</p>}
        {success && <p className="text-green-400 mb-3">{success}</p>}

        {step === 1 && (
          <>
            <input
              className="w-full p-3 rounded-xl bg-slate-900 text-white border border-slate-700 mb-3"
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <button className="w-full py-3 bg-blue-500 rounded-xl text-white" onClick={sendCode}>
              Send Code
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <input
              className="w-full p-3 rounded-xl bg-slate-900 text-white border border-slate-700 mb-3"
              placeholder="Enter code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            <button className="w-full py-3 bg-green-500 rounded-xl text-white" onClick={verifyCode}>
              Verify Code
            </button>
          </>
        )}

        {step === 3 && (
          <>
            <input
              className="w-full p-3 rounded-xl bg-slate-900 text-white border border-slate-700 mb-3"
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <button className="w-full py-3 bg-cyan-500 rounded-xl text-white" onClick={resetPassword}>
              Reset Password
            </button>
          </>
        )}

        {step === 4 && (
          <p className="text-slate-200">✅ You can now sign in with your new password.</p>
        )}
      </div>
    </div>
  );
}
