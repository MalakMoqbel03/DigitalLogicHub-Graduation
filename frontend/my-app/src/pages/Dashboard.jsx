import React, { useEffect, useState } from "react";
import api from "../services/api";
import {
  Cpu, LogOut, ArrowRight, Brain, CircuitBoard,
  Trophy, CheckCircle, BookOpen, Target, AlertTriangle,
  BarChart2, Zap, Grid3X3, Hash, Sigma, TrendingUp, TrendingDown, Minus,
  ClipboardList,
} from "lucide-react";
import ThemeToggle from "../components/ThemeToggle";
import StudyAssistant from "../components/StudyAssistant";

// ── Helpers ───────────────────────────────────────────────────────────────────

const LEVEL_COLOR = {
  beginner:
    "text-green-700 border-green-300 bg-green-50 " +
    "dark:text-green-400 dark:border-green-400/30 dark:bg-green-400/10",
  intermediate:
    "text-yellow-700 border-yellow-300 bg-yellow-50 " +
    "dark:text-yellow-400 dark:border-yellow-400/30 dark:bg-yellow-400/10",
  advanced:
    "text-purple-700 border-purple-300 bg-purple-50 " +
    "dark:text-purple-400 dark:border-purple-400/30 dark:bg-purple-400/10",
};

const TOPIC_CONFIG = {
  karnaugh_map:       { label: "Karnaugh Maps",      Icon: Grid3X3,    gradient: "from-cyan-500 to-teal-500"      },
  number_conversions: { label: "Number Conversions", Icon: Hash,       gradient: "from-purple-500 to-indigo-500"  },
  logic_gates:        { label: "Logic Gates",        Icon: Cpu,        gradient: "from-green-500 to-emerald-500"  },
  boolean_algebra:    { label: "Boolean Algebra",    Icon: Sigma,      gradient: "from-orange-500 to-amber-500"   },
};

const LEVEL_ICON = {
  beginner:     TrendingDown,
  intermediate: Minus,
  advanced:     TrendingUp,
};

const LEVEL_COLOR_CLASS = {
  beginner:     "text-green-400",
  intermediate: "text-yellow-400",
  advanced:     "text-purple-400",
};

const VARK_LABEL = {
  visual:       "👁  Visual",
  auditory:     "🎧 Auditory",
  reading:      "📖 Read / Write",
  kinesthetic:  "🛠  Kinesthetic",
};

function StatCard({ icon: Icon, label, value, sub, color = "text-cyan-600 dark:text-cyan-400" }) {
  return (
    <div className="bg-white border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-5 flex flex-col gap-1 transition-colors">
      <div className={`${color} mb-1`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      <p className="text-sm font-medium text-gray-600 dark:text-slate-300">{label}</p>
      {sub && <p className="text-xs text-gray-400 dark:text-slate-500">{sub}</p>}
      </div>
  );
}

function MiniStat({ icon: Icon, label, value, color = "text-cyan-600 dark:text-cyan-400" }) {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <div className={`w-8 h-8 rounded-lg bg-gray-100 dark:bg-slate-700/50 flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <p className="flex-1 min-w-0 text-sm text-gray-600 dark:text-slate-300 truncate">{label}</p>
      <p className="text-sm font-bold text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

function TopicBar({ topic, viewed, total, percentage }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700 dark:text-slate-300 truncate max-w-[60%]">{topic}</span>
        <span className="text-gray-400 dark:text-slate-500">{viewed} / {total}</span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function TopicSkillCard({ topicId, level }) {
  const cfg = TOPIC_CONFIG[topicId];
  if (!cfg) return null;
  const { Icon, gradient, label } = cfg;
  const LevelIcon = LEVEL_ICON[level] || Minus;
  const levelColor = LEVEL_COLOR_CLASS[level] || "text-slate-400";

  return (
    <div className="bg-white border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 rounded-xl p-3 flex items-center gap-3 transition-colors">
      <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center flex-shrink-0`}>
        <Icon className="w-4 h-4 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-gray-700 dark:text-slate-300 text-xs font-medium truncate">{label}</p>
        <div className={`flex items-center gap-1 ${levelColor}`}>
          <LevelIcon className="w-3 h-3" />
          <span className="text-xs font-semibold capitalize">{level}</span>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function Dashboard({ user, onNavigate, onLogout }) {
  const [showVarkConfirm, setShowVarkConfirm] = useState(false);
  const [progress, setProgress]   = useState(null);
  const [topicLevels, setTopicLevels] = useState(null);
  const [loading,  setLoading]    = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/users/progress`);
        setProgress(res.data);
        // Try to get topic-level breakdown from last assessment stored in progress
        if (res.data?.latest_assessment?.topic_levels) {
          setTopicLevels(res.data.latest_assessment.topic_levels);
        }
      } catch {
        setProgress(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user?.id]);

  const level         = progress?.level || user?.level;
  const style         = progress?.learning_style || user?.learning_style;
  const levelClass    = LEVEL_COLOR[level?.toLowerCase()] ||
    "text-gray-600 border-gray-300 bg-gray-100 dark:text-slate-400 dark:border-slate-600 dark:bg-slate-700/30";
  const hasAssessment = (progress?.assessment_count ?? 0) > 0;
  const hasVark       = !!style;

  // Build topic levels from misconceptions if available
  const displayTopicLevels = topicLevels || (hasAssessment && level ? {
    karnaugh_map: level,
    number_conversions: level,
    logic_gates: level,
    boolean_algebra: level,
  } : null);

  // Initials for the profile avatar (from name, falling back to email)
  const initials = ((user?.name || user?.email || "U")
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join("") || "U").toUpperCase();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100
                    dark:from-gray-900 dark:via-slate-900 dark:to-gray-900 p-4 md:p-6 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-6">

        {/* ════════════════ LEFT SIDEBAR ════════════════ */}
        <aside className="w-full lg:w-80 flex-shrink-0 lg:sticky lg:top-6 self-start space-y-5">

          {/* Brand */}
          <div className="flex items-center gap-3 px-1">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 flex-shrink-0">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-gray-900 dark:text-white font-bold text-lg">DigitalLogicHub</h1>
          </div>

          {/* Profile card */}
          <div className="bg-white border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-5 transition-colors">
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-cyan-500/20 mb-3">
                {initials}
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{user?.name || "Learner"}</h2>
              <p className="text-gray-500 dark:text-slate-400 text-sm break-all mt-0.5">{user?.email}</p>
            </div>
            {(level || style) && (
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {level && (
                  <span className={`px-3 py-1 rounded-full text-xs font-medium border ${levelClass}`}>
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </span>
                )}
                {style && (
                  <span className="px-3 py-1 rounded-full text-xs font-medium border
                                   text-cyan-700 border-cyan-300 bg-cyan-50
                                   dark:text-cyan-400 dark:border-cyan-400/30 dark:bg-cyan-400/10">
                    {VARK_LABEL[style] || style}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Progress summary */}
          {!loading && progress && (
            <div className="bg-white border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-5 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <BarChart2 className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                <h3 className="text-gray-900 dark:text-white font-semibold text-sm">Your Progress</h3>
              </div>
              <div className="divide-y divide-gray-100 dark:divide-slate-700/50">
                <MiniStat icon={Trophy} label="Best Score"
                  value={`${progress.best_score}/${progress.best_score > 0 ? 12 : 0}`}
                  color="text-yellow-600 dark:text-yellow-400" />
                <MiniStat icon={BarChart2} label="Assessments Taken"
                  value={progress.assessment_count}
                  color="text-blue-600 dark:text-blue-400" />
                <MiniStat icon={BookOpen} label="Resources Viewed"
                  value={progress.total_resources_viewed}
                  color="text-cyan-600 dark:text-cyan-400" />
                <MiniStat icon={Zap} label="Latest Score"
                  value={progress.latest_assessment ? `${progress.latest_assessment.percentage}%` : "N/A"}
                  color="text-green-600 dark:text-green-400" />
              </div>
            </div>
          )}

          {/* Areas to Improve */}
          {!loading && progress?.top_misconceptions?.length > 0 && (
            <div className="bg-white border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-5 transition-colors">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                <h3 className="text-gray-900 dark:text-white font-semibold text-sm">Areas to Improve</h3>
              </div>
              <div className="space-y-2">
                {progress.top_misconceptions.map((m) => (
                  <div
                    key={m.concept_tag}
                    className="flex items-center justify-between gap-2 p-2.5 bg-yellow-50 border border-yellow-200
                               dark:bg-yellow-500/5 dark:border-yellow-500/20 rounded-xl"
                  >
                    <span className="text-gray-700 dark:text-slate-300 text-xs capitalize truncate">
                      {m.concept_tag.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-yellow-700 dark:text-yellow-400 font-medium flex-shrink-0">
                      {m.count}× missed
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sidebar footer: theme + sign out */}
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={onLogout}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white hover:bg-gray-100 border border-gray-200 text-gray-700
                         dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300
                         rounded-xl transition-colors text-sm"
            >
              <LogOut className="w-4 h-4" /> Sign out
            </button>
          </div>
        </aside>

        {/* ════════════════ MAIN CONTENT ════════════════ */}
        <main className="flex-1 min-w-0 space-y-6">

          {/* Welcome banner */}
          <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-2xl p-7 shadow-2xl">
            <h2 className="text-2xl font-bold text-white mb-1">
              {hasAssessment ? `Keep it up, ${user?.name?.split(" ")[0]}! 🚀` : `Let's get started, ${user?.name?.split(" ")[0]}!`}
            </h2>
            <p className="text-blue-100 text-sm">
              {hasAssessment
                ? "Your personalised topic-by-topic breakdown is ready."
                : "Complete the VARK quiz and skill assessment to unlock your personalised learning path."}
            </p>
          </div>

          {/* Survey Banner */}
          <div className="flex items-center justify-between gap-4
                          bg-white border border-indigo-200 dark:bg-slate-800/50 dark:border-indigo-500/30
                          rounded-2xl px-5 py-4 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500
                              flex items-center justify-center flex-shrink-0 shadow-md shadow-indigo-500/20">
                <ClipboardList className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-gray-900 dark:text-white font-semibold text-sm">
                  Share your experience with us 🙏
                </p>
                <p className="text-gray-500 dark:text-slate-400 text-xs mt-0.5">
                  Takes less than 3 minutes. Your feedback helps us improve DigitalLogicHub.{" "}
                  <span className="text-indigo-400 dark:text-indigo-400 text-xs">↗ opens in new tab</span>
                </p>
              </div>
            </div>
            <a
              href="https://forms.gle/ZTAEt5Hx82KmLsAW8"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 flex items-center gap-2 px-4 py-2
                         bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600
                         text-white text-sm font-semibold rounded-xl transition-all shadow-md shadow-indigo-500/20"
            >
              Take Survey
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          {/* Action cards */}
          <div className="grid md:grid-cols-2 gap-6">

            {/* VARK Card */}
            <div className="bg-white border border-gray-200 hover:border-purple-400
                            dark:bg-slate-800/50 dark:backdrop-blur-xl dark:border-slate-700 dark:hover:border-purple-500/50
                            rounded-2xl p-6 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">VARK Learning Style</h3>
              <p className="text-gray-500 dark:text-slate-400 text-sm mb-4">
                Discover how you learn best: Visual, Auditory, Read/Write, or Kinesthetic.
              </p>
              <div className="flex items-center gap-3 text-xs text-gray-400 dark:text-slate-500 mb-4">
                <span>16 Questions</span><span>•</span><span>~5 min</span>
              </div>
              {hasVark && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200
                                dark:bg-green-500/10 dark:border-green-500/30 rounded-xl">
                  <p className="text-green-700 dark:text-green-400 text-sm flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    Completed: {VARK_LABEL[style] || style}
                  </p>
                </div>
              )}
              <button
                onClick={() => setShowVarkConfirm(true)}
                className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2"
              >
                {hasVark ? "Retake Quiz" : "Start Quiz"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Assessment Card */}
            <div className="bg-white border border-gray-200 hover:border-cyan-400
                            dark:bg-slate-800/50 dark:backdrop-blur-xl dark:border-slate-700 dark:hover:border-cyan-500/50
                            rounded-2xl p-6 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center mb-4">
                <CircuitBoard className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">Skill Assessment</h3>
              <p className="text-gray-500 dark:text-slate-400 text-sm mb-4">
                4 topics · 12 questions total. K-Maps, Number Conversions, Logic Gates, Boolean Algebra.
              </p>
              <div className="flex items-center gap-3 text-xs text-gray-400 dark:text-slate-500 mb-4">
                <span>12 Questions</span><span>•</span><span>4 Topics</span><span>•</span><span>~10 min</span>
              </div>
              {hasAssessment && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200
                                dark:bg-blue-500/10 dark:border-blue-500/30 rounded-xl">
                  <p className="text-blue-700 dark:text-blue-400 text-sm flex items-center gap-2">
                    <Trophy className="w-4 h-4" />
                    Best: {progress.best_score}/12 &nbsp;·&nbsp; Overall: {progress.level}
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

          {/* Topic skill breakdown (shown after assessment) */}
          {!loading && hasAssessment && displayTopicLevels && (
            <div className="bg-white border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-6 transition-colors">
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                <h3 className="text-gray-900 dark:text-white font-semibold">Your Topic Skill Levels</h3>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(displayTopicLevels).map(([topicId, topicLevel]) => (
                  <TopicSkillCard key={topicId} topicId={topicId} level={topicLevel} />
                ))}
              </div>
            </div>
          )}

          {/* Topic progress bars */}
          {!loading && progress?.topic_progress?.length > 0 && (
            <div className="bg-white border border-gray-200
                            dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-6 transition-colors">
              <div className="flex items-center gap-2 mb-5">
                <Target className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                <h3 className="text-gray-900 dark:text-white font-semibold">Topic Progress</h3>
                <span className="text-xs text-gray-400 dark:text-slate-500 ml-auto">{level} level</span>
              </div>
              {progress.topic_progress.slice(0, 6).map((t) => (
                <TopicBar key={t.topic} {...t} />
              ))}
            </div>
          )}

          {/* Learning Materials CTA */}
          {hasAssessment && hasVark && (
            <button
              onClick={() => onNavigate("learningMaterials")}
              className="w-full py-4 bg-white border border-gray-200 hover:border-cyan-400 text-gray-900
                         dark:bg-slate-800/50 dark:hover:bg-slate-700/50 dark:border-slate-700 dark:hover:border-cyan-500/50 dark:text-white
                         rounded-2xl font-semibold transition-colors flex items-center justify-center gap-3"
            >
              <BookOpen className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
              View My Personalised Learning Materials
              <ArrowRight className="w-5 h-5 text-gray-400 dark:text-slate-400" />
            </button>
          )}

        </main>
      </div>

      {/* ── VARK retake confirmation modal ─────────────────────────────── */}
      {showVarkConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-sm w-full shadow-2xl border border-gray-200 dark:border-slate-700">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
              Retake VARK Quiz?
            </h3>
            <p className="text-gray-500 dark:text-slate-400 text-sm mb-5">
              This will reset your current learning style result and update your personalised recommendations. Are you sure?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowVarkConfirm(false);
                  onNavigate("vark");
                }}
                className="flex-1 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white font-semibold rounded-xl transition text-sm"
              >
                Yes, retake
              </button>
              <button
                onClick={() => setShowVarkConfirm(false)}
                className="flex-1 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-gray-700 dark:text-slate-300 font-semibold rounded-xl transition text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── AI Study Assistant - fixed to viewport ───────────────────────── */}
      <StudyAssistant user={user} />

    </div>
  );
}