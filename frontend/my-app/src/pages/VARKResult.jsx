import React from "react";
import { CheckCircle, BarChart3, Home } from "lucide-react";

const descriptions = {
  visual: {
    title: "Visual Learner",
    tips: [
      "Use diagrams and mind maps",
      "Watch videos",
      "Use color-coded notes",
    ],
  },
  auditory: {
    title: "Auditory Learner",
    tips: [
      "Listen to lectures",
      "Join discussions",
      "Explain concepts aloud",
    ],
  },
  reading: {
    title: "Read/Write Learner",
    tips: [
      "Rewrite notes",
      "Read textbooks",
      "Make summaries",
    ],
  },
  kinesthetic: {
    title: "Kinesthetic Learner",
    tips: [
      "Practice hands-on",
      "Use real-life examples",
      "Study while moving",
    ],
  },
};

export default function VARKResult({ result, onBack }) {
  const style = result?.learning_style?.toLowerCase();
  const data = descriptions[style];

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <button onClick={onBack}>← Back</button>
        <p>No result found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6 text-white">
      <div className="max-w-3xl mx-auto">

        <div className="flex justify-between mb-6">
          <h1 className="text-xl font-semibold flex gap-2 items-center">
            <BarChart3 /> VARK Results
          </h1>
          <button onClick={onBack} className="flex gap-2 items-center">
            <Home className="w-4 h-4" /> Dashboard
          </button>
        </div>

        <div className="bg-purple-600 rounded-2xl p-8 text-center mb-6">
          <h2 className="text-3xl font-bold">
            {data.title}
          </h2>
        </div>

        <div className="bg-slate-800 rounded-2xl p-6">
          <h3 className="font-semibold mb-4">
            Learning Tips
          </h3>

          <div className="space-y-3">
            {data.tips.map((tip, i) => (
              <div key={i} className="flex gap-2">
                <CheckCircle className="text-green-400 w-4 h-4 mt-1" />
                <span>{tip}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}