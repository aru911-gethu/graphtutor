"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, ArrowRight, Target, Brain, Sparkles } from "lucide-react";
import { createGuestDemoSession } from "@/lib/api";

const GOALS = [
  { id: "transformers", title: "Master Transformers & Attention", domain: "Deep Learning", prereqs: "Linear Algebra, Calculus, Python" },
  { id: "rag", title: "Build Production RAG Systems", domain: "AI Engineering", prereqs: "Vector DBs, Embeddings, LLMs" },
  { id: "ai-agents", title: "Architect Autonomous AI Agents", domain: "Multi-Agent Systems", prereqs: "LLM Tool Use, Knowledge Graphs" },
  { id: "docker", title: "Containerization & Cloud Native", domain: "DevOps / Infra", prereqs: "Linux Namespaces, cgroups" },
];

const CALIBRATION_QUESTIONS = [
  {
    q: "How familiar are you with matrix multiplications and vector dot products?",
    options: ["Never seen them", "Remember high-school basics", "Use NumPy/PyTorch regularly", "Mastered geometric linear maps"],
  },
  {
    q: "Have you ever trained or fine-tuned an attention-based neural network?",
    options: ["No, completely new", "Used HuggingFace pipelines", "Written training loops from scratch", "Implemented custom self-attention CUDA kernels"],
  },
  {
    q: "What is your primary learning modality preference?",
    options: ["Visual pipelines and data flow diagrams", "Mathematical formalisms and equations", "Hands-on runnable code blocks", "Architectural trade-off case studies"],
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [selectedGoal, setSelectedGoal] = useState("transformers");
  const [step, setStep] = useState<"goal" | "quiz" | "ready">("goal");
  const [answers, setAnswers] = useState<number[]>([1, 1, 0]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFinish = async () => {
    setIsSubmitting(true);
    try {
      await createGuestDemoSession();
      router.push(`/dashboard?goal=${selectedGoal}`);
    } catch {
      router.push(`/dashboard?goal=${selectedGoal}`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-10 space-y-8">
      {/* Progress Indicator */}
      <div className="flex items-center justify-between text-xs font-mono text-gray-400 border-b border-gray-800 pb-4">
        <span className={step === "goal" ? "text-indigo-400 font-bold" : ""}>1. Choose Learning Goal</span>
        <span className={step === "quiz" ? "text-indigo-400 font-bold" : ""}>2. Knowledge Calibration</span>
        <span className={step === "ready" ? "text-indigo-400 font-bold" : ""}>3. Seed Graph</span>
      </div>

      {/* Step 1: Goal selection */}
      {step === "goal" && (
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold text-white">What do you want to master?</h1>
            <p className="text-gray-400">graphtutor will discover your prerequisite knowledge gaps and build a personalized path.</p>
          </div>

          <div className="space-y-3">
            {GOALS.map((g) => (
              <div
                key={g.id}
                onClick={() => setSelectedGoal(g.id)}
                className={`p-4 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                  selectedGoal === g.id
                    ? "border-indigo-500 bg-indigo-950/40 text-white"
                    : "border-gray-800 bg-gray-900/40 text-gray-300 hover:border-gray-700"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Target className="w-4 h-4 text-indigo-400" />
                    <span className="font-bold text-base">{g.title}</span>
                  </div>
                  <p className="text-xs text-gray-400">Prerequisites: {g.prereqs}</p>
                </div>
                <div className="w-5 h-5 rounded-full border border-gray-700 flex items-center justify-center">
                  {selectedGoal === g.id && <div className="w-3 h-3 rounded-full bg-indigo-500" />}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => setStep("quiz")}
            className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white flex items-center justify-center space-x-2 transition"
          >
            <span>Proceed to Calibration</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Step 2: Calibration quiz */}
      {step === "quiz" && (
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold text-white">Calibrate Baseline Knowledge</h1>
            <p className="text-gray-400">Answer honestly so the adaptive explainer starts at the optimal pedagogical level.</p>
          </div>

          <div className="space-y-6">
            {CALIBRATION_QUESTIONS.map((cq, idx) => (
              <div key={idx} className="p-5 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
                <span className="text-sm font-semibold text-gray-200">
                  {idx + 1}. {cq.q}
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
                  {cq.options.map((opt, optIdx) => (
                    <button
                      key={optIdx}
                      onClick={() => {
                        const next = [...answers];
                        next[idx] = optIdx;
                        setAnswers(next);
                      }}
                      className={`text-left text-xs p-3 rounded-lg border transition ${
                        answers[idx] === optIdx
                          ? "border-indigo-500 bg-indigo-950/60 text-white font-medium"
                          : "border-gray-800 bg-gray-900/30 text-gray-400 hover:border-gray-700"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => setStep("ready")}
            className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white flex items-center justify-center space-x-2 transition"
          >
            <span>Generate Topological Learning Path</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Step 3: Ready */}
      {step === "ready" && (
        <div className="p-8 rounded-2xl bg-gray-900/60 border border-gray-800 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 mx-auto flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">Knowledge Graph Initialized</h2>
            <p className="text-gray-400 text-sm max-w-md mx-auto">
              We mapped your baseline across linear algebra, calculus, and neural networks. Your first recommended milestone is ready.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-black/40 border border-gray-800 text-left font-mono text-xs space-y-2">
            <div className="flex justify-between text-gray-400">
              <span>Target Goal:</span>
              <span className="text-indigo-400">{selectedGoal}</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Discovered Prerequisites:</span>
              <span className="text-emerald-400">3 Foundations Validated</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Next Recommended Step:</span>
              <span className="text-amber-400">attention-mechanism</span>
            </div>
          </div>

          <button
            onClick={handleFinish}
            disabled={isSubmitting}
            className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white flex items-center justify-center space-x-2 transition"
          >
            <span>{isSubmitting ? "Loading Dashboard..." : "Enter My Dashboard"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}