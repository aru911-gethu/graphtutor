"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, Network, Brain, Cpu, Terminal, Compass, Layers, CheckCircle } from "lucide-react";
import { createGuestDemoSession } from "@/lib/api";

export default function LandingPage() {
  const router = useRouter();
  const [loadingDemo, setLoadingDemo] = useState(false);

  const startDemo = async () => {
    setLoadingDemo(true);
    try {
      await createGuestDemoSession();
      router.push("/lesson/transformers");
    } catch (e) {
      router.push("/lesson/transformers");
    } finally {
      setLoadingDemo(false);
    }
  };

  const themes = [
    { title: "AI & Data Pipelines", icon: Cpu, badge: "AI_PIPELINE", desc: "Tensor shape flows, attention heatmaps, and hyperparameter matrices." },
    { title: "Code & Builders", icon: Terminal, badge: "CODE", desc: "Line-by-line remarks, copyable code, and sandbox execution outputs." },
    { title: "Math & Proofs", icon: Sparkles, badge: "MATH", desc: "KaTeX mathematical formalisms, symbol glossaries, and geometric intuition." },
    { title: "Systems & DevOps", icon: Layers, badge: "SYSTEMS", desc: "Process topology architectures, data journeys, and kernel isolation." },
    { title: "Architectural Decisions", icon: Compass, badge: "DECISIONS", desc: "Trade-off matrices, decision frameworks, and production case studies." },
    { title: "Root Cause Debugging", icon: Brain, badge: "DEBUGGING", desc: "Stack trace diagnostics, failure triage, and before/after diffs." },
  ];

  return (
    <div className="space-y-24 py-8">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-950/60 border border-indigo-700/50 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Personal Adaptive Learning Agent</span>
        </div>

        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
          Master Complex Tech Concepts with <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-emerald-400">Adaptive Visual Themes</span>
        </h1>

        <p className="text-lg sm:text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
          thinknx constructs your personal Neo4j knowledge graph, explains concepts tailored to your depth, quizzes your understanding, and schedules reviews via FSRS spaced repetition.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <button
            onClick={startDemo}
            disabled={loadingDemo}
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white shadow-xl shadow-indigo-600/30 flex items-center justify-center space-x-2 transition"
          >
            <span>{loadingDemo ? "Spinning up session..." : "Try a lesson — No sign-up"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <Link
            href="/onboarding"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gray-800/80 hover:bg-gray-700 font-semibold text-gray-200 border border-gray-700 flex items-center justify-center space-x-2 transition"
          >
            <span>Calibrate My Knowledge</span>
          </Link>
        </div>

        {/* Live Knowledge Graph Preview Card */}
        <div className="mt-12 p-6 rounded-2xl bg-[#0f172a]/80 border border-gray-800 shadow-2xl relative overflow-hidden text-left">
          <div className="flex items-center justify-between pb-4 border-b border-gray-800 text-xs text-gray-400">
            <span className="flex items-center space-x-2 font-mono">
              <Network className="w-4 h-4 text-emerald-400" />
              <span>Neo4j Topological Subgraph • 16 Mastered Seed Concepts</span>
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
              FSRS Retention: 92%
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
            {[
              { name: "Linear Algebra", status: "Mastered", color: "border-emerald-500/40 bg-emerald-950/20 text-emerald-300" },
              { name: "Machine Learning", status: "Mastered", color: "border-emerald-500/40 bg-emerald-950/20 text-emerald-300" },
              { name: "Attention Mechanism", status: "Learning", color: "border-amber-500/40 bg-amber-950/20 text-amber-300" },
              { name: "Transformers", status: "Next Up", color: "border-indigo-500/40 bg-indigo-950/20 text-indigo-300" },
            ].map((node) => (
              <div key={node.name} className={`p-3 rounded-lg border ${node.color} flex flex-col justify-between space-y-2`}>
                <span className="font-semibold text-sm">{node.name}</span>
                <span className="text-xs uppercase tracking-wider font-mono opacity-80">{node.status}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Six Themes Gallery */}
      <section className="space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold text-white">Six Specialized Visual Pedagogies</h2>
          <p className="text-gray-400">Code is not taught like Math. DevOps is not taught like Algorithms.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {themes.map((t) => {
            const Icon = t.icon;
            return (
              <div key={t.badge} className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 hover:border-gray-700 hover:bg-gray-900 transition flex flex-col justify-between space-y-4">
                <div className="space-y-3">
                  <div className="w-10 h-10 rounded-xl bg-gray-800 flex items-center justify-center text-indigo-400">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-bold text-white">{t.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">{t.desc}</p>
                </div>
                <div className="pt-2">
                  <span className="text-xs font-mono px-2 py-1 rounded bg-gray-800/80 text-gray-300 border border-gray-700">
                    {t.badge}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA Footer Banner */}
      <section className="p-8 sm:p-12 rounded-3xl bg-gradient-to-br from-indigo-950/60 via-purple-950/30 to-gray-900 border border-indigo-900/40 text-center space-y-6">
        <h2 className="text-3xl font-bold text-white">Ready to test your comprehension?</h2>
        <p className="text-gray-300 max-w-xl mx-auto">
          Start with zero-sign-up demo mode. Your progress persists in your browser session.
        </p>
        <button
          onClick={startDemo}
          className="px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white shadow-xl shadow-indigo-600/30 inline-flex items-center space-x-2 transition"
        >
          <span>Launch Transformers Lesson</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </section>
    </div>
  );
}