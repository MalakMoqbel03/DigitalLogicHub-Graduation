import React, { useEffect, useState, useCallback } from "react";
import api from "../services/api";
import {
  ArrowLeft, ArrowRight, CheckCircle, XCircle, Trophy,
  Home, AlertTriangle, BookOpen, Loader2, ChevronRight,
  Hash, Cpu, Grid3X3, Sigma, Star, TrendingUp, TrendingDown, Minus,
} from "lucide-react";

// ─────────────────────────────────────────────────────────────────────────────
// Constants & helpers
// ─────────────────────────────────────────────────────────────────────────────

const TOPIC_ICONS = {
  karnaugh_map:       { Icon: Grid3X3,  gradient: "from-cyan-500 to-teal-500",     ring: "ring-cyan-400/30",    badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"  },
  number_conversions: { Icon: Hash,     gradient: "from-purple-500 to-indigo-500", ring: "ring-purple-400/30",  badge: "bg-purple-500/10 text-purple-400 border-purple-500/30" },
  logic_gates:        { Icon: Cpu,      gradient: "from-green-500 to-emerald-500", ring: "ring-green-400/30",   badge: "bg-green-500/10 text-green-400 border-green-500/30"  },
  boolean_algebra:    { Icon: Sigma,     gradient: "from-orange-500 to-amber-500",  ring: "ring-orange-400/30",  badge: "bg-orange-500/10 text-orange-400 border-orange-500/30" },
};

const DIFF_BADGE = {
  easy:   "bg-green-500/10 text-green-400 border border-green-500/20",
  medium: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
  hard:   "bg-red-500/10 text-red-400 border border-red-500/20",
};

const LEVEL_CONFIG = {
  beginner:     { color: "text-green-400",  bg: "bg-green-500/10 border-green-500/30",  Icon: TrendingDown, label: "Beginner"     },
  intermediate: { color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/30", Icon: Minus,        label: "Intermediate" },
  advanced:     { color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/30", Icon: TrendingUp,   label: "Advanced"     },
};

const shuffleArray = (arr) => [...arr].sort(() => Math.random() - 0.5);

const GridBg = () => (
  <div className="fixed inset-0 pointer-events-none overflow-hidden">
    <div className="absolute inset-0 opacity-[0.04]" style={{
      backgroundImage: `linear-gradient(rgba(6,182,212,.8) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(6,182,212,.8) 1px, transparent 1px)`,
      backgroundSize: "60px 60px",
    }} />
    <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />
    <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl" />
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function SectionNav({ sections, currentSection, answers, onJump }) {
  return (
    <div className="flex gap-2 flex-wrap justify-center mb-8">
      {sections.map((sec, i) => {
        const cfg = TOPIC_ICONS[sec.topic.id] || {};
        const sectionAnswers = answers[sec.topic.id] || {};
        const answered = Object.keys(sectionAnswers).length;
        const total = sec.questions.length;
        const isActive = i === currentSection;
        const isDone = answered === total;

        return (
          <button
            key={sec.topic.id}
            onClick={() => onJump(i)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all duration-200
              ${isActive
                ? `bg-gradient-to-r ${cfg.gradient} text-white border-transparent shadow-lg`
                : isDone
                  ? "bg-slate-800/80 border-green-500/40 text-green-400"
                  : "bg-slate-800/60 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-300"
              }`}
          >
            {cfg.Icon && <cfg.Icon className="w-4 h-4" />}
            <span className="hidden sm:inline">{sec.topic.label}</span>
            <span className="text-xs opacity-80">{answered}/{total}</span>
            {isDone && <CheckCircle className="w-3.5 h-3.5 text-green-400" />}
          </button>
        );
      })}
    </div>
  );
}

function AnswerOption({ text, selected, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full p-4 rounded-xl text-left transition-all duration-200 border text-sm leading-relaxed
        ${selected
          ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-400/60 text-white shadow-lg shadow-cyan-500/10"
          : "bg-slate-800/50 border-slate-700/60 text-slate-300 hover:bg-slate-700/60 hover:border-slate-600 hover:text-white"
        } disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      <span className={`inline-block w-5 h-5 rounded-full border mr-3 flex-shrink-0 align-middle transition-all
        ${selected ? "border-cyan-400 bg-cyan-400" : "border-slate-500"}`} />
      {text}
    </button>
  );
}

function ResultTopicCard({ topicId, result, suggestion, section }) {
  const cfg = TOPIC_ICONS[topicId] || {};
  const lvlCfg = LEVEL_CONFIG[result.level] || LEVEL_CONFIG.beginner;
  const { Icon: TopicIcon, gradient } = cfg;
  const { Icon: LevelIcon } = lvlCfg;

  return (
    <div className="bg-slate-800/50 border border-slate-700/60 rounded-2xl p-6 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg`}>
            {TopicIcon && <TopicIcon className="w-5 h-5 text-white" />}
          </div>
          <div>
            <h3 className="text-white font-semibold">{section?.topic?.label || topicId}</h3>
            <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border ${lvlCfg.bg} ${lvlCfg.color}`}>
              <LevelIcon className="w-3 h-3" /> {lvlCfg.label}
            </span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-white">{result.score}/{result.total}</p>
          <p className="text-xs text-slate-400">correct</p>
        </div>
      </div>

      {/* Score bar */}
      <div className="h-2 bg-slate-700 rounded-full mb-4 overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${gradient} rounded-full transition-all duration-700`}
          style={{ width: `${(result.score / result.total) * 100}%` }}
        />
      </div>

      {/* Question breakdown */}
      <div className="space-y-2 mb-4">
        {result.details.map((d, i) => (
          <div key={i} className={`flex items-start gap-3 p-3 rounded-xl border text-sm
            ${d.is_correct
              ? "bg-green-500/5 border-green-500/20"
              : "bg-red-500/5 border-red-500/20"}`}
          >
            {d.is_correct
              ? <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              : <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
            }
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${DIFF_BADGE[d.difficulty]}`}>
                  {d.difficulty}
                </span>
                <span className="text-slate-400 text-xs truncate">{d.question_text}</span>
              </div>
              {!d.is_correct && (
                <div className="space-y-0.5">
                  <p className="text-red-400 text-xs">Your answer: {d.selected_answer}</p>
                  <p className="text-green-400 text-xs">Correct: {d.correct_answer}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Misconception alert */}
      {result.misconceptions.length > 0 && (
        <div className="p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-xl flex gap-2 mb-3">
          <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-yellow-400 text-xs font-medium mb-0.5">Misconception detected</p>
            <p className="text-slate-400 text-xs">{result.misconceptions.map(m => m.replace(/_/g, " ")).join(", ")}</p>
          </div>
        </div>
      )}

      {/* Suggestion */}
      {suggestion && (
        <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-xl flex gap-2">
          <BookOpen className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
          <p className="text-blue-300 text-xs">{suggestion.recommendation}</p>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────────────────

export default function DigitalAssessment({ user, onComplete, onBack, onNavigate }) {
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState(null);

  // answers[topicId][difficulty] = { question_id, answer_id }
  const [answers, setAnswers] = useState({});
  // shuffled answers per question
  const [shuffledAnswers, setShuffledAnswers] = useState({});
  // which section (0-3) is active
  const [currentSection, setCurrentSection] = useState(0);

  // Load questions
  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/assessment/questions");
        const secs = res.data.sections || [];
        setSections(secs);

        // Pre-shuffle each question's answers
        const shuffled = {};
        secs.forEach((sec) => {
          sec.questions.forEach((q) => {
            shuffled[q.id] = shuffleArray(q.answers);
          });
        });
        setShuffledAnswers(shuffled);
      } catch {
        setError("Failed to load assessment questions. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const selectAnswer = useCallback((topicId, difficulty, questionId, answerId) => {
    setAnswers((prev) => ({
      ...prev,
      [topicId]: {
        ...(prev[topicId] || {}),
        [difficulty]: { question_id: questionId, answer_id: answerId },
      },
    }));
  }, []);

  // Count total answered
  const totalAnswered = Object.values(answers).reduce(
    (sum, topicAnswers) => sum + Object.keys(topicAnswers).length, 0
  );
  const totalQuestions = sections.reduce((s, sec) => s + sec.questions.length, 0);
  const allAnswered = totalAnswered === totalQuestions && totalQuestions > 0;

  const submit = async () => {
    if (!allAnswered) return;
    setSubmitting(true);
    setError("");
    try {
      const res = await api.post("/assessment/submit", {
        user_id: user.id,
        topic_answers: answers,
      });
      setResults(res.data);
      onComplete?.(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to submit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Loading ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <GridBg />
        <div className="text-center relative z-10">
          <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading your assessment…</p>
        </div>
      </div>
    );
  }

  // ─── Results ───────────────────────────────────────────────────────────────
  if (results) {
    const lvlCfg = LEVEL_CONFIG[results.level] || LEVEL_CONFIG.beginner;
    const { Icon: LevelIcon } = lvlCfg;

    return (
      <div className="min-h-screen bg-gray-950 p-4 relative">
        <GridBg />
        <div className="max-w-4xl mx-auto relative z-10 pb-16">
          {/* Header */}
          <div className="flex justify-between items-center mb-8 pt-4">
            <div className="flex items-center gap-2 text-white font-semibold">
              <Trophy className="w-5 h-5 text-yellow-400" />
              Assessment Results
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => onNavigate?.("learningMaterials")}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-white text-sm font-medium transition-colors"
              >
                <BookOpen className="w-4 h-4" /> Learning Materials
              </button>
              <button
                onClick={onBack}
                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm transition-colors"
              >
                <Home className="w-4 h-4" /> Dashboard
              </button>
            </div>
          </div>

          {/* Overall score banner */}
          <div className="relative overflow-hidden rounded-2xl p-8 mb-8 text-white text-center bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/60">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-purple-500/10" />
            <div className="relative z-10">
              <p className="text-slate-400 text-sm mb-2">Overall Score</p>
              <div className="text-6xl font-bold mb-2">{results.percentage}%</div>
              <div className="text-xl text-slate-300 mb-3">{results.score} / {results.total} correct</div>
              <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-semibold ${lvlCfg.bg} ${lvlCfg.color}`}>
                <LevelIcon className="w-4 h-4" />
                Overall Level: {lvlCfg.label}
              </span>
            </div>
          </div>

          {/* Per-topic level pills */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
            {sections.map((sec) => {
              const topicResult = results.topic_results?.[sec.topic.id];
              if (!topicResult) return null;
              const cfg = TOPIC_ICONS[sec.topic.id] || {};
              const lvl = LEVEL_CONFIG[topicResult.level] || LEVEL_CONFIG.beginner;
              return (
                <div key={sec.topic.id} className={`p-4 rounded-xl border text-center ${lvl.bg}`}>
                  <div className={`w-8 h-8 mx-auto mb-2 rounded-lg bg-gradient-to-br ${cfg.gradient} flex items-center justify-center`}>
                    {cfg.Icon && <cfg.Icon className="w-4 h-4 text-white" />}
                  </div>
                  <p className="text-xs text-slate-400 mb-1">{sec.topic.label}</p>
                  <p className={`text-sm font-bold ${lvl.color}`}>{lvl.label}</p>
                  <p className="text-xs text-slate-500">{topicResult.score}/{topicResult.total}</p>
                </div>
              );
            })}
          </div>

          {/* Misconception alert */}
          {results.misconceptions_detected?.length > 0 && (
            <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-2xl flex gap-3 mb-6">
              <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-yellow-400 font-medium mb-1">Misconceptions Detected</p>
                <p className="text-slate-400 text-sm">
                  We found repeated errors in: {results.misconceptions_detected.map(m => m.replace(/_/g, " ")).join(", ")}.
                  Your learning materials have been personalised to address these gaps.
                </p>
              </div>
            </div>
          )}

          {/* Per-topic detailed results */}
          <h2 className="text-white font-bold text-lg mb-4">Topic Breakdown</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {sections.map((sec) => {
              const topicResult = results.topic_results?.[sec.topic.id];
              const suggestion = results.topic_suggestions?.[sec.topic.id];
              if (!topicResult) return null;
              return (
                <ResultTopicCard
                  key={sec.topic.id}
                  topicId={sec.topic.id}
                  result={topicResult}
                  suggestion={suggestion}
                  section={sec}
                />
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // ─── Assessment ────────────────────────────────────────────────────────────
  const sec = sections[currentSection];
  if (!sec) return null;

  const cfg = TOPIC_ICONS[sec.topic.id] || {};
  const sectionAnswers = answers[sec.topic.id] || {};
  const sectionAnswered = Object.keys(sectionAnswers).length;
  const sectionTotal = sec.questions.length;
  const sectionProgress = (sectionAnswered / sectionTotal) * 100;

  return (
    <div className="min-h-screen bg-gray-950 p-4 relative">
      <GridBg />
      <div className="max-w-2xl mx-auto relative z-10 pb-16">
        {/* Header */}
        <div className="flex justify-between items-center mb-6 pt-4">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${cfg.gradient} flex items-center justify-center`}>
              {cfg.Icon && <cfg.Icon className="w-4 h-4 text-white" />}
            </div>
            Digital Assessment
          </div>
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm transition-colors"
          >
            <Home className="w-4 h-4" /> Dashboard
          </button>
        </div>

        {/* Overall progress */}
        <div className="mb-2 flex justify-between text-xs text-slate-400">
          <span>{totalAnswered} of {totalQuestions} questions answered</span>
          <span>{Math.round((totalAnswered / totalQuestions) * 100) || 0}%</span>
        </div>
        <div className="h-1.5 bg-slate-800 rounded-full mb-6">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
            style={{ width: `${(totalAnswered / totalQuestions) * 100}%` }}
          />
        </div>

        {/* Section navigation */}
        <SectionNav
          sections={sections}
          currentSection={currentSection}
          answers={answers}
          onJump={setCurrentSection}
        />

        {/* Current section header */}
        <div className={`rounded-2xl p-5 mb-6 border bg-gradient-to-r ${cfg.gradient} bg-opacity-10 border-transparent relative overflow-hidden`}
          style={{ background: "linear-gradient(135deg, rgba(6,182,212,0.08), rgba(99,102,241,0.08))", borderColor: "rgba(6,182,212,0.2)" }}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${cfg.gradient} flex items-center justify-center shadow-lg`}>
              {cfg.Icon && <cfg.Icon className="w-6 h-6 text-white" />}
            </div>
            <div>
              <h2 className="text-white font-bold text-lg">{sec.topic.label}</h2>
              <p className="text-slate-400 text-sm">{sec.topic.description}</p>
            </div>
          </div>
          {/* Section progress */}
          <div className="mt-4">
            <div className="flex justify-between text-xs text-slate-400 mb-1.5">
              <span>Section progress</span>
              <span>{sectionAnswered}/{sectionTotal}</span>
            </div>
            <div className="h-1.5 bg-black/30 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${cfg.gradient} rounded-full transition-all duration-400`}
                style={{ width: `${sectionProgress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Questions */}
        <div className="space-y-6">
          {sec.questions.map((q, qi) => {
            const selectedId = sectionAnswers[q.difficulty]?.answer_id;
            const shuffled = shuffledAnswers[q.id] || q.answers;

            return (
              <div key={q.id} className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-5 backdrop-blur-sm">
                {/* Question header */}
                <div className="flex items-center gap-2 mb-3">
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${DIFF_BADGE[q.difficulty]}`}>
                    {q.difficulty === "easy" ? "★ Easy" : q.difficulty === "medium" ? "★★ Medium" : "★★★ Hard"}
                  </span>
                  <span className="text-slate-500 text-xs">Question {qi + 1}</span>
                </div>

                <h3 className="text-white font-medium mb-4 leading-relaxed">{q.question_text}</h3>

                <div className="space-y-2.5">
                  {shuffled.map((a) => (
                    <AnswerOption
                      key={a.id}
                      text={a.answer_text}
                      selected={selectedId === a.id}
                      onClick={() => selectAnswer(sec.topic.id, q.difficulty, q.id, a.id)}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => setCurrentSection((c) => Math.max(0, c - 1))}
            disabled={currentSection === 0}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Previous
          </button>

          {currentSection < sections.length - 1 ? (
            <button
              onClick={() => setCurrentSection((c) => c + 1)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all
                ${sectionAnswered === sectionTotal
                  ? `bg-gradient-to-r ${cfg.gradient} text-white shadow-lg`
                  : "bg-slate-800 border border-slate-700 text-slate-400"}`}
            >
              Next Section <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={submit}
              disabled={!allAnswered || submitting}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20 transition-all hover:opacity-90"
            >
              {submitting
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Submitting…</>
                : <><CheckCircle className="w-4 h-4" /> Submit Assessment</>
              }
            </button>
          )}
        </div>

        {!allAnswered && currentSection === sections.length - 1 && (
          <p className="text-center text-slate-500 text-xs mt-3">
            Answer all {totalQuestions} questions to submit ({totalAnswered}/{totalQuestions} done)
          </p>
        )}

        {error && (
          <p className="text-red-400 text-sm text-center mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}