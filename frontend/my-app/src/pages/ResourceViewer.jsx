import React, { useEffect, useState } from "react";
import api from "../services/api";
import {
  Home, ThumbsUp, ThumbsDown, Star,
  CheckCircle, XCircle, ChevronRight, Award, Loader2,
  TrendingUp, AlertTriangle, Bookmark, BookmarkCheck, Lightbulb,
  Check
} from "lucide-react";
import ThemeToggle from "../components/ThemeToggle";

// ─────────────────────────────────────────────────────────────────────────────
// Quiz component
// ─────────────────────────────────────────────────────────────────────────────
function ResourceQuiz({ user, resource, onQuizDone }) {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/quiz/questions/${resource.id}`, {
          params: { user_id: user.id },
        });
        setQuestions(res.data.questions || []);
      } catch {
        setError("Could not load quiz questions.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [resource.id, user.id]);

  const handleSelect = (questionId, option) => {
    if (result) return;
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  };

  const handleSubmit = async () => {
    if (Object.keys(answers).length < questions.length) {
      setError("Please answer all questions before submitting.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        user_id: user.id,
        resource_id: resource.id,
        answers: questions.map((q) => ({
          question_id: q.id,
          chosen_option: answers[q.id],
        })),
      };
      const res = await api.post("/quiz/submit", payload);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-500 dark:text-slate-400 py-4">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading quiz…
      </div>
    );
  }

  if (questions.length === 0) return null;

  const OPTION_LABELS = { a: "A", b: "B", c: "C", d: "D" };
  const OPTION_KEYS = ["a", "b", "c", "d"];

  return (
    <div className="mt-6 bg-white border border-gray-200 shadow-sm dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-6 transition-colors">
      <div className="flex items-center gap-2 mb-5">
        <Award className="w-5 h-5 text-cyan-500" />
        <h2 className="text-xl font-bold">Quick Knowledge Check</h2>
        <span className="ml-auto text-xs text-gray-400 dark:text-slate-500">
          {questions.length} question{questions.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Result banner */}
      {result && (
        <div className={`mb-5 p-4 rounded-xl flex flex-col gap-3 ${
          result.percentage >= 50
            ? "bg-green-50 border border-green-200 dark:bg-green-500/10 dark:border-green-500/30"
            : "bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/30"
        }`}>
          <div className="flex items-center gap-2">
            {result.percentage >= 50
              ? <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              : <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />}
            <p className={`font-bold ${result.percentage >= 50 ? "text-green-700 dark:text-green-300" : "text-red-700 dark:text-red-300"}`}>
              {result.score} / {result.total} correct ({result.percentage}%)
            </p>
          </div>

          {result.level_changed && (
            <div className="flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
              <span className="text-cyan-700 dark:text-cyan-300 font-medium">
                Level updated to <strong>{result.new_level}</strong>!
              </span>
            </div>
          )}

          {result.top_misconceptions?.length > 0 && (
            <div className="mt-1">
              <div className="flex items-center gap-1 text-xs text-orange-600 dark:text-orange-400 font-semibold mb-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Areas to Improve
              </div>
              <div className="flex flex-wrap gap-2">
                {result.top_misconceptions.map((m) => (
                  <span key={m.concept_tag}
                    className="px-2 py-1 text-xs rounded-lg bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300">
                    {m.concept_tag.replace(/_/g, " ")} ({m.count}×)
                  </span>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={onQuizDone}
            className="mt-1 self-start inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl text-sm transition shadow-lg shadow-cyan-500/20"
          >
            Continue <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-transparent rounded-xl flex gap-2">
          <XCircle className="w-4 h-4 flex-shrink-0" /> {error}
        </div>
      )}

      {/* Questions */}
      <div className="space-y-6">
        {questions.map((q, qi) => {
          const qResult = result?.results?.find((r) => r.question_id === q.id);
          return (
            <div key={q.id}>
              <p className="font-medium text-gray-800 dark:text-white mb-3">
                {qi + 1}. {q.question_text}
              </p>
              <div className="grid grid-cols-1 gap-2">
                {OPTION_KEYS.map((key) => {
                  const isSelected = answers[q.id] === key;
                  const isCorrect = qResult && key === qResult.correct;
                  const isWrong = qResult && isSelected && !qResult.is_correct;

                  let btnClass = "w-full text-left px-4 py-3 rounded-xl text-sm transition-colors border ";
                  if (isCorrect && result) {
                    btnClass += "bg-green-100 border-green-400 text-green-800 dark:bg-green-500/20 dark:border-green-500 dark:text-green-300";
                  } else if (isWrong) {
                    btnClass += "bg-red-100 border-red-400 text-red-800 dark:bg-red-500/20 dark:border-red-500 dark:text-red-300";
                  } else if (isSelected) {
                    btnClass += "bg-cyan-100 border-cyan-400 text-cyan-800 dark:bg-cyan-500/20 dark:border-cyan-500 dark:text-cyan-300";
                  } else {
                    btnClass += "bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800";
                  }

                  return (
                    <button key={key} className={btnClass} onClick={() => handleSelect(q.id, key)} disabled={!!result}>
                      <span className="font-bold mr-2">{OPTION_LABELS[key]}.</span> {q.options[key]}
                    </button>
                  );
                })}
              </div>

              {/* AI Explanation for wrong answers */}
              {qResult && !qResult.is_correct && qResult.explanation && (
                <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-200 dark:bg-amber-500/10 dark:border-amber-500/30 flex gap-2">
                  <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                    {qResult.explanation}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {!result && (
        <button
          onClick={handleSubmit}
          disabled={submitting || Object.keys(answers).length < questions.length}
          className="mt-6 w-full py-3 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
        >
          {submitting ? <><Loader2 className="w-4 h-4 animate-spin" /> Submitting…</> : "Submit Answers"}
        </button>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main ResourceViewer
// ─────────────────────────────────────────────────────────────────────────────
export default function ResourceViewer({ user, resource, onBack }) {
  const [rating, setRating] = useState(0);
  const [liked, setLiked] = useState(null);
  const [comment, setComment] = useState("");
  const [saveStatus, setSaveStatus] = useState("idle"); // idle | saving | saved | error
  const [saveTimer, setSaveTimer] = useState(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizDone, setQuizDone] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [bookmarkLoading, setBookmarkLoading] = useState(false);

  useEffect(() => {
    const loadFeedback = async () => {
      try {
        const res = await api.get(`/recommender/feedback/${user.id}/${resource.id}`);
        setRating(res.data.rating || 0);
        setLiked(res.data.liked);
        setComment(res.data.comment || "");
      } catch (err) {
        console.error(err);
      }
    };
    loadFeedback();

    const loadBookmark = async () => {
      try {
        const res = await api.get(`/recommender/bookmarks/${user.id}`);
        const isSaved = (res.data.items || []).some((r) => r.id === resource.id);
        setBookmarked(isSaved);
      } catch {}
    };
    loadBookmark();

    const checkQuiz = async () => {
      try {
        const res = await api.get(`/quiz/history/${user.id}/${resource.id}`);
        if (res.data.attempted) setQuizDone(true);
      } catch {}
    };
    checkQuiz();
  }, [user.id, resource.id]);

  const toggleBookmark = async () => {
    setBookmarkLoading(true);
    try {
      const res = await api.post("/recommender/bookmark", {
        user_id: user.id,
        resource_id: resource.id,
        bookmarked: !bookmarked,
      });
      setBookmarked(res.data.bookmarked);
    } catch {}
    finally {
      setBookmarkLoading(false);
    }
  };

  // Auto-save feedback whenever rating or liked changes (debounced 600ms)
  const autoSaveFeedback = async (newRating, newLiked, newComment) => {
    setSaveStatus("saving");
    try {
      await api.post("/recommender/feedback", {
        user_id: user.id,
        resource_id: resource.id,
        rating: newRating === 0 ? null : newRating,
        liked: newLiked,
        comment: newComment,
      });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 2500);
    }
  };

  const scheduleAutoSave = (newRating, newLiked, newComment) => {
    if (saveTimer) clearTimeout(saveTimer);
    const t = setTimeout(() => autoSaveFeedback(newRating, newLiked, newComment), 600);
    setSaveTimer(t);
  };

  const handleRatingChange = (s) => {
    setRating(s);
    scheduleAutoSave(s, liked, comment);
  };

  const handleLikedChange = (val) => {
    setLiked(val);
    scheduleAutoSave(rating, val, comment);
  };

  const handleCommentBlur = () => {
    // Save on textarea blur (when user finishes typing)
    autoSaveFeedback(rating, liked, comment);
  };

  const renderEmbed = () => {
    const url = resource?.external_url;
    const type = (resource?.resource_type || "").toLowerCase();

    // ── YouTube video ─────────────────────────────────────────────────────
    if (type === "video" && url?.includes("youtube.com")) {
      let videoId = null;
      try { videoId = new URL(url).searchParams.get("v"); } catch {}
      if (videoId) {
        return (
          <iframe
            title={resource.title}
            width="100%" height="480"
            src={`https://www.youtube.com/embed/${videoId}`}
            allowFullScreen
            className="rounded-xl"
          />
        );
      }
    }

    // ── YouTube short URL (youtu.be) ──────────────────────────────────────
    if (type === "video" && url?.includes("youtu.be")) {
      let videoId = null;
      try { videoId = new URL(url).pathname.replace("/", ""); } catch {}
      if (videoId) {
        return (
          <iframe
            title={resource.title}
            width="100%" height="480"
            src={`https://www.youtube.com/embed/${videoId}`}
            allowFullScreen
            className="rounded-xl"
          />
        );
      }
    }

    // ── PDF ───────────────────────────────────────────────────────────────
    if (type === "pdf" || url?.endsWith(".pdf")) {
      return (
        <iframe
          title={resource.title}
          src={url}
          width="100%" height="600"
          className="rounded-xl bg-white"
        />
      );
    }

    // ── Everything else: article / website / interactive / unknown ────────
    // Don't try to iframe arbitrary websites (they block it).
    // Show a rich resource card instead.
    const typeLabel = {
      article:     "Article",
      website:     "Website",
      interactive: "Interactive",
      book:        "Book / Reading",
      slide:       "Slides",
      slides:      "Slides",
      tutorial:    "Tutorial",
    }[type] || (type ? type.charAt(0).toUpperCase() + type.slice(1) : "Resource");

    const typeIcon = {
      article:     "📄",
      website:     "🌐",
      interactive: "🖱️",
      book:        "📚",
      slide:       "🖼️",
      slides:      "🖼️",
      tutorial:    "🎓",
      video:       "▶️",
    }[type] || "🔗";

    return (
      <div className="rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 p-6 flex flex-col gap-4">
        {/* Type badge */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">{typeIcon}</span>
          <span className="text-sm font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide">
            {typeLabel}
          </span>
        </div>

        {/* Description */}
        {resource.description && (
          <p className="text-gray-700 dark:text-slate-300 leading-relaxed text-sm">
            {resource.description}
          </p>
        )}

        {/* Meta row */}
        <div className="flex flex-wrap gap-3 text-xs text-gray-500 dark:text-slate-500">
          {resource.difficulty && (
            <span className="px-2 py-1 rounded-lg bg-gray-100 dark:bg-slate-800">
              Level: {resource.difficulty}
            </span>
          )}
          {resource.duration_minutes && (
            <span className="px-2 py-1 rounded-lg bg-gray-100 dark:bg-slate-800">
              ⏱ {resource.duration_minutes} min
            </span>
          )}
          {resource.vark_style && (
            <span className="px-2 py-1 rounded-lg bg-gray-100 dark:bg-slate-800">
              Style: {resource.vark_style}
            </span>
          )}
          {resource.source && (
            <span className="px-2 py-1 rounded-lg bg-gray-100 dark:bg-slate-800">
              Source: {resource.source}
            </span>
          )}
        </div>

        {/* Open button */}
        {url ? (
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="self-start inline-flex items-center gap-2 px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-white font-semibold rounded-xl transition shadow-lg shadow-cyan-500/20 text-sm"
          >
            Open {typeLabel} <span>↗</span>
          </a>
        ) : (
          <p className="text-sm text-gray-400 dark:text-slate-500 italic">No URL available for this resource.</p>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white p-6 transition-colors">
      <div className="max-w-4xl mx-auto">

        {/* Top bar */}
        <div className="flex items-center justify-between mb-6">
          <button onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 rounded-xl transition-colors bg-white hover:bg-gray-100 border border-gray-200 text-gray-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300">
            <Home className="w-4 h-4" /> Back
          </button>
          <ThemeToggle />
        </div>

        {/* Resource embed */}
        <div className="bg-white border border-gray-200 shadow-sm dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-6 mb-6 transition-colors">
          <div className="flex items-start justify-between gap-3 mb-2">
            <h1 className="text-2xl font-bold flex-1">{resource.title}</h1>
            <button
              onClick={toggleBookmark}
              disabled={bookmarkLoading}
              title={bookmarked ? "Remove bookmark" : "Save for later"}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors border flex-shrink-0 ${
                bookmarked
                  ? "bg-cyan-50 border-cyan-300 text-cyan-700 dark:bg-cyan-500/20 dark:border-cyan-500/50 dark:text-cyan-300"
                  : "bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
              }`}
            >
              {bookmarkLoading
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : bookmarked
                  ? <><BookmarkCheck className="w-4 h-4" /> Saved</>
                  : <><Bookmark className="w-4 h-4" /> Save</>
              }
            </button>
          </div>

          <p className="text-gray-500 dark:text-slate-400 mb-4">
            {resource.topic} {resource.subtopic ? `• ${resource.subtopic}` : ""}
          </p>
          {renderEmbed()}

          {!showQuiz && !quizDone && (
            <div className="mt-6 p-4 rounded-xl bg-cyan-50 border border-cyan-200 dark:bg-cyan-500/10 dark:border-cyan-500/30 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <Award className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                <p className="text-cyan-800 dark:text-cyan-200 text-sm font-medium">
                  Done watching? Test your understanding with 2 quick questions!
                </p>
              </div>
              <button
                onClick={() => setShowQuiz(true)}
                className="flex items-center gap-1 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl text-sm font-semibold transition shadow-lg shadow-cyan-500/20 whitespace-nowrap"
              >
                Take Quiz <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {quizDone && !showQuiz && (
            <div className="mt-4 flex items-center gap-2 text-green-600 dark:text-green-400 text-sm">
              <CheckCircle className="w-4 h-4" /> Quiz completed for this resource
            </div>
          )}
        </div>

        {showQuiz && !quizDone && (
          <ResourceQuiz
            user={user}
            resource={resource}
            onQuizDone={() => { setQuizDone(true); setShowQuiz(false); }}
          />
        )}

        {/* Feedback */}
        <div className="bg-white border border-gray-200 shadow-sm dark:bg-slate-800/50 dark:border-slate-700 rounded-2xl p-6 transition-colors mt-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Your Feedback</h2>
            {/* Fix #5: visual save status indicator */}
            {saveStatus === "saving" && (
              <span className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-slate-500">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…
              </span>
            )}
            {saveStatus === "saved" && (
              <span className="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400 font-medium">
                <Check className="w-3.5 h-3.5" /> Saved
              </span>
            )}
            {saveStatus === "error" && (
              <span className="flex items-center gap-1.5 text-xs text-red-500 dark:text-red-400">
                <XCircle className="w-3.5 h-3.5" /> Failed to save
              </span>
            )}
          </div>

          {/* Fix #1: rating triggers auto-save */}
          <div className="flex gap-2 mb-4">
            {[1, 2, 3, 4, 5].map((s) => (
              <button key={s} onClick={() => handleRatingChange(s)}>
                <Star className={`w-6 h-6 transition-colors ${
                  s <= rating
                    ? "text-yellow-500 fill-yellow-500 dark:text-yellow-400 dark:fill-yellow-400"
                    : "text-gray-300 dark:text-slate-500"
                }`} />
              </button>
            ))}
          </div>

          {/* Fix #1: like/dislike triggers auto-save */}
          <div className="flex gap-3 mb-4">
            <button onClick={() => handleLikedChange(true)}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-colors ${
                liked === true
                  ? "bg-green-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
              }`}>
              <ThumbsUp className="w-4 h-4" /> Like
            </button>
            <button onClick={() => handleLikedChange(false)}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-colors ${
                liked === false
                  ? "bg-red-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
              }`}>
              <ThumbsDown className="w-4 h-4" /> Dislike
            </button>
          </div>

          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            onBlur={handleCommentBlur}
            placeholder="Write your opinion about this material..."
            className="w-full p-3 rounded-xl transition-colors bg-gray-50 border border-gray-200 text-gray-900 placeholder-gray-400 dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            rows={4}
          />
          <p className="mt-1.5 text-xs text-gray-400 dark:text-slate-500">
            Feedback is saved automatically when you rate or like/dislike.
          </p>
        </div>
      </div>
    </div>
  );
}