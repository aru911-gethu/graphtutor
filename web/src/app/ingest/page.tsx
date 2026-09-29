"use client";

import { useState } from "react";
import { ingestContent } from "@/lib/api";
import { FileText, Link2, Image, Sparkles, CheckCircle2, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function IngestPage() {
  const [tab, setTab] = useState<"text" | "url" | "image">("text");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleIngest = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      const res = await ingestContent(tab, content);
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-extrabold text-white">Add Knowledge to Your Graph</h1>
        <p className="text-gray-400 text-sm">
          Paste articles, URLs, or architectural diagrams. graphtutor decomposes them into atomic concepts with prerequisite dependencies.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800 space-x-4">
        {[
          { id: "text", label: "Raw Text / Notes", icon: FileText },
          { id: "url", label: "Web Article / GitHub", icon: Link2 },
          { id: "image", label: "Architecture Diagram", icon: Image },
        ].map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => {
                setTab(t.id as any);
                setResult(null);
              }}
              className={`pb-3 px-2 font-medium text-sm flex items-center space-x-2 border-b-2 transition ${
                tab === t.id
                  ? "border-indigo-500 text-white"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Input Form */}
      <div className="space-y-4">
        {tab === "text" && (
          <textarea
            rows={6}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste text notes, tutorial excerpts, or documentation paragraphs..."
            className="w-full p-4 rounded-xl bg-gray-900/60 border border-gray-800 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm"
          />
        )}

        {tab === "url" && (
          <input
            type="url"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="https://arxiv.org/abs/... or https://github.com/..."
            className="w-full p-4 rounded-xl bg-gray-900/60 border border-gray-800 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm"
          />
        )}

        {tab === "image" && (
          <div className="p-8 border-2 border-dashed border-gray-800 rounded-2xl text-center space-y-3 bg-gray-900/20">
            <Image className="w-8 h-8 text-gray-500 mx-auto" />
            <p className="text-sm text-gray-400">Upload screenshot or architecture diagram</p>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  const reader = new FileReader();
                  reader.onloadend = () => setContent(reader.result as string);
                  reader.readAsDataURL(file);
                }
              }}
              className="text-xs text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500"
            />
          </div>
        )}

        <button
          onClick={handleIngest}
          disabled={loading || !content}
          className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition disabled:opacity-50 flex items-center justify-center space-x-2"
        >
          <Sparkles className="w-4 h-4" />
          <span>{loading ? "Extracting Atomic Concepts..." : "Extract & Add to Graph"}</span>
        </button>
      </div>

      {/* Resulting Chips */}
      {result && (
        <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5" />
            <span>Extracted {result.concepts.length} Atomic Concepts</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {result.concepts.map((c: any) => (
              <div key={c.name} className="p-4 rounded-xl bg-black/40 border border-gray-800 space-y-2">
                <div className="flex justify-between items-start">
                  <span className="font-bold text-sm text-white">{c.displayName || c.name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300">
                    Complexity: {c.complexity}
                  </span>
                </div>
                {c.prerequisites?.length > 0 && (
                  <p className="text-xs text-gray-400">
                    Prereqs: {c.prerequisites.join(", ")}
                  </p>
                )}
                <Link
                  href={`/lesson/${c.name}`}
                  className="inline-flex items-center space-x-1 text-xs text-indigo-400 hover:underline pt-1"
                >
                  <span>Learn Concept</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}