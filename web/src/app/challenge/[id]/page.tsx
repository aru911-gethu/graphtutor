"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Trophy, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";

export default function ChallengePage() {
  const params = useParams();
  const id = params?.id || "chl_demo123";

  const [answered, setAnswered] = useState<number | null>(null);
  const [score, setScore] = useState<number | null>(null);

  const sampleQuestion = {
    prompt: "What is the core architectural innovation of the Transformer over RNNs?",
    options: [
      "It computes pairwise token self-attention in parallel, eliminating sequential bottleneck.",
      "It uses continuous Fourier transformations instead of matrix multiplications.",
      "It eliminates all matrix multiplications using discrete lookup trees.",
      "It requires strictly single-precision integer CPU arithmetic."
    ],
    correct_index: 0
  };

  const handleSelect = (idx: number) => {
    setAnswered(idx);
    if (idx === sampleQuestion.correct_index) {
      setScore(100);
    } else {
      setScore(0);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-12 space-y-8 text-center">
      <div className="space-y-3">
        <div className="w-12 h-12 rounded-full bg-amber-950 border border-amber-700 text-amber-400 mx-auto flex items-center justify-center">
          <Trophy className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-extrabold text-white">Quiz Calibration Challenge</h1>
        <p className="text-sm text-gray-400">
          A friend challenged you to beat their score on <span className="text-indigo-400 font-bold">Transformers</span>!
        </p>
      </div>

      {/* Side by side comparison */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-1">
          <span className="text-xs font-mono text-gray-400">Friend's Score</span>
          <p className="text-3xl font-bold text-indigo-400">95%</p>
        </div>
        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-1">
          <span className="text-xs font-mono text-gray-400">Your Score</span>
          <p className="text-3xl font-bold text-emerald-400">{score !== null ? `${score}%` : "—"}</p>
        </div>
      </div>

      {/* Question */}
      <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 text-left space-y-4">
        <p className="text-base text-gray-200 font-semibold">{sampleQuestion.prompt}</p>
        <div className="space-y-2">
          {sampleQuestion.options.map((opt, idx) => (
            <button
              key={idx}
              disabled={answered !== null}
              onClick={() => handleSelect(idx)}
              className={`w-full text-left p-3.5 rounded-xl border text-xs transition ${
                answered !== null
                  ? idx === sampleQuestion.correct_index
                    ? "border-emerald-500 bg-emerald-950/40 text-emerald-300 font-bold"
                    : idx === answered
                    ? "border-red-500 bg-red-950/40 text-red-300"
                    : "border-gray-800 bg-gray-900/20 text-gray-500"
                  : "border-gray-800 bg-gray-900/40 text-gray-300 hover:border-gray-700"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {score !== null && (
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            {score === 100 ? "You tied the challenge! Ready to explore your full graph?" : "Nice try! Review transformers to close the gap."}
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center space-x-2 px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition shadow-xl shadow-indigo-600/30"
          >
            <span>Start Learning with graphtutor</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  );
}