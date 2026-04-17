import React, { useEffect, useState } from "react";
import api from "../services/api";
import { Brain, CheckCircle, Home } from "lucide-react";

const VARK_COLORS = {
  visual:   "from-blue-500   to-cyan-500",
  auditory: "from-purple-500 to-pink-500",
  reading:  "from-green-500  to-teal-500",
};

const VARK_LABELS = {
  visual:   "👁  Visual",
  auditory: "🎧 Auditory",
  reading:  "📖 Read / Write",
};

export default function VARKQuiz({ user, onComplete, onBack }) {
  const [questions, setQuestions] = useState([]);
  const [current,   setCurrent]   = useState(0);
  const [selected,  setSelected]  = useState({});   // { questionId: optionId }
  const [loading,   setLoading]   = useState(true);
  const [submitting,setSubmitting]= useState(false);
  const [error,     setError]     = useState("");

  // ── Load questions ──────────────────────────────────────────────────────────
  useEffect(() => {
    api.get("/auth/vark/questions")
      .then((res) => setQuestions(res.data.questions || []))
      .catch(() => setError("Failed to load VARK questions from server."))
      .finally(() => setLoading(false));
  }, []);

  const total        = questions.length;
  const answeredCount = Object.keys(selected).length;
  const allAnswered  = answeredCount === total && total > 0;

  // ── Select an option and auto-advance ──────────────────────────────────────
  const selectOption = (questionId, optionId) => {
    setSelected((prev) => ({ ...prev, [questionId]: optionId }));
    // Short delay so the highlight is visible before moving on
    setTimeout(() => {
      setCurrent((c) => (c < total - 1 ? c + 1 : c));
    }, 300);
  };

  // ── Submit ──────────────────────────────────────────────────────────────────
  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const res = await api.post("/auth/vark/submit", {
        user_id:    user.id,
        option_ids: Object.values(selected),
      });
      if (!res.data?.learning_style) throw new Error("Invalid response");
      onComplete({ learning_style: res.data.learning_style, scores: res.data.scores });
      onBack();
    } catch (err) {
      setError(
        typeof err.response?.data?.detail === "string"
          ? err.response.data.detail
          : "Failed to submit. Please try again."
      );
      setSubmitting(false);
    }
  };

  // ── Loading / error states ──────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center gap-3">
        <div className="w-6 h-6 border-2 border-purple-400/30 border-t-purple-400 rounded-full animate-spin" />
        Loading VARK questions...
      </div>
    );
  }

  if (error && !questions.length) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <button onClick={onBack} className="text-slate-400 mb-4 flex items-center gap-2">
          <Home className="w-4 h-4" /> Dashboard
        </button>
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  const q = questions[current];

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">

      {/* ── Top bar ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-base">VARK Learning Style Quiz</h1>
            <p className="text-slate-400 text-xs">Discover how you learn best</p>
          </div>
        </div>
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300 text-sm transition"
        >
          <Home className="w-4 h-4" /> Dashboard
        </button>
      </div>

      {/* ── Progress bar ───────────────────────────────────────────────────── */}
      <div className="h-1 bg-slate-800">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
          style={{ width: `${(answeredCount / total) * 100}%` }}
        />
      </div>

      {/* ── Main content ───────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col max-w-2xl w-full mx-auto px-6 py-8">

        {/* Question counter */}
        <div className="flex justify-between items-center mb-6 text-sm text-slate-400">
          <span>Question <span className="text-white font-semibold">{current + 1}</span> of {total}</span>
          <span><span className="text-purple-400 font-semibold">{answeredCount}</span> answered</span>
        </div>

        {/* Question card */}
        <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-7 mb-6 flex-1">
          <h2 className="text-lg font-semibold leading-relaxed mb-7">
            {q?.question_text}
          </h2>

          <div className="space-y-3">
            {q?.options
              .filter((o) => o.vark_type !== "kinesthetic")   // remove kinesthetic
              .map((o, idx) => {
                const isChosen = selected[q.id] === o.id;
                const labels   = ["A", "B", "C"];
                return (
                  <button
                    key={o.id}
                    onClick={() => selectOption(q.id, o.id)}
                    className={`w-full p-4 rounded-xl text-left transition-all duration-150 flex items-start gap-4 group
                      ${isChosen
                        ? "bg-purple-600/80 border border-purple-400 text-white shadow-lg shadow-purple-500/20"
                        : "bg-slate-700/60 border border-slate-600 text-slate-200 hover:bg-slate-700 hover:border-slate-500"
                      }`}
                  >
                    {/* Letter badge */}
                    <span className={`w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5
                      ${isChosen ? "bg-white/20 text-white" : "bg-slate-600 text-slate-300 group-hover:bg-slate-500"}`}>
                      {labels[idx]}
                    </span>
                    <span className="leading-relaxed">{o.option_text}</span>
                    {isChosen && (
                      <CheckCircle className="w-5 h-5 text-purple-200 flex-shrink-0 ml-auto mt-0.5" />
                    )}
                  </button>
                );
              })}
          </div>
        </div>

        {/* Error message */}
        {error && (
          <p className="text-red-400 text-sm mb-4 text-center">{error}</p>
        )}

        {/* Submit button — only shows when all answered */}
        {allAnswered && (
          <button
            onClick={submit}
            disabled={submitting}
            className="w-full py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:opacity-90 transition disabled:opacity-60 flex items-center justify-center gap-2 mb-6"
          >
            {submitting
              ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Submitting...</>
              : <><CheckCircle className="w-5 h-5" /> Submit Quiz</>
            }
          </button>
        )}

        {/* ── Question number navigation ────────────────────────────────────── */}
        <div>
          <p className="text-xs text-slate-500 mb-3 text-center">
            Click a number to jump to that question
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {questions.map((qItem, idx) => {
              const isAnswered = selected[qItem.id] !== undefined;
              const isCurrent  = idx === current;
              return (
                <button
                  key={qItem.id}
                  onClick={() => setCurrent(idx)}
                  className={`w-9 h-9 rounded-lg text-sm font-semibold transition-all duration-150
                    ${isCurrent
                      ? "bg-purple-500 text-white ring-2 ring-purple-400 ring-offset-2 ring-offset-gray-900 scale-110"
                      : isAnswered
                        ? "bg-purple-900/70 text-purple-300 border border-purple-500/50"
                        : "bg-slate-700 text-slate-400 border border-slate-600 hover:bg-slate-600 hover:text-white"
                    }`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}