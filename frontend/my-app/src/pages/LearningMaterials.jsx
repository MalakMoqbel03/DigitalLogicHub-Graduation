import React, { useEffect, useState } from "react";
import { Home, BookOpen, ExternalLink } from "lucide-react";
import { fetchRecommendations } from "../services/api";
import ThemeToggle from "../components/ThemeToggle";
import TopicIcon, { getTopicColors } from "../components/TopicIcon";

export default function LearningMaterials({ user, onBack, onOpenResource }) {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [apiUser, setApiUser] = useState(null);

  useEffect(() => {
    if (!user?.id) return;

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await fetchRecommendations(user.id);
        setItems(data.items || []);
        setApiUser(data.user || null);
      } catch (err) {
        setError(
          err.response?.data?.detail || err.message || "Failed to load recommendations"
        );
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user?.id]);

  const style =
    apiUser?.learning_style ||
    user?.varkResult?.learning_style ||
    user?.learning_style ||
    "Not set";
  const level = apiUser?.level || user?.level || "Not set";

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white p-6 transition-colors">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8 flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
            <div>
              <h1 className="text-2xl font-bold">Recommended Learning Materials</h1>
              <p className="text-gray-500 dark:text-slate-400 text-sm">
                Based on your learning style and current level
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <ThemeToggle />
            <button
              onClick={onBack}
              className="flex items-center gap-2 px-4 py-2 rounded-xl transition-colors bg-white hover:bg-gray-100 border border-gray-200 text-gray-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300"
            >
              <Home className="w-4 h-4" /> Dashboard
            </button>
          </div>
        </div>

        <div className="mb-6 p-4 rounded-xl bg-gray-50 border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 transition-colors">
          <p className="text-gray-700 dark:text-slate-300">
            Learning Style:{" "}
            <span className="font-semibold text-cyan-600 dark:text-cyan-400">
              {style}
            </span>
          </p>
          <p className="text-gray-700 dark:text-slate-300">
            Level:{" "}
            <span className="font-semibold text-cyan-600 dark:text-cyan-400">
              {level}
            </span>
          </p>
        </div>

        {loading && (
          <p className="text-gray-700 dark:text-slate-300">Loading recommendations...</p>
        )}
        {error && <p className="text-red-600 dark:text-red-400">{error}</p>}

        {!loading && !error && items.length === 0 && (
          <div className="p-6 rounded-xl bg-gray-50 border border-gray-200 dark:bg-slate-800/50 dark:border-slate-700 transition-colors">
            <p>No matching materials found yet.</p>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {items.map((r) => {
            const colors = getTopicColors(r.topic);
            const prettyTopic = r.topic ? r.topic.replace(/_/g, " ") : "";

            return (
              <div
                key={r.id}
                className="bg-white border border-gray-200 shadow-sm dark:bg-slate-800/50 dark:border-slate-700 dark:shadow-none rounded-2xl p-5 transition-colors"
              >
                <div className="flex gap-3 items-start mb-3">
                  <TopicIcon topic={r.topic} size={48} />
                  <div className="flex-1 min-w-0">
                    <p
                      className="text-xs font-medium mb-1"
                      style={{ color: colors.fg }}
                    >
                      {prettyTopic}
                      {r.subtopic ? ` • ${r.subtopic}` : ""}
                    </p>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white leading-snug">
                      {r.title}
                    </h3>
                  </div>
                </div>

                <p className="text-gray-500 dark:text-slate-400 text-sm mb-3">
                  {r.resource_type} • {r.difficulty} • {r.vark_style}
                  {r.duration_minutes ? ` • ${r.duration_minutes} min` : ""}
                  {r.is_short ? " • short" : ""}
                </p>

                {r.description && (
                  <p className="text-gray-700 dark:text-slate-300 text-sm mb-4">
                    {r.description}
                  </p>
                )}

                <button
                  onClick={() => onOpenResource(r)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl transition shadow-lg shadow-cyan-500/20"
                >
                  Open Resource
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
