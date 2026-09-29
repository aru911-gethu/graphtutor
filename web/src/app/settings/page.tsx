"use client";

import { useEffect, useState } from "react";
import { getUserProfile } from "@/lib/api";
import { Send, CheckCircle2, ShieldCheck, Sliders, Smartphone } from "lucide-react";

export default function SettingsPage() {
  const [profile, setProfile] = useState<any>(null);
  const [level, setLevel] = useState("intermediate");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getUserProfile().then((data) => {
      setProfile(data);
      if (data.explanation_level) setLevel(data.explanation_level);
    }).catch(() => {});
  }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto py-8 space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-extrabold text-white">Learner Settings</h1>
        <p className="text-sm text-gray-400">Configure your learning profile, depth preferences, and Telegram notifications.</p>
      </div>

      {/* Depth level */}
      <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
        <div className="flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <h2 className="font-bold text-lg text-white">Pedagogical Explanation Level</h2>
        </div>
        <p className="text-xs text-gray-400">Controls technical density and mathematical rigor of AI-generated lessons.</p>

        <div className="grid grid-cols-3 gap-3">
          {["beginner", "intermediate", "advanced"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevel(lvl)}
              className={`p-3 rounded-xl border text-sm font-semibold capitalize transition ${
                level === lvl
                  ? "border-indigo-500 bg-indigo-950/60 text-white"
                  : "border-gray-800 bg-gray-900/40 text-gray-400 hover:border-gray-700"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Telegram Link */}
      <div className="p-6 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-4">
        <div className="flex items-center space-x-2">
          <Smartphone className="w-5 h-5 text-indigo-400" />
          <h2 className="font-bold text-lg text-white">Telegram Companion Link</h2>
        </div>
        <p className="text-xs text-gray-400">
          Receive daily spaced repetition reminders directly via the Telegram bot.
        </p>

        <div className="p-4 rounded-xl bg-black/40 border border-gray-800 flex items-center justify-between text-xs font-mono">
          <div className="flex items-center space-x-2 text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
            <span>Telegram bot: @graphtutor_bot (create it in BotFather, then set TELEGRAM_BOT_TOKEN)</span>
          </div>
          <a
            href="https://t.me"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition"
          >
            Open in Telegram
          </a>
        </div>
      </div>

      <button
        onClick={handleSave}
        className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition flex items-center justify-center space-x-2"
      >
        <span>{saved ? "Preferences Saved!" : "Save Preferences"}</span>
      </button>
    </div>
  );
}