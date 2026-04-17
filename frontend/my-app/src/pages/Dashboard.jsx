import React, { useEffect, useState } from "react";
import api from "../services/api";
import {
  Cpu, LogOut, ArrowRight, Brain, CircuitBoard,
  Trophy, CheckCircle, BookOpen, Target, AlertTriangle,
  BarChart2, Zap,
} from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────────

const LEVEL_COLOR = {
  beginner:     "text-green-400  border-green-400/30  bg-green-400/10",
  intermediate: "text-yellow-400 border-yellow-400/30 bg-yellow-400/10",
  advanced:     "text-purple-400 border-purple-400/30 bg-purple-400/10",
};

const VARK_LABEL = {
  visual:       "👁  Visual",
  auditory:     "🎧 Auditory",
  reading:      "📖 Read / Write",
  kinesthetic:  "🛠  Kinesthetic",
};

function StatCard({ icon: Icon, label, value, sub, color = "text-cyan-400" }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-5 flex flex-col gap-1">
      <div className={`${color} mb-1`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm font-medium text-slate-300">{label}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function TopicBar({ topic, viewed, total, percentage }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-300 truncate max-w-[60%]">{topic}</span>
        <span className="text-slate-500">{viewed} / {total}</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function Dashboard({ user, onNavigate, onLogout }) {
  const [progress, setProgress]   = useState(null);
  const [loading,  setLoading]    = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        // Token is attached automatically by the Axios interceptor
        const res = await api.get(`/users/progress`);
        setProgress(res.data);
      } catch {
        // If the call fails (e.g. no assessments yet), gracefully show nothing
        setProgress(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user?.id]);

  const level         = progress?.level || user?.level;
  const style         = progress?.learning_style || user?.learning_style;
  const levelClass    = LEVEL_COLOR[level?.toLowerCase()] || "text-slate-400 border-slate-600 bg-slate-700/30";
  const hasAssessment = (progress?.assessment_count ?? 0) > 0;
  const hasVark       = !!style;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 p-6">
      <div className="max-w-5xl mx-auto">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold text-xl">DigitalLogicHub</h1>
              <p className="text-slate-400 text-sm">Welcome back, {user?.name}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300 transition"
          >
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>

        {/* ── Welcome banner ──────────────────────────────────────────────── */}
        <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-2xl p-7 mb-8 shadow-2xl flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">
              {hasAssessment ? `Keep it up, ${user?.name?.split(" ")[0]}! 🚀` : `Let's get started, ${user?.name?.split(" ")[0]}!`}
            </h2>
            <p className="text-blue-100 text-sm">
              {hasAssessment
                ? "Your personalised recommendations are ready."
                : "Complete the VARK quiz and skill assessment to unlock your learning path."}
            </p>
          </div>
          {/* Level + Style badges */}
          <div className="flex gap-3 flex-wrap">
            {level && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${levelClass}`}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </span>
            )}
            {style && (
              <span className="px-3 py-1 rounded-full text-sm font-medium border text-cyan-400 border-cyan-400/30 bg-cyan-400/10">
                {VARK_LABEL[style] || style}
              </span>
            )}
          </div>
        </div>

        {/* ── Stat cards ──────────────────────────────────────────────────── */}
        {!loading && progress && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              icon={Trophy}
              label="Best Score"
              value={`${progress.best_score}/10`}
              sub={`${progress.best_percentage}% correct`}
              color="text-yellow-400"
            />
            <StatCard
              icon={BarChart2}
              label="Assessments Taken"
              value={progress.assessment_count}
              sub="skill assessments"
              color="text-purple-400"
            />
            <StatCard
              icon={BookOpen}
              label="Resources Viewed"
              value={progress.total_resources_viewed}
              sub="learning materials"
              color="text-cyan-400"
            />
            <StatCard
              icon={Zap}
              label="Latest Score"
              value={progress.latest_assessment ? `${progress.latest_assessment.percentage}%` : "—"}
              sub={progress.latest_assessment?.level || "not taken yet"}
              color="text-green-400"
            />
          </div>
        )}

        {/* ── Main action cards ────────────────────────────────────────────── */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">

          {/* VARK Card */}
          <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700 hover:border-purple-500/50 transition">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-4">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">VARK Learning Style</h3>
            <p className="text-slate-400 text-sm mb-4">
              Discover how you learn best — Visual, Auditory, Read/Write, or Kinesthetic.
            </p>
            <div className="flex items-center gap-3 text-xs text-slate-500 mb-4">
              <span>16 Questions</span><span>•</span><span>~5 min</span>
            </div>
            {hasVark && (
              <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-xl">
                <p className="text-green-400 text-sm flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Completed — {VARK_LABEL[style] || style}
                </p>
              </div>
            )}
            <button
              onClick={() => onNavigate("vark")}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2"
            >
              {hasVark ? "Retake Quiz" : "Start Quiz"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Assessment Card */}
          <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl p-6 border border-slate-700 hover:border-cyan-500/50 transition">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center mb-4">
              <CircuitBoard className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Skill Assessment</h3>
            <p className="text-slate-400 text-sm mb-4">
              Test your Digital Systems knowledge — logic gates, Boolean algebra, circuits.
            </p>
            <div className="flex items-center gap-3 text-xs text-slate-500 mb-4">
              <span>10 Questions</span><span>•</span><span>~5 min</span>
            </div>
            {hasAssessment && (
              <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                <p className="text-blue-400 text-sm flex items-center gap-2">
                  <Trophy className="w-4 h-4" />
                  Best: {progress.best_score}/10 &nbsp;·&nbsp; Level: {progress.level}
                </p>
              </div>
            )}
            <button
              onClick={() => onNavigate("assessment")}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2"
            >
              {hasAssessment ? "Retake Assessment" : "Start Assessment"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* ── Bottom row: topic progress + misconceptions ──────────────────── */}
        {!loading && progress && (
          <div className="grid md:grid-cols-2 gap-6 mb-6">

            {/* Topic Progress */}
            {progress.topic_progress?.length > 0 && (
              <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-5">
                  <Target className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-white font-semibold">Topic Progress</h3>
                  <span className="text-xs text-slate-500 ml-auto">{level} level</span>
                </div>
                {progress.topic_progress.slice(0, 6).map((t) => (
                  <TopicBar key={t.topic} {...t} />
                ))}
              </div>
            )}

            {/* Misconceptions */}
            {progress.top_misconceptions?.length > 0 && (
              <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-5">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  <h3 className="text-white font-semibold">Areas to Improve</h3>
                </div>
                <div className="space-y-3">
                  {progress.top_misconceptions.map((m) => (
                    <div
                      key={m.concept_tag}
                      className="flex items-center justify-between p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-xl"
                    >
                      <span className="text-slate-300 text-sm capitalize">
                        {m.concept_tag.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-yellow-400 font-medium">
                        {m.count}× missed
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Learning Materials CTA ───────────────────────────────────────── */}
        {hasAssessment && hasVark && (
          <button
            onClick={() => onNavigate("learningMaterials")}
            className="w-full py-4 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 hover:border-cyan-500/50 rounded-2xl text-white font-semibold transition flex items-center justify-center gap-3"
          >
            <BookOpen className="w-5 h-5 text-cyan-400" />
            View My Personalised Learning Materials
            <ArrowRight className="w-5 h-5 text-slate-400" />
          </button>
        )}

      </div>
    </div>
  );
}