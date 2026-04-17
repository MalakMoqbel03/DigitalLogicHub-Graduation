import React, { useState } from "react";
import api from "../services/api";
import {
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  CheckCircle,
  XCircle,
  Cpu
} from "lucide-react";

// ==================== GRID BACKGROUND ====================
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

export default function SignUp({ onSwitchToSignIn }) {
  // ==================== STATES ====================
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Verification
  const [showVerification, setShowVerification] = useState(false);
  const [code, setCode] = useState("");
  const [userCode, setUserCode] = useState(["", "", "", "", "", ""]);

  // ==================== VALIDATION ====================
  const validatePassword = (pwd) => {
    return (
      pwd.length >= 8 &&
      pwd.length <= 15 &&
      /[A-Z]/.test(pwd) &&
      /[a-z]/.test(pwd) &&
      /[0-9]/.test(pwd)
    );
  };

  // ==================== REGISTER ====================
  const handleRegister = async () => {
    setError("");
    setSuccess("");

    if (!validatePassword(password)) {
      setError("Password must be 8–15 chars, upper, lower, number");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      await api.post("/auth/register", {
        name: name.trim(),
        email: email.toLowerCase(),
        password,
      });

      setShowVerification(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    }

    setLoading(false);
  };

  // ==================== CODE INPUT ====================
  const handleCodeInput = (index, value) => {
    if (!/^\d?$/.test(value)) return;

    const newCode = [...userCode];
    newCode[index] = value;
    setUserCode(newCode);

    if (value && index < 5) {
      document.getElementById(`code-${index + 1}`)?.focus();
    }
  };

  // ==================== VERIFY ====================
  const handleVerify = async () => {
    setError("");
    setLoading(true);

    try {
      await api.post("/auth/verify", {
        email: email.toLowerCase(),
        code: userCode.join(""),
      });

      setSuccess("Account verified successfully!");
      setTimeout(() => onSwitchToSignIn(), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid code");
      setUserCode(["", "", "", "", "", ""]);
    }

    setLoading(false);
  };

  // ==================== VERIFICATION SCREEN ====================
  if (showVerification) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4 relative">
        <GridBackground />
        <div className="max-w-md w-full bg-slate-800/50 p-8 rounded-2xl border border-slate-700">
          <div className="text-center mb-6">
            <Cpu className="mx-auto text-green-400 w-10 h-10 mb-2" />
            <h2 className="text-white text-2xl font-bold">Verify Email</h2>
            <p className="text-slate-400 text-sm">{email}</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 text-red-400 rounded-xl flex gap-2">
              <XCircle className="w-4 h-4" /> {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-500/10 text-green-400 rounded-xl flex gap-2">
              <CheckCircle className="w-4 h-4" /> {success}
            </div>
          )}

          <div className="flex justify-center gap-2 mb-6">
            {userCode.map((v, i) => (
              <input
                key={i}
                id={`code-${i}`}
                value={v}
                maxLength={1}
                onChange={(e) => handleCodeInput(i, e.target.value)}
                className="w-12 h-14 text-center text-xl bg-slate-900 text-white rounded-xl border border-slate-700"
              />
            ))}
          </div>

          <button
            onClick={handleVerify}
            disabled={loading || userCode.join("").length !== 6}
            className="w-full py-3 bg-green-500 rounded-xl text-white font-semibold"
          >
            {loading ? "Verifying..." : "Verify Account"}
          </button>
        </div>
      </div>
    );
  }

  // ==================== SIGN UP SCREEN ====================
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4 relative">
      <GridBackground />
      <div className="max-w-md w-full bg-slate-800/50 p-8 rounded-2xl border border-slate-700">
        <h2 className="text-white text-2xl font-bold mb-6 text-center">
          Create Account
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 text-red-400 rounded-xl">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <input
            placeholder="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-3 rounded-xl bg-slate-900 text-white border border-slate-700"
          />

          <input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 rounded-xl bg-slate-900 text-white border border-slate-700"
          />

          <input
            type={showPassword ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 rounded-xl bg-slate-900 text-white border border-slate-700"
          />

          <input
            type={showPassword ? "text" : "password"}
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full p-3 rounded-xl bg-slate-900 text-white border border-slate-700"
          />

          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full py-3 bg-blue-500 rounded-xl text-white font-semibold"
          >
            {loading ? "Creating..." : "Create Account"}
          </button>

          <p className="text-center text-slate-400 text-sm">
            Already have an account?{" "}
            <button
              onClick={onSwitchToSignIn}
              className="text-blue-400 font-medium"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
