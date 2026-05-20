import React from "react";
import { CheckCircle, BarChart3, Home } from "lucide-react";

const descriptions = {
  visual: {
    title: "Visual Learner",
    tips: ["Use diagrams and mind maps", "Watch videos", "Use color-coded notes"],
  },
  auditory: {
    title: "Auditory Learner",
    tips: ["Listen to lectures", "Join discussions", "Explain concepts aloud"],
  },
  reading: {
    title: "Read/Write Learner",
    tips: ["Rewrite notes", "Read textbooks", "Make summaries"],
  },
};

export default function VARKResult({ result, onBack }) {
  const style = result?.learning_style?.toLowerCase();
  const data = descriptions[style];

  if (!data) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white p-6 transition-colors">
        <button onClick={onBack}>← Back</button>
        <p>No result found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 p-6 text-gray-900 dark:text-white transition-colors">
      <div className="max-w-3xl mx-auto">

        <div className="flex justify-between mb-6">
          <h1 className="text-xl font-semibold flex gap-2 items-center">
            <BarChart3 /> VARK Results
          </h1>
          <button
            onClick={onBack}
            className="flex gap-2 items-center px-3 py-2 rounded-xl transition-colors
                       bg-white hover:bg-gray-100 border border-gray-200 text-gray-700
                       dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-slate-700 dark:text-slate-300"
          >
            <Home className="w-4 h-4" /> Dashboard
          </button>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl p-8 text-center mb-6 text-white shadow-lg shadow-purple-500/20">
          <h2 className="text-3xl font-bold">
            {data.title}
          </h2>
        </div>

        <div className="bg-white border border-gray-200 dark:bg-slate-800 dark:border-slate-700 rounded-2xl p-6 transition-colors shadow-sm dark:shadow-none">
          <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">
            Learning Tips
          </h3>

          <div className="space-y-3">
            {data.tips.map((tip, i) => (
              <div key={i} className="flex gap-2 text-gray-700 dark:text-slate-300">
                <CheckCircle className="text-green-600 dark:text-green-400 w-4 h-4 mt-1 flex-shrink-0" />
                <span>{tip}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}