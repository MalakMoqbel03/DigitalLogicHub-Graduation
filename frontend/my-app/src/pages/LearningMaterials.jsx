import React, { useEffect, useState } from "react";
import { Home, BookOpen, ExternalLink } from "lucide-react";
import { fetchRecommendations } from "../services/api";

export default function LearningMaterials({ user, onBack, onOpenResource })  {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const style =
    user?.varkResult?.learning_style || user?.learning_style || "Not set";

  const level =
    user?.level || "Not set";

  useEffect(() => {
    if (!user?.id) return;

    const load = async () => {
      setLoading(true);
      setError("");

      try {
        const data = await fetchRecommendations(user.id);
        setItems(data.items || []);
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

  

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-cyan-400" />
            <div>
              <h1 className="text-2xl font-bold">Recommended Learning Materials</h1>
              <p className="text-slate-400 text-sm">
                Based on your learning style and current level
              </p>
            </div>
          </div>

          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300"
          >
            <Home className="w-4 h-4" />
            Dashboard
          </button>
        </div>

        <div className="mb-6 p-4 rounded-xl bg-slate-800/50 border border-slate-700">
          <p className="text-slate-300">
            Learning Style: <span className="font-semibold text-cyan-400">{style}</span>
          </p>
          <p className="text-slate-300">
            Level: <span className="font-semibold text-cyan-400">{level}</span>
          </p>
        </div>

        {loading && <p className="text-slate-300">Loading recommendations...</p>}
        {error && <p className="text-red-400">{error}</p>}

        {!loading && !error && items.length === 0 && (
          <div className="p-6 rounded-xl bg-slate-800/50 border border-slate-700">
            <p>No matching materials found yet.</p>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {items.map((r) => (
            <div
              key={r.id}
              className="bg-slate-800/50 border border-slate-700 rounded-2xl p-5"
            >
              <h3 className="text-lg font-bold text-white mb-2">{r.title}</h3>

              <p className="text-slate-400 text-sm mb-2">
                {r.topic} {r.subtopic ? `• ${r.subtopic}` : ""}
              </p>

              <p className="text-slate-400 text-sm mb-3">
                {r.resource_type} • {r.difficulty} • {r.vark_style}
                {r.duration_minutes ? ` • ${r.duration_minutes} min` : ""}
                {r.is_short ? " • short" : ""}
              </p>

              {r.description && (
                <p className="text-slate-300 text-sm mb-4">{r.description}</p>
              )}

              <button
                onClick={() => {
                    onOpenResource(r);
                    }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl"
              >
                Open Resource
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}