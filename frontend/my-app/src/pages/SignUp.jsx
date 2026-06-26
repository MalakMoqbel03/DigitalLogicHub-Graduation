import React, { useState } from "react";
import api from "../services/api";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  CheckCircle,
  XCircle,
  Cpu,
  User,
  GraduationCap,
  BookOpen,
  Calendar,
} from "lucide-react";
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
  </div>
);

const STUDY_YEARS = [
  { value: "1", label: "1st Year" },
  { value: "2", label: "2nd Year" },
  { value: "3", label: "3rd Year" },
  { value: "4", label: "4th Year" },
  { value: "5+", label: "5th Year or above" },
  { value: "postgrad", label: "Postgraduate" },
];

export default function SignUp({ onSwitchToSignIn }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [universityName, setUniversityName] = useState("");
  const [major, setMajor] = useState("");
  const [studyYear, setStudyYear] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showVerification, setShowVerification] = useState(false);
  const [userCode, setUserCode] = useState(["", "", "", "", "", ""]);

  const validatePassword = (pwd) =>
    pwd.length >= 8 &&
    pwd.length <= 15 &&
    /[A-Z]/.test(pwd) &&
    /[a-z]/.test(pwd) &&
    /[0-9]/.test(pwd) &&
    /[^A-Za-z0-9]/.test(pwd);   // at least one special character

  const handleRegister = async () => {
    setError("");
    setSuccess("");
    if (!validatePassword(password)) {
      setError("Password must be 8-15 chars and include uppercase, lowercase, a number, and a special character (e.g. !@#$%)");
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
        university_name: universityName.trim() || null,
        major: major.trim() || null,
        study_year: studyYear || null,
      });
      setShowVerification(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    }
    setLoading(false);
  };

  const handleCodeInput = (index, value) => {
    if (!/^\d?$/.test(value)) return;
    const newCode = [...userCode];
    newCode[index] = value;
    setUserCode(newCode);
    if (value && index < 5) document.getElementById(`code-${index + 1}`)?.focus();
  };

  const handleVerify = async () => {
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/verify", { email: email.toLowerCase(), code: userCode.join("") });
      setSuccess("Account verified successfully!");
      setTimeout(() => onSwitchToSignIn(), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid code");
      setUserCode(["", "", "", "", "", ""]);
    }
    setLoading(false);
  };

  const inputClass =
    "w-full p-3 rounded-xl bg-gray-50 border border-gray-200 text-gray-900 placeholder-gray-400 " +
    "dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:placeholder-slate-500 " +
    "focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors";

  const selectClass =
    "w-full p-3 rounded-xl appearance-none bg-gray-50 border border-gray-200 text-gray-900 " +
    "dark:bg-slate-900 dark:border-slate-700 dark:text-white " +
    "focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors";

  if (showVerification) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-gray-900 dark:via-slate-900 dark:to-gray-900 flex items-center justify-center p-4 relative transition-colors">
        <GridBackground />
        <div className="absolute top-4 right-4 z-20"><ThemeToggle /></div>
        <div className="max-w-md w-full bg-white border border-gray-200 shadow-xl dark:bg-slate-800/50 dark:border-slate-700 p-8 rounded-2xl relative z-10 transition-colors">
          <div className="text-center mb-6">
            <Cpu className="mx-auto text-green-500 dark:text-green-400 w-10 h-10 mb-2" />
            <h2 className="text-gray-900 dark:text-white text-2xl font-bold">Verify Email</h2>
            <p className="text-gray-500 dark:text-slate-400 text-sm">{email}</p>
          </div>
          {error && <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-transparent rounded-xl flex gap-2"><XCircle className="w-4 h-4" /> {error}</div>}
          {success && <div className="mb-4 p-3 bg-green-50 text-green-700 border border-green-200 dark:bg-green-500/10 dark:text-green-400 dark:border-transparent rounded-xl flex gap-2"><CheckCircle className="w-4 h-4" /> {success}</div>}
          <div className="flex justify-center gap-2 mb-6">
            {userCode.map((v, i) => (
              <input key={i} id={`code-${i}`} value={v} maxLength={1}
                onChange={(e) => handleCodeInput(i, e.target.value)}
                className="w-12 h-14 text-center text-xl rounded-xl bg-gray-50 text-gray-900 border border-gray-200 dark:bg-slate-900 dark:text-white dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-colors"
              />
            ))}
          </div>
          <button onClick={handleVerify} disabled={loading || userCode.join("").length !== 6}
            className="w-full py-3 bg-green-500 hover:bg-green-400 disabled:opacity-50 rounded-xl text-white font-semibold transition">
            {loading ? "Verifying..." : "Verify Account"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-gray-900 dark:via-slate-900 dark:to-gray-900 flex items-center justify-center p-4 relative transition-colors">
      <GridBackground />
      <div className="absolute top-4 right-4 z-20"><ThemeToggle /></div>

      <div className="max-w-md w-full bg-white border border-gray-200 shadow-xl dark:bg-slate-800/50 dark:border-slate-700 p-8 rounded-2xl relative z-10 transition-colors">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 mb-4 shadow-lg shadow-blue-500/25">
            <Cpu className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-gray-900 dark:text-white text-2xl font-bold">Create Account</h2>
          <p className="text-gray-500 dark:text-slate-400 text-sm">Start your learning journey</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-transparent rounded-xl flex gap-2 items-center">
            <XCircle className="w-4 h-4" /> {error}
          </div>
        )}

        <div className="space-y-4">
          <div className="relative">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
            <input placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} className={inputClass + " pl-12"} />
          </div>

          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
            <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass + " pl-12"} />
          </div>

          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
            <input type={showPassword ? "text" : "password"} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className={inputClass + " pl-12 pr-12"} />
            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300">
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          {/* Live password strength checklist */}
          {password.length > 0 && (
            <div className="grid grid-cols-2 gap-1 text-xs px-1">
              {[
                { ok: password.length >= 8 && password.length <= 15, label: "8-15 characters" },
                { ok: /[A-Z]/.test(password), label: "Uppercase letter" },
                { ok: /[a-z]/.test(password), label: "Lowercase letter" },
                { ok: /[0-9]/.test(password), label: "Number" },
                { ok: /[^A-Za-z0-9]/.test(password), label: "Special character (!@#$%…)" },
              ].map(({ ok, label }) => (
                <span key={label} className={`flex items-center gap-1 ${ok ? "text-green-600 dark:text-green-400" : "text-gray-400 dark:text-slate-500"}`}>
                  {ok ? "✓" : "○"} {label}
                </span>
              ))}
            </div>
          )}

          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
            <input type={showPassword ? "text" : "password"} placeholder="Confirm Password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className={inputClass + " pl-12"} />
          </div>

          {/* Academic profile divider */}
          <div className="pt-2">
            <p className="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-3">
              Academic Profile <span className="normal-case font-normal opacity-70">(optional)</span>
            </p>

            <div className="space-y-3">
              <div className="relative">
                <GraduationCap className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
                <input placeholder="University Name" value={universityName} onChange={(e) => setUniversityName(e.target.value)} className={inputClass + " pl-12"} />
              </div>

              <div className="relative">
                <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500" />
                <input placeholder="Major / Field of Study" value={major} onChange={(e) => setMajor(e.target.value)} className={inputClass + " pl-12"} />
              </div>

              <div className="relative">
                <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-slate-500 pointer-events-none z-10" />
                <select value={studyYear} onChange={(e) => setStudyYear(e.target.value)} className={selectClass + " pl-12"}>
                  <option value="">Study Year</option>
                  {STUDY_YEARS.map((y) => <option key={y.value} value={y.value}>{y.label}</option>)}
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-400 hover:to-cyan-400 disabled:opacity-50 rounded-xl text-white font-semibold flex items-center justify-center gap-2 transition shadow-lg shadow-blue-500/25"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>Create Account <ArrowRight className="w-5 h-5" /></>
            )}
          </button>

          <p className="text-center text-gray-500 dark:text-slate-400 text-sm">
            Already have an account?{" "}
            <button onClick={onSwitchToSignIn} className="text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 font-medium">
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}