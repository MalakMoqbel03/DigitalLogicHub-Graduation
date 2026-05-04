import React, { useEffect, useState } from "react";
import api from "../services/api";
import { Brain, CheckCircle, Home } from "lucide-react";

export default function VARKQuiz({ user, onComplete, onBack }) {
  const [questions, setQuestions] = useState([]);
  const [current,   setCurrent]   = useState(0);
  const [selected,  setSelected]  = useState({});
  const [loading,   setLoading]   = useState(true);
  const [submitting,setSubmitting]= useState(false);
  const [error,     setError]     = useState("");

  useEffect(() => {
    api.get("/auth/vark/questions")
      .then((res) => setQuestions(res.data.questions || []))
      .catch(() => setError("Failed to load VARK questions from server."))
      .finally(() => setLoading(false));
  }, []);

  const total         = questions.length;
  const answeredCount = Object.keys(selected).length;
  const allAnswered   = answeredCount === total && total > 0;

  const selectOption = (questionId, optionId) => {
    setSelected((prev) => ({ ...prev, [questionId]: optionId }));
    setTimeout(() => {
      setCurrent((c) => (c < total - 1 ? c + 1 : c));
    }, 300);
  };

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

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white flex items-center justify-center gap-3 transition-colors">
        <div className="w-6 h-6 border-2 border-purple-400/30 border-t-purple-500 rounded-full animate-spin" />
        Loading VARK questions...
      </div>
    );
  }

  if (error && !questions.length) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white p-6 transition-colors">
        <button onClick={onBack} className="text-gray-500 dark:text-slate-400 mb-4 flex items-center gap-2">
          <Home className="w-4 h-4" /> Dashboard
        </button>
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </div>
    );
  }

  const q = questions[current];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white flex flex-col transition-colors">

      {/* ── Top bar ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-slate-800 transition-colors">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-base">VARK Learning Style Quiz</h1>
            <p className="text-gray-500 dark:text-slate-400 text-xs">Discover how you learn best</p>
          </div>
        </div>
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-colors
                     bg-white hover:bg-gray-100 border border-gray-200 text-gray-700
                     dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300"
        >
          <Home className="w-4 h-4" /> Dashboard
        </button>
      </div>

      {/* ── Progress bar ───────────────────────────────────────────────────── */}
      <div className="h-1 bg-gray-200 dark:bg-slate-800 transition-colors">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
          style={{ width: `${(answeredCount / total) * 100}%` }}
        />
      </div>

      {/* ── Main content ───────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col max-w-2xl w-full mx-auto px-6 py-8">

        <div className="flex justify-between items-center mb-6 text-sm text-gray-500 dark:text-slate-400">
          <span>Question <span className="text-gray-900 dark:text-white font-semibold">{current + 1}</span> of {total}</span>
          <span><span className="text-purple-600 dark:text-purple-400 font-semibold">{answeredCount}</span> answered</span>
        </div>

        <div className="bg-white border border-gray-200 dark:bg-slate-800/60 dark:border-slate-700 rounded-2xl p-7 mb-6 flex-1 transition-colors shadow-sm dark:shadow-none">
          <h2 className="text-lg font-semibold leading-relaxed mb-7">
            {q?.question_text}
          </h2>

          <div className="space-y-3">
            {q?.options
              .filter((o) => o.vark_type !== "kinesthetic")
              .map((o, idx) => {
                const isChosen = selected[q.id] === o.id;
                const labels   = ["A", "B", "C"];
                return (
                  <button
                    key={o.id}
                    onClick={() => selectOption(q.id, o.id)}
                    className={`w-full p-4 rounded-xl text-left transition-all duration-150 flex items-start gap-4 group
                      ${isChosen
                        ? "bg-purple-600 border border-purple-500 text-white shadow-lg shadow-purple-500/20"
                        : "bg-gray-50 border border-gray-200 text-gray-700 hover:bg-gray-100 hover:border-gray-300 " +
                          "dark:bg-slate-700/60 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700 dark:hover:border-slate-500"
                      }`}
                  >
                    <span className={`w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5
                      ${isChosen
                        ? "bg-white/20 text-white"
                        : "bg-gray-200 text-gray-700 group-hover:bg-gray-300 " +
                          "dark:bg-slate-600 dark:text-slate-300 dark:group-hover:bg-slate-500"
                      }`}>
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

        {error && (
          <p className="text-red-600 dark:text-red-400 text-sm mb-4 text-center">{error}</p>
        )}

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

        <div>
          <p className="text-xs text-gray-400 dark:text-slate-500 mb-3 text-center">
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
                      ? "bg-purple-500 text-white ring-2 ring-purple-400 ring-offset-2 ring-offset-white dark:ring-offset-gray-900 scale-110"
                      : isAnswered
                        ? "bg-purple-100 text-purple-700 border border-purple-300 dark:bg-purple-900/70 dark:text-purple-300 dark:border-purple-500/50"
                        : "bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200 hover:text-gray-900 " +
                          "dark:bg-slate-700 dark:text-slate-400 dark:border-slate-600 dark:hover:bg-slate-600 dark:hover:text-white"
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