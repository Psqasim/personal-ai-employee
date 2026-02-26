"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import { GlassSpinner } from "@/components/LoadingStates";

interface BriefingMeta {
  filename: string;
  date: string;
  weekStart?: string;
  weekEnd?: string;
  totalCompleted?: number;
  apiCost?: number;
  pendingApprovals?: number;
  generatedAt?: string;
}

export default function BriefingsPage() {
  const { data: session, status } = useSession();
  const [briefings, setBriefings] = useState<BriefingMeta[]>([]);
  const [latest, setLatest] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedContent, setSelectedContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const userRole = (session?.user as any)?.role;
  const isAdmin = userRole === "admin";

  const fetchBriefings = async () => {
    try {
      const res = await fetch("/api/briefings");
      if (!res.ok) return;
      const data = await res.json();
      setBriefings(data.briefings || []);
      setLatest(data.latest || null);
      if (!selected && data.briefings?.length > 0) {
        setSelected(data.briefings[0].filename);
        setSelectedContent(data.latest);
      }
      setLastRefresh(new Date());
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (status !== "authenticated") return;
    fetchBriefings();
    const interval = setInterval(fetchBriefings, 30_000);
    return () => clearInterval(interval);
  }, [status]);

  const handleSelectBriefing = async (filename: string) => {
    setSelected(filename);
    if (filename === briefings[0]?.filename) {
      setSelectedContent(latest);
      return;
    }
    setSelectedContent(null);
  };

  if (status === "loading" || loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <GlassSpinner size={48} label="Loading briefings..." />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center py-24 px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-10 text-center max-w-md"
        >
          <div className="text-5xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Admin Access Required</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
            CEO Briefings contain confidential business information and are restricted to administrators.
          </p>
          <motion.a
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            href="/dashboard/status"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-semibold rounded-xl shadow-lg shadow-blue-500/25"
          >
            🏥 Go to MCP Health
          </motion.a>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="px-6 py-6 space-y-6">

      {/* ── Header ───────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-wrap items-start justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-extrabold bg-gradient-to-r from-amber-400 via-orange-500 to-rose-500 bg-clip-text text-transparent">
            CEO Briefings
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Weekly executive reports — auto-generated every Sunday at 23:00
          </p>
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.15 }}
          className="flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500 glass-card px-4 py-2 rounded-full shrink-0"
        >
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-lg shadow-emerald-500/50" />
          <span>Auto-refresh 30s · Last: {lastRefresh.toLocaleTimeString()}</span>
        </motion.div>
      </motion.div>

      {briefings.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-16 text-center"
        >
          <div className="text-5xl mb-4">📋</div>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No briefings yet
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Briefings are generated every Sunday at 23:00 automatically.
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 font-mono glass-card rounded-xl px-4 py-2 inline-block">
            python scripts/generate_ceo_briefing.py
          </p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

          {/* ── Briefing List (left panel) ───────────────────────────── */}
          <div className="lg:col-span-4 space-y-2">
            <div className="flex items-center gap-2 mb-3 px-1">
              <div className="w-1 h-5 rounded-full bg-gradient-to-b from-amber-400 to-orange-600" />
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Reports ({briefings.length})
              </span>
            </div>
            {briefings.map((b, index) => (
              <motion.button
                key={b.filename}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => handleSelectBriefing(b.filename)}
                className={`w-full text-left p-4 rounded-2xl transition-all duration-200 ${
                  selected === b.filename
                    ? "glass-card border-cyan-500/30 dark:border-cyan-500/30 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/20"
                    : "glass-card hover:shadow-lg hover:shadow-white/5"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className={`text-sm font-semibold ${
                      selected === b.filename
                        ? "text-cyan-500 dark:text-cyan-400"
                        : "text-gray-900 dark:text-white"
                    }`}>
                      {b.date}
                    </p>
                    {b.weekStart && b.weekEnd && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        {b.weekStart} → {b.weekEnd}
                      </p>
                    )}
                  </div>
                  {b === briefings[0] && (
                    <span className="shrink-0 text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full font-bold border border-emerald-500/20 uppercase tracking-wider shadow-sm shadow-emerald-500/10">
                      Latest
                    </span>
                  )}
                </div>
                <div className="mt-2.5 flex gap-3 text-xs text-gray-600 dark:text-gray-400">
                  {b.totalCompleted !== undefined && (
                    <span className="flex items-center gap-1">
                      <span className="text-emerald-400">✅</span> {b.totalCompleted} tasks
                    </span>
                  )}
                  {b.apiCost !== undefined && (
                    <span className="flex items-center gap-1">
                      <span className="text-amber-400">💰</span> ${b.apiCost.toFixed(4)}
                    </span>
                  )}
                  {b.pendingApprovals !== undefined && b.pendingApprovals > 0 && (
                    <span className="flex items-center gap-1 text-amber-500">
                      ⏳ {b.pendingApprovals} pending
                    </span>
                  )}
                </div>
              </motion.button>
            ))}
          </div>

          {/* ── Briefing Content (right panel) ──────────────────────── */}
          <div className="lg:col-span-8">
            <AnimatePresence mode="wait">
              {selected === briefings[0]?.filename && selectedContent ? (
                <motion.div
                  key="content"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.3 }}
                  className="glass-card rounded-2xl overflow-hidden"
                >
                  {/* Content header bar */}
                  <div className="px-6 py-3 border-b border-white/5 flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Full Report
                    </span>
                    <span className="text-[10px] text-gray-500 dark:text-gray-500 glass-card px-2 py-0.5 rounded-full">
                      {briefings[0]?.date}
                    </span>
                  </div>
                  <div className="p-6">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <MarkdownRenderer content={selectedContent} />
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="glass-card rounded-2xl p-16 text-center"
                >
                  <div className="text-4xl mb-3">📄</div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Select the latest briefing to view full content.
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Historical briefing content is stored in vault/Briefings/
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  );
}

/** Simple markdown renderer for briefing content */
function MarkdownRenderer({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("# ")) {
      elements.push(
        <h1 key={i} className="text-xl font-bold text-gray-900 dark:text-white mt-4 mb-2">
          {line.slice(2)}
        </h1>
      );
    } else if (line.startsWith("## ")) {
      elements.push(
        <h2 key={i} className="text-base font-semibold text-gray-800 dark:text-gray-200 mt-5 mb-2 border-b border-white/10 pb-1">
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith("### ")) {
      elements.push(
        <h3 key={i} className="text-sm font-semibold text-gray-700 dark:text-gray-300 mt-3 mb-1">
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith("---")) {
      elements.push(<hr key={i} className="border-white/10 my-3" />);
    } else if (line.startsWith("| ")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      elements.push(<MarkdownTable key={`table-${i}`} lines={tableLines} />);
      continue;
    } else if (line.startsWith("- ")) {
      elements.push(
        <li key={i} className="text-sm text-gray-700 dark:text-gray-300 ml-4 list-disc">
          <InlineMarkdown text={line.slice(2)} />
        </li>
      );
    } else if (/^\d+\.\s/.test(line)) {
      elements.push(
        <li key={i} className="text-sm text-gray-700 dark:text-gray-300 ml-4 list-decimal">
          <InlineMarkdown text={line.replace(/^\d+\.\s/, "")} />
        </li>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} className="my-1" />);
    } else if (line.startsWith("*") && line.endsWith("*")) {
      elements.push(
        <p key={i} className="text-xs text-gray-400 dark:text-gray-500 italic mt-2">
          {line.replace(/^\*|\*$/g, "")}
        </p>
      );
    } else if (line.trim()) {
      elements.push(
        <p key={i} className="text-sm text-gray-700 dark:text-gray-300">
          <InlineMarkdown text={line} />
        </p>
      );
    }

    i++;
  }

  return <div className="space-y-0.5">{elements}</div>;
}

function MarkdownTable({ lines }: { lines: string[] }) {
  const rows = lines
    .filter((l) => !l.match(/^\|[-|: ]+\|$/))
    .map((l) =>
      l.slice(1, -1).split("|").map((c) => c.trim())
    );

  if (rows.length === 0) return null;
  const [header, ...body] = rows;

  return (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full text-xs glass-card rounded-xl overflow-hidden">
        <thead className="bg-white/5">
          <tr>
            {header.map((h, j) => (
              <th key={j} className="px-3 py-2 text-left font-semibold text-gray-700 dark:text-gray-300">
                <InlineMarkdown text={h} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? "bg-white/[0.02]" : "bg-white/[0.04]"}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-1.5 text-gray-600 dark:text-gray-400 border-t border-white/5">
                  <InlineMarkdown text={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function InlineMarkdown({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return (
    <>
      {parts.map((p, i) => {
        if (p.startsWith("**") && p.endsWith("**")) {
          return <strong key={i} className="font-semibold text-gray-900 dark:text-white">{p.slice(2, -2)}</strong>;
        }
        if (p.startsWith("`") && p.endsWith("`")) {
          return <code key={i} className="font-mono text-xs bg-white/10 px-1 rounded">{p.slice(1, -1)}</code>;
        }
        return <span key={i}>{p}</span>;
      })}
    </>
  );
}
