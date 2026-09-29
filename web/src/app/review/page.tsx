"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDueReviews, submitReview } from "@/lib/api";
import { Clock, CheckCircle2, RotateCcw, ArrowRight, Sparkles } from "lucide-react";

export default function ReviewSessionPage() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showAnswer, setShowAnswer] = useState(false);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    async function loadReviews() {
      try {
        const due = await getDueReviews();
        setReviews(due);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadReviews();
  }, []);

  const handleGrade = async (rating: number) => {
    const current = reviews[currentIndex];
    if (current) {
      await submitReview(current.concept, rating).catch(() => {});
    }

    if (currentIndex + 1 < reviews.length) {
      setCurrentIndex(currentIndex + 1);
      setShowAnswer(false);
    } else {
      setCompleted(true);
    }
  };

  if (loading) {
    return <div className="py-24 text-center text-gray-400 font-mono">Loading due FSRS cards...</div>;
  }

  if (completed || reviews.length === 0) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 mx-auto flex items-center justify-center">
          <CheckCircle2 className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white">Review Session Complete!</h2>
        <p className="text-sm text-gray-400">
          All due spaced repetition cards reviewed. Your memory stability and retention have been updated.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition"
        >
          <span>Return to Dashboard</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  const current = reviews[currentIndex];

  return (
    <div className="max-w-2xl mx-auto py-8 space-y-6">
      <div className="flex justify-between items-center text-xs font-mono text-gray-400 border-b border-gray-800 pb-3">
        <span>FSRS Spaced Repetition Session</span>
        <span>Card {currentIndex + 1} of {reviews.length}</span>
      </div>

      {/* Review Card */}
      <div className="p-8 rounded-2xl bg-gray-900/70 border border-gray-800 shadow-xl space-y-6 text-center">
        <div className="space-y-2">
          <span className="text-xs uppercase font-mono text-indigo-400 font-semibold">Active Recall Prompt</span>
          <h2 className="text-3xl font-extrabold text-white">{current.displayName || current.concept}</h2>
        </div>

        <p className="text-base text-gray-300 max-w-lg mx-auto leading-relaxed">
          Explain the operational mechanism, core inputs/outputs, and computational trade-offs of this concept without looking.
        </p>

        {!showAnswer ? (
          <button
            onClick={() => setShowAnswer(true)}
            className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition shadow-lg shadow-indigo-600/30"
          >
            Show Reference Answer
          </button>
        ) : (
          <div className="space-y-6 pt-4 border-t border-gray-800 text-left">
            <div className="p-4 rounded-xl bg-black/40 border border-gray-800 space-y-2 text-sm text-gray-300">
              <span className="text-xs font-mono text-emerald-400 font-bold uppercase">Core Intuition Summary</span>
              <p>Self-attention transforms token embeddings into queries, keys, and values, computing pairwise dot products to softly route contextual representations across sequences.</p>
            </div>

            {/* FSRS 4-Tier Rating Buttons */}
            <div className="space-y-2">
              <span className="text-xs font-mono text-gray-400 uppercase text-center block">Rate your recall ease:</span>
              <div className="grid grid-cols-4 gap-2">
                <button
                  onClick={() => handleGrade(1)}
                  className="p-3 rounded-xl bg-red-950/40 border border-red-800/80 hover:bg-red-900/60 text-red-300 font-semibold text-xs flex flex-col items-center space-y-1 transition"
                >
                  <span>Again</span>
                  <span className="text-[10px] font-mono opacity-70">&lt; 10m</span>
                </button>
                <button
                  onClick={() => handleGrade(2)}
                  className="p-3 rounded-xl bg-amber-950/40 border border-amber-800/80 hover:bg-amber-900/60 text-amber-300 font-semibold text-xs flex flex-col items-center space-y-1 transition"
                >
                  <span>Hard</span>
                  <span className="text-[10px] font-mono opacity-70">1.2d</span>
                </button>
                <button
                  onClick={() => handleGrade(3)}
                  className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/80 hover:bg-indigo-900/60 text-indigo-300 font-semibold text-xs flex flex-col items-center space-y-1 transition"
                >
                  <span>Good</span>
                  <span className="text-[10px] font-mono opacity-70">3.5d</span>
                </button>
                <button
                  onClick={() => handleGrade(4)}
                  className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/80 hover:bg-emerald-900/60 text-emerald-300 font-semibold text-xs flex flex-col items-center space-y-1 transition"
                >
                  <span>Easy</span>
                  <span className="text-[10px] font-mono opacity-70">7d</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}