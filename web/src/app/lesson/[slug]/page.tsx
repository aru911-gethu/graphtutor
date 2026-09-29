"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Sparkles, Terminal, CheckCircle2, AlertCircle, RefreshCw, Cpu, BookOpen, Layers, Compass, Brain } from "lucide-react";
import { getAssessmentQuestions, submitAssessmentAnswer } from "@/lib/api";

export default function LessonPage() {
  const params = useParams();
  const slug = (params?.slug as string) || "transformers";

  const [lesson, setLesson] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<any[]>([]);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizResult, setQuizResult] = useState<any>(null);

  useEffect(() => {
    async function loadLessonAndQuiz() {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/lessons/${slug}`);
        if (res.ok) {
          const data = await res.json();
          setLesson(data);
        }

        const qList = await getAssessmentQuestions(slug).catch(() => []);
        setQuestions(qList);
      } catch (err) {
        console.error("Error fetching lesson", err);
      } finally {
        setLoading(false);
      }
    }
    loadLessonAndQuiz();
  }, [slug]);

  const handleQuizSubmit = async () => {
    if (selectedAnswer === null || !questions.length) return;
    const q = questions[0];
    try {
      const res = await submitAssessmentAnswer({
        question_id: q.id,
        concept_slug: slug,
        selected_index: selectedAnswer,
        response_time_ms: 3500,
        current_theta: 0.5,
      });
      setQuizResult(res);
      setQuizSubmitted(true);
    } catch (e) {
      console.error("Quiz submission error", e);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-4">
        <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin mx-auto" />
        <p className="text-gray-400 font-mono text-sm">Streaming structured lesson from Claude & Neo4j...</p>
      </div>
    );
  }

  const currentTheme = lesson?.theme || "ai_pipeline";

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8">
      {/* Back button & header */}
      <div className="flex items-center justify-between">
        <Link href="/dashboard" className="inline-flex items-center space-x-2 text-sm text-gray-400 hover:text-white transition">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
        <span className="px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-700/50 text-indigo-300 font-mono text-xs font-semibold uppercase">
          Theme: {currentTheme}
        </span>
      </div>

      {/* Hero title */}
      <div className="space-y-3">
        <h1 className="text-4xl font-extrabold text-white tracking-tight">
          {lesson?.display_name || slug.replace("-", " ").toUpperCase()}
        </h1>
        <p className="text-lg text-gray-300 leading-relaxed">{lesson?.summary}</p>
      </div>

      {/* Intuition Anchor */}
      {lesson?.intuition_anchor && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/50 via-gray-900 to-gray-900 border border-indigo-800/40 space-y-2">
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            <span>Intuitive Mental Anchor</span>
          </div>
          <p className="text-base text-gray-200 italic leading-relaxed">
            "{lesson.intuition_anchor}"
          </p>
        </div>
      )}

      {/* THEME 1: AI_PIPELINE */}
      {currentTheme === "ai_pipeline" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
            <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm uppercase tracking-wider">
              <Cpu className="w-4 h-4" />
              <span>Tensor Shape Pipeline Steps</span>
            </div>
            <div className="space-y-2">
              {(lesson.tensor_pipeline_steps || []).map((step: string, idx: number) => (
                <div key={idx} className="p-3 rounded-lg bg-black/40 border border-gray-800/80 font-mono text-xs text-gray-300 flex items-start space-x-3">
                  <span className="text-indigo-400 font-bold">{idx + 1}.</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>

          {lesson.matrix_intuition && (
            <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-2">
              <h3 className="font-bold text-white text-base">Attention Matrix Intuition</h3>
              <p className="text-sm text-gray-300 leading-relaxed">{lesson.matrix_intuition}</p>
            </div>
          )}
        </div>
      )}

      {/* THEME 2: MATH */}
      {currentTheme === "math" && (
        <div className="space-y-6">
          {lesson.formula_latex && (
            <div className="p-8 rounded-2xl bg-black/50 border border-indigo-900/50 text-center space-y-3">
              <span className="text-xs font-mono uppercase text-indigo-400">Formal Mathematical Definition</span>
              <div className="text-2xl font-mono text-white py-2">{lesson.formula_latex}</div>
            </div>
          )}

          {lesson.symbol_glossary && (
            <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-3">
              <h3 className="font-bold text-white text-base">Mathematical Symbols</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {lesson.symbol_glossary.map((sym: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-lg bg-black/30 border border-gray-800 space-y-1">
                    <span className="font-mono text-indigo-400 font-bold">{sym.symbol}</span> — <span className="text-sm text-white font-medium">{sym.name}</span>
                    <p className="text-xs text-gray-400">{sym.meaning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* THEME 3: SYSTEMS */}
      {currentTheme === "systems" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm uppercase tracking-wider">
              <Layers className="w-4 h-4" />
              <span>Architectural Data Journey</span>
            </div>
            <div className="space-y-2">
              {(lesson.data_journey_steps || []).map((step: string, idx: number) => (
                <div key={idx} className="p-3 rounded-lg bg-black/40 border border-gray-800 text-xs text-gray-300 font-mono flex items-start space-x-3">
                  <span className="text-emerald-400 font-bold">{idx + 1}.</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* INLINE DIAGNOSTIC QUIZ */}
      {questions.length > 0 && (
        <div className="p-8 rounded-2xl bg-gradient-to-b from-gray-900 to-[#0e1628] border border-indigo-900/40 space-y-6">
          <div className="flex items-center justify-between border-b border-gray-800 pb-4">
            <div className="flex items-center space-x-2">
              <BookOpen className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-lg text-white">Diagnostic Understanding Test</h3>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
              Bloom: {questions[0].blooms_level}
            </span>
          </div>

          <p className="text-base text-gray-200 font-medium">{questions[0].prompt}</p>

          <div className="space-y-3">
            {questions[0].options.map((opt: string, optIdx: number) => (
              <button
                key={optIdx}
                disabled={quizSubmitted}
                onClick={() => setSelectedAnswer(optIdx)}
                className={`w-full text-left p-4 rounded-xl border text-sm transition flex items-start space-x-3 ${
                  quizSubmitted
                    ? optIdx === questions[0].correct_index
                      ? "border-emerald-500 bg-emerald-950/40 text-emerald-200"
                      : optIdx === selectedAnswer
                      ? "border-red-500 bg-red-950/40 text-red-200"
                      : "border-gray-800 bg-gray-900/30 text-gray-400"
                    : selectedAnswer === optIdx
                    ? "border-indigo-500 bg-indigo-950/60 text-white font-medium"
                    : "border-gray-800 bg-gray-900/40 text-gray-300 hover:border-gray-700"
                }`}
              >
                <span className="w-5 h-5 rounded-full border border-gray-700 text-xs flex items-center justify-center font-mono shrink-0">
                  {String.fromCharCode(65 + optIdx)}
                </span>
                <span>{opt}</span>
              </button>
            ))}
          </div>

          {!quizSubmitted ? (
            <button
              onClick={handleQuizSubmit}
              disabled={selectedAnswer === null}
              className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition disabled:opacity-50"
            >
              Submit Answer & Update Graph Mastery
            </button>
          ) : (
            <div className="p-4 rounded-xl bg-black/40 border border-gray-800 space-y-3">
              <div className="flex items-center space-x-2">
                {quizResult?.is_correct ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-amber-400" />
                )}
                <span className="font-bold text-sm text-white">
                  {quizResult?.is_correct ? "Correct! Cognitive ability increased." : "Misconception detected."}
                </span>
              </div>
              <p className="text-xs text-gray-300">{questions[0].explanation}</p>
              <div className="flex justify-between items-center text-xs font-mono text-gray-400 pt-2 border-t border-gray-800">
                <span>Updated Latent Ability (θ): {quizResult?.new_theta}</span>
                <span className="text-emerald-400 font-bold uppercase">Tag: {quizResult?.skill_tag}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}