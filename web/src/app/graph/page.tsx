"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getGraphData } from "@/lib/api";
import { Network, ArrowRight, BookOpen, Layers, CheckCircle2 } from "lucide-react";

export default function GraphCanvasPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cyInstance: any = null;

    async function initGraph() {
      try {
        const cytoscape = (await import("cytoscape")).default;
        const graphData = await getGraphData();
        setStats(graphData.summary);

        if (!containerRef.current) return;

        cyInstance = cytoscape({
          container: containerRef.current,
          elements: graphData.elements,
          style: [
            {
              selector: "node",
              style: {
                label: "data(label)",
                color: "#f3f4f6",
                "font-size": "11px",
                "text-valign": "bottom",
                "text-margin-y": 6,
                width: "data(size)",
                height: "data(size)",
                "background-color": (ele: any) => {
                  const status = ele.data("status");
                  if (status === "mastered") return "#10b981"; // emerald
                  if (status === "learning") return "#6366f1"; // indigo
                  if (status === "decaying") return "#f59e0b"; // amber
                  return "#374151"; // gray locked
                },
                "border-width": 2,
                "border-color": "#1f2937",
              },
            },
            {
              selector: "edge",
              style: {
                width: 2,
                "line-color": "#334155",
                "target-arrow-color": "#475569",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
                opacity: 0.6,
              },
            },
            {
              selector: "node:selected",
              style: {
                "border-color": "#ffffff",
                "border-width": 4,
              },
            },
          ],
          layout: {
            name: "cose",
            idealEdgeLength: 100,
            nodeOverlap: 20,
            padding: 40,
            animate: false,
          },
        });

        cyInstance.on("tap", "node", (evt: any) => {
          setSelectedNode(evt.target.data());
        });

        cyInstance.on("tap", (evt: any) => {
          if (evt.target === cyInstance) {
            setSelectedNode(null);
          }
        });
      } catch (e) {
        console.error("Cytoscape init error", e);
      } finally {
        setLoading(false);
      }
    }

    initGraph();

    return () => {
      if (cyInstance) {
        cyInstance.destroy();
      }
    };
  }, []);

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
      {/* Canvas Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-gray-900/60 border border-gray-800">
        <div className="flex items-center space-x-3">
          <Network className="w-5 h-5 text-indigo-400" />
          <h1 className="font-bold text-white text-base">Interactive Knowledge Canvas</h1>
        </div>

        <div className="flex items-center space-x-4 text-xs font-mono">
          <span className="flex items-center space-x-1.5 text-emerald-400">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>Mastered ({stats?.mastered || 6})</span>
          </span>
          <span className="flex items-center space-x-1.5 text-indigo-400">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
            <span>Learning ({stats?.learning || 4})</span>
          </span>
          <span className="flex items-center space-x-1.5 text-gray-400">
            <span className="w-2.5 h-2.5 rounded-full bg-gray-600" />
            <span>Locked ({stats?.locked || 6})</span>
          </span>
        </div>
      </div>

      {/* Main Graph & Slide Sheet */}
      <div className="flex-1 relative rounded-2xl overflow-hidden border border-gray-800 bg-[#080d18]">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#080d18] z-10 text-gray-400 font-mono text-sm">
            Rendering Neo4j Cytoscape DAG...
          </div>
        )}

        <div ref={containerRef} className="w-full h-full" />

        {/* Selected Node Sheet */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-80 p-5 rounded-2xl bg-gray-900/95 backdrop-blur border border-gray-700 shadow-2xl space-y-4 z-20">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-mono uppercase text-indigo-400 font-semibold">{selectedNode.domain}</span>
                <h3 className="text-xl font-bold text-white">{selectedNode.label}</h3>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded uppercase font-mono font-bold ${
                selectedNode.status === "mastered" ? "bg-emerald-950 text-emerald-300 border border-emerald-800" : "bg-indigo-950 text-indigo-300 border border-indigo-800"
              }`}>
                {selectedNode.status}
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono text-gray-300">
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span>Mastery Level:</span>
                <span className="text-white font-bold">{Math.round(selectedNode.mastery * 100)}%</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span>Latent Ability (θ):</span>
                <span className="text-white font-bold">{selectedNode.theta}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span>Topological Complexity:</span>
                <span className="text-white font-bold">{selectedNode.complexity}</span>
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <Link
                href={`/lesson/${selectedNode.id}`}
                className="flex-1 py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white text-center transition flex items-center justify-center space-x-1"
              >
                <span>Open Lesson</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/review"
                className="py-2 px-3 rounded-lg bg-gray-800 hover:bg-gray-700 font-semibold text-xs text-gray-200 text-center transition"
              >
                Review
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}