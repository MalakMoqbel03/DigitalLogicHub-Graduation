import React, { useEffect, useState } from "react";
import api from "../services/api";
import { Home, ThumbsUp, ThumbsDown, Star } from "lucide-react";
import ThemeToggle from "../components/ThemeToggle";

export default function ResourceViewer({ user, resource, onBack }) {
  const [rating, setRating] = useState(0);
  const [liked, setLiked] = useState(null);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");

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
  }, [user.id, resource.id]);

  const saveFeedback = async () => {
    try {
      await api.post("/recommender/feedback", {
        user_id: user.id,
        resource_id: resource.id,
        rating,
        liked,
        comment,
      });
      setMessage("Feedback saved successfully");
    } catch (err) {
      setMessage("Failed to save feedback");
    }
  };

  const renderEmbed = () => {
    if (!resource?.external_url) return <p>No resource URL available.</p>;

    if (resource.resource_type === "video" && resource.external_url.includes("youtube.com")) {
      const videoId = new URL(resource.external_url).searchParams.get("v");
      if (videoId) {
        return (
          <iframe
            title={resource.title}
            width="100%"
            height="480"
            src={`https://www.youtube.com/embed/${videoId}`}
            allowFullScreen
            className="rounded-xl"
          />
        );
      }
    }

    if (resource.resource_type === "pdf" || resource.external_url.endsWith(".pdf")) {
      return (
        <iframe
          title={resource.title}
          src={resource.external_url}
          width="100%"
          height="600"
          className="rounded-xl bg-white"
        />
      );
    }

    return (
      <div className="space-y-3">
        <p className="text-gray-700 dark:text-slate-300">
          This resource cannot be embedded directly here.
        </p>
        <a
          href={resource.external_url}
          target="_blank"
          rel="noreferrer"
          className="inline-block px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl transition shadow-lg shadow-cyan-500/20"
        >
          Open Original Source
        </a>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white p-6 transition-colors">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 rounded-xl transition-colors bg-white hover:bg-gray-100 border border-gray-200 text-gray-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300"
          >
            <Home className="w-4 h-4" /> Back
          </button>
          <ThemeToggle />
        </div>

        <div className="bg-white border border-gray-200 shadow-sm dark:bg-slate-800/50 dark:border-slate-700 dark:shadow-none rounded-2xl p-6 mb-6 transition-colors">
          <h1 className="text-2xl font-bold mb-2">{resource.title}</h1>
          <p className="text-gray-500 dark:text-slate-400 mb-4">
            {resource.topic} {resource.subtopic ? `\u2022 ${resource.subtopic}` : ""}
          </p>
          {renderEmbed()}
        </div>

        <div className="bg-white border border-gray-200 shadow-sm dark:bg-slate-800/50 dark:border-slate-700 dark:shadow-none rounded-2xl p-6 transition-colors">
          <h2 className="text-xl font-bold mb-4">Your Feedback</h2>

          <div className="flex gap-2 mb-4">
            {[1, 2, 3, 4, 5].map((s) => (
              <button key={s} onClick={() => setRating(s)}>
                <Star
                  className={`w-6 h-6 transition-colors ${
                    s <= rating
                      ? "text-yellow-500 fill-yellow-500 dark:text-yellow-400 dark:fill-yellow-400"
                      : "text-gray-300 dark:text-slate-500"
                  }`}
                />
              </button>
            ))}
          </div>

          <div className="flex gap-3 mb-4">
            <button
              onClick={() => setLiked(true)}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-colors ${
                liked === true
                  ? "bg-green-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
              }`}
            >
              <ThumbsUp className="w-4 h-4" />
              Like
            </button>

            <button
              onClick={() => setLiked(false)}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-colors ${
                liked === false
                  ? "bg-red-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
              }`}
            >
              <ThumbsDown className="w-4 h-4" />
              Dislike
            </button>
          </div>

          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Write your opinion about this material..."
            className="w-full p-3 rounded-xl mb-4 transition-colors bg-gray-50 border border-gray-200 text-gray-900 placeholder-gray-400 dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            rows={4}
          />

          <button
            onClick={saveFeedback}
            className="px-5 py-3 bg-cyan-500 hover:bg-cyan-400 text-white rounded-xl transition shadow-lg shadow-cyan-500/20"
          >
            Save Feedback
          </button>

          {message && <p className="mt-3 text-gray-600 dark:text-slate-300">{message}</p>}
        </div>
      </div>
    </div>
  );
}
