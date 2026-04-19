import React, { useEffect, useState } from "react";
import api from "../services/api";
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Trophy,
  CircuitBoard,
  Home,
} from "lucide-react";

const shuffleArray = (array) => [...array].sort(() => Math.random() - 0.5);

const GridBackground = () => (
  <div className="fixed inset-0 pointer-events-none">
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

export default function DigitalAssessment({ user, onComplete, onBack }) {
  const [questions, setQuestions] = useState([]);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState({});
  const [shuffledAnswers, setShuffledAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [results, setResults] = useState(null);

  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const res = await api.get("/assessment/questions");
        const qs = res.data.questions || [];
        const shuffled = {};
        qs.forEach((q) => { shuffled[q.id] = shuffleArray(q.answers); });
        setQuestions(qs);
        setShuffledAnswers(shuffled);
      } catch {
        setError("Failed to load assessment questions.");
      } finally {
        setLoading(false);
      }
    };
    loadQuestions();
  }, []);

  const answeredCount = Object.keys(answers).length;

  const selectAnswer = (questionId, answerId) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answerId }));
    setTimeout(() => {
      setCurrent((c) => c < questions.length - 1 ? c + 1 : c);
    }, 250);
  };

  const submit = async () => {
    try {
      setError("");
      const res = await api.post("/assessment/submit", {
        user_id: user.id,
        answers,
      });
      const safeResult = {
        score: res.data.score,
        total: res.data.total,
        percentage: res.data.percentage,
        level: res.data.level,
        details: res.data.details || [],
      };
      setResults(safeResult);
      onComplete?.(safeResult);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          e.response?.data?.message ||
          "Failed to submit assessment."
      );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white flex items-center justify-center transition-colors">
        Loading assessment...
      </div>
    );
  }

  /* ==================== RESULTS ==================== */
  if (results) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 p-4 relative transition-colors">
        <GridBackground />

        <div className="max-w-4xl mx-auto relative z-10">
          <div className="flex justify-between mb-6">
            <div className="flex items-center gap-2 text-gray-900 dark:text-white font-semibold">
              <Trophy className="w-5 h-5 text-yellow-500 dark:text-yellow-400" />
              Assessment Results
            </div>
            <button
              onClick={onBack}
              className="flex items-center gap-2 px-3 py-2 rounded-xl transition-colors
                         bg-white hover:bg-gray-100 border border-gray-200 text-gray-700
                         dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300"
            >
              <Home className="w-4 h-4" /> Dashboard
            </button>
          </div>

          <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl p-8 text-white text-center mb-6 shadow-lg shadow-cyan-500/20">
            <div className="text-4xl font-bold">
              {results.score}/{results.total}
            </div>
            <div className="text-xl">{results.percentage}%</div>
            <div className="text-sm mt-2">
              Level: <b>{results.level}</b>
            </div>
          </div>

          <div className="space-y-4">
            {results.details.map((d, i) => (
              <div
                key={i}
                className={`p-4 rounded-xl border transition-colors ${
                  d.is_correct
                    ? "bg-green-50 border-green-200 dark:bg-green-500/10 dark:border-green-500/30"
                    : "bg-red-50 border-red-200 dark:bg-red-500/10 dark:border-red-500/30"
                }`}
              >
                <div className="flex gap-3">
                  {d.is_correct
                    ? <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mt-1 flex-shrink-0" />
                    : <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-1 flex-shrink-0" />
                  }
                  <div>
                    <p className="text-gray-900 dark:text-white font-medium">
                      {d.question_text}
                    </p>
                    <p className="text-gray-500 dark:text-slate-400 text-sm">
                      Your answer: {d.selected_answer}
                    </p>
                    {!d.is_correct && (
                      <p className="text-green-600 dark:text-green-400 text-sm">
                        Correct: {d.correct_answer}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  /* ==================== QUESTIONS ==================== */
  const q = questions[current];

  if (!q) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white flex items-center justify-center transition-colors">
        Loading question...
      </div>
    );
  }

  const progress = ((current + 1) / questions.length) * 100;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 p-4 relative transition-colors">
      <GridBackground />

      <div className="max-w-2xl mx-auto relative z-10">
        <div className="flex justify-between mb-6">
          <div className="flex items-center gap-2 text-gray-900 dark:text-white font-semibold">
            <CircuitBoard className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
            Digital Assessment
          </div>
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-3 py-2 rounded-xl transition-colors
                       bg-white hover:bg-gray-100 border border-gray-200 text-gray-700
                       dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300"
          >
            <Home className="w-4 h-4" /> Dashboard
          </button>
        </div>

        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-500 dark:text-slate-400 mb-1">
            <span>Question {current + 1} / {questions.length}</span>
            <span>{answeredCount} answered</span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-slate-800 rounded-full transition-colors">
            <div
              className="h-full bg-cyan-500 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="bg-white border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 p-6 rounded-2xl mb-6 transition-colors shadow-sm dark:shadow-none">
          <h2 className="text-gray-900 dark:text-white font-semibold mb-4">
            {q.question_text}
          </h2>

          <div className="space-y-3">
            {shuffledAnswers[q.id]?.map((a) => (
              <button
                key={a.id}
                onClick={() => selectAnswer(q.id, a.id)}
                className={`w-full p-4 rounded-xl text-left transition-colors ${
                  answers[q.id] === a.id
                    ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white border border-transparent"
                    : "bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200 " +
                      "dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-700 dark:border-slate-700"
                }`}
              >
                {a.answer_text}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={() => setCurrent((c) => Math.max(0, c - 1))}
            disabled={current === 0}
            className="px-6 py-3 rounded-xl disabled:opacity-50 flex gap-2 items-center transition-colors
                       bg-white hover:bg-gray-100 border border-gray-200 text-gray-700
                       dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300"
          >
            <ArrowLeft className="w-5 h-5" /> Previous
          </button>

          {current === questions.length - 1 && (
            <button
              onClick={submit}
              disabled={answeredCount < questions.length}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl disabled:opacity-50 flex gap-2 items-center shadow-lg shadow-cyan-500/25"
            >
              Submit <CheckCircle className="w-5 h-5" />
            </button>
          )}
        </div>

        {error && (
          <p className="text-red-600 dark:text-red-400 text-sm mt-4">{error}</p>
        )}
      </div>
    </div>
  );
}