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

/* ==================== HELPERS ==================== */
const shuffleArray = (array) => {
  return [...array].sort(() => Math.random() - 0.5);
};

/* ==================== GRID BACKGROUND ==================== */
const GridBackground = () => (
  <div className="fixed inset-0 pointer-events-none">
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

/* ==================== MAIN COMPONENT ==================== */
export default function DigitalAssessment({ user, onComplete, onBack }) {
  const [questions, setQuestions] = useState([]);
  const [current, setCurrent] = useState(0);

  // { questionId: answerId }
  const [answers, setAnswers] = useState({});

  // shuffled answers per question { questionId: [answers] }
  const [shuffledAnswers, setShuffledAnswers] = useState({});

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [results, setResults] = useState(null);

  /* ==================== LOAD QUESTIONS ==================== */
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const res = await api.get("/assessment/questions");
        const qs = res.data.questions || [];

        // shuffle answers ONCE per question
        const shuffled = {};
        qs.forEach((q) => {
          shuffled[q.id] = shuffleArray(q.answers);
        });

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

  /* ==================== ANSWER SELECT ==================== */
  const selectAnswer = (questionId, answerId) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: answerId,
    }));

    // auto move to next question (UX improvement)
    setTimeout(() => {
      setCurrent((c) =>
        c < questions.length - 1 ? c + 1 : c
      );
    }, 250);
  };

  /* ==================== SUBMIT ==================== */
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

  /* ==================== LOADING ==================== */
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        Loading assessment...
      </div>
    );
  }

  /* ==================== RESULTS ==================== */
  if (results) {
    return (
      <div className="min-h-screen bg-gray-900 p-4 relative">
        <GridBackground />

        <div className="max-w-4xl mx-auto relative z-10">
          <div className="flex justify-between mb-6">
            <div className="flex items-center gap-2 text-white font-semibold">
              <Trophy className="w-5 h-5 text-yellow-400" />
              Assessment Results
            </div>
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-slate-300 hover:text-white"
            >
              <Home className="w-4 h-4" /> Dashboard
            </button>
          </div>

          {/* SCORE */}
          <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl p-8 text-white text-center mb-6">
            <div className="text-4xl font-bold">
              {results.score}/{results.total}
            </div>
            <div className="text-xl">{results.percentage}%</div>
            <div className="text-sm mt-2">
              Level: <b>{results.level}</b>
            </div>
          </div>

          {/* REVIEW */}
          <div className="space-y-4">
            {results.details.map((d, i) => (
              <div
                key={i}
                className={`p-4 rounded-xl border ${
                  d.is_correct
                    ? "bg-green-500/10 border-green-500/30"
                    : "bg-red-500/10 border-red-500/30"
                }`}
              >
                <div className="flex gap-3">
                  {d.is_correct ? (
                    <CheckCircle className="w-5 h-5 text-green-400 mt-1" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400 mt-1" />
                  )}
                  <div>
                    <p className="text-white font-medium">
                      {d.question_text}
                    </p>
                    <p className="text-slate-400 text-sm">
                      Your answer: {d.selected_answer}
                    </p>
                    {!d.is_correct && (
                      <p className="text-green-400 text-sm">
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
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        Loading question...
      </div>
    );
  }

  const progress = ((current + 1) / questions.length) * 100;

  return (
    <div className="min-h-screen bg-gray-900 p-4 relative">
      <GridBackground />

      <div className="max-w-2xl mx-auto relative z-10">
        {/* HEADER */}
        <div className="flex justify-between mb-6">
          <div className="flex items-center gap-2 text-white font-semibold">
            <CircuitBoard className="w-5 h-5 text-cyan-400" />
            Digital Assessment
          </div>
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-slate-300 hover:text-white"
          >
            <Home className="w-4 h-4" /> Dashboard
          </button>
        </div>

        {/* PROGRESS */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-slate-400 mb-1">
            <span>
              Question {current + 1} / {questions.length}
            </span>
            <span>{answeredCount} answered</span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full">
            <div
              className="h-full bg-cyan-500 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* QUESTION */}
        <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 mb-6">
          <h2 className="text-white font-semibold mb-4">
            {q.question_text}
          </h2>

          <div className="space-y-3">
            {shuffledAnswers[q.id]?.map((a) => (
              <button
                key={a.id}
                onClick={() => selectAnswer(q.id, a.id)}
                className={`w-full p-4 rounded-xl text-left transition ${
                  answers[q.id] === a.id
                    ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white"
                    : "bg-slate-900 text-slate-300 hover:bg-slate-700 border border-slate-700"
                }`}
              >
                {a.answer_text}
              </button>
            ))}
          </div>
        </div>

        {/* NAVIGATION */}
        <div className="flex justify-between">
          <button
            onClick={() => setCurrent((c) => Math.max(0, c - 1))}
            disabled={current === 0}
            className="px-6 py-3 bg-slate-800 text-slate-300 rounded-xl disabled:opacity-50 flex gap-2"
          >
            <ArrowLeft className="w-5 h-5" /> Previous
          </button>

          {current === questions.length - 1 && (
            <button
              onClick={submit}
              disabled={answeredCount < questions.length}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl disabled:opacity-50 flex gap-2"
            >
              Submit <CheckCircle className="w-5 h-5" />
            </button>
          )}
        </div>

        {error && (
          <p className="text-red-400 text-sm mt-4">{error}</p>
        )}
      </div>
    </div>
  );
}
