"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Clock, Flame, BookOpen, ArrowRight, Activity, Award, ShieldAlert, Sparkles } from "lucide-react";
import { getDueReviews, getLearningPath, getSkillReport } from "@/lib/api";

export default function DashboardPage() {
  const [reviewsDue, setReviewsDue] = useState<any[]>([]);
  const [learningPath, setLearningPath] = useState<any>(null);
  const [skillReport, setSkillReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [reviews, path, report] = await Promise.all([
          getDueReviews().catch(() => []),
          getLearningPath("transformers").catch(() => null),
          getSkillReport().catch(() => null),
        ]);
        setReviewsDue(reviews);
        setLearningPath(path);
        setSkillReport(report);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  return (
    <div className="space-y-8 py-4">
      {/* Top Stat Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs uppercase tracking-wider text-gray-400 font-mono">Reviews Due</span>
            <p className="text-3xl font-extrabold text-amber-400">{reviewsDue.length}</p>
          </div>
          <div className="p-3 rounded-xl bg-amber-950/40 text-amber-400">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs uppercase tracking-wider text-gray-400 font-mono">Current Streak</span>
            <p className="text-3xl font-extrabold text-orange-400">5 Days</p>
          </div>
          <div className="p-3 rounded-xl bg-orange-950/40 text-orange-400">
            <Flame className="w-6 h-6" />
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs uppercase tracking-wider text-gray-400 font-mono">Cognitive Ability (θ)</span>
            <p className="text-3xl font-extrabold text-indigo-400">{skillReport?.overall_ability || 76}%</p>
          </div>
          <div className="p-3 rounded-xl bg-indigo-950/40 text-indigo-400">
            <Award className="w-6 h-6" />
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs uppercase tracking-wider text-gray-400 font-mono">Mastered Concepts</span>
            <p className="text-3xl font-extrabold text-emerald-400">{skillReport?.skill_breakdown?.mastered || 6}</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-950/40 text-emerald-400">
            <Activity className="w-6 h-6" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Next Up & Learning Path */}
        <div className="lg:col-span-2 space-y-6">
          {/* Next Up Hero Card */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/70 via-gray-900 to-gray-900 border border-indigo-900/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-900 text-indigo-300 font-semibold uppercase">
                Next Recommended Concept
              </span>
              <h2 className="text-2xl font-bold text-white">
                {learningPath?.next_step?.displayName || "Attention Mechanism"}
              </h2>
              <p className="text-sm text-gray-400 max-w-md">
                Prerequisites met (Linear Algebra & Deep Learning). Learn query-key-value projections and affinity matrices.
              </p>
            </div>
            <Link
              href={`/lesson/${learningPath?.next_step?.concept || "attention-mechanism"}`}
              className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white shadow-lg shadow-indigo-600/30 flex items-center space-x-2 transition shrink-0"
            >
              <span>Learn Now</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Goal Roadmap Steps */}
          <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-lg text-white">Target Goal: Transformers</h3>
              <span className="text-xs text-gray-400 font-mono">4-Step Prerequisite Chain</span>
            </div>

            <div className="space-y-3">
              {(learningPath?.steps || [
                { concept: "linear-algebra", displayName: "Linear Algebra", status: "mastered", complexity: 0.4 },
                { concept: "machine-learning", displayName: "Machine Learning", status: "mastered", complexity: 0.5 },
                { concept: "attention-mechanism", displayName: "Attention Mechanism", status: "in_progress", complexity: 0.7 },
                { concept: "transformers", displayName: "Transformers", status: "locked", complexity: 0.7 },
              ]).map((step: any, idx: number) => (
                <div
                  key={step.concept}
                  className="p-3.5 rounded-xl border border-gray-800 bg-gray-900/40 flex items-center justify-between text-sm"
                >
                  <div className="flex items-center space-x-3">
                    <span className="w-6 h-6 rounded-full bg-gray-800 text-gray-400 font-mono text-xs flex items-center justify-center font-bold">
                      {idx + 1}
                    </span>
                    <span className="font-semibold text-gray-200">{step.displayName}</span>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-mono uppercase font-semibold ${
                        step.status === "mastered"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : step.status === "in_progress"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-gray-800 text-gray-400"
                      }`}
                    >
                      {step.status}
                    </span>
                    <Link
                      href={`/lesson/${step.concept}`}
                      className="text-gray-400 hover:text-white p-1 transition"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Due Reviews & Radar Axes */}
        <div className="space-y-6">
          {/* Due Reviews Card */}
          <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-lg text-white">Spaced Repetition</h3>
              <Link href="/review" className="text-xs text-indigo-400 hover:underline">
                Review All →
              </Link>
            </div>

            {reviewsDue.length === 0 ? (
              <p className="text-sm text-gray-400 py-4">No reviews currently due! Everything is fresh in memory.</p>
            ) : (
              <div className="space-y-2">
                {reviewsDue.map((rev) => (
                  <div
                    key={rev.concept}
                    className="p-3 rounded-lg border border-amber-900/40 bg-amber-950/20 flex items-center justify-between"
                  >
                    <div>
                      <p className="font-semibold text-sm text-white">{rev.displayName || rev.concept}</p>
                      <p className="text-xs text-amber-400/80 font-mono">Retrievability: {Math.round((rev.retrievability || 0.6) * 100)}%</p>
                    </div>
                    <Link
                      href="/review"
                      className="px-3 py-1 rounded bg-amber-600 hover:bg-amber-500 font-semibold text-xs text-white transition"
                    >
                      Review
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Radar Domain Competency */}
          <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
            <h3 className="font-bold text-lg text-white">Competency Breakdown</h3>
            <div className="space-y-3">
              {(skillReport?.radar_chart || [
                { domain: "Deep Learning", score: 78 },
                { domain: "Mathematics", score: 92 },
                { domain: "Infrastructure", score: 65 },
                { domain: "Programming", score: 88 },
              ]).map((axis: any) => (
                <div key={axis.domain} className="space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-gray-300">{axis.domain}</span>
                    <span className="text-indigo-400 font-bold">{axis.score}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full"
                      style={{ width: `${axis.score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}