"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

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
    // For non-latest, we only have the list metadata
    setSelectedContent(null);
  };

  if (status === "loading" || loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

      {/* ─── Header ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            📊 CEO Briefings
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Weekly executive reports — auto-generated every Sunday at 23:00
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span>Auto-refresh 30s · Last: {lastRefresh.toLocaleTimeString()}</span>
        </div>
      </div>

      {briefings.length === 0 ? (
        /* ─── Empty state ─────────────────────────────────────────────── */
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <div className="text-5xl mb-4">📋</div>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No briefings yet
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Briefings are generated every Sunday at 23:00 automatically.
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 font-mono bg-gray-50 dark:bg-gray-900 rounded-lg px-4 py-2 inline-block">
            python scripts/generate_ceo_briefing.py
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* ─── Sidebar: Briefing list ──────────────────────────────── */}
          <div className="lg:col-span-1 space-y-2">
            {briefings.map((b) => (
              <button
                key={b.filename}
                onClick={() => handleSelectBriefing(b.filename)}
                className={`w-full text-left p-4 rounded-xl border transition-all ${
                  selected === b.filename
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400"
                    : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {b.date}
                    </p>
                    {b.weekStart && b.weekEnd && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        {b.weekStart} → {b.weekEnd}
                      </p>
                    )}
                  </div>
                  {b === briefings[0] && (
                    <span className="shrink-0 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded-full font-medium">
                      Latest
                    </span>
                  )}
                </div>
                <div className="mt-2 flex gap-3 text-xs text-gray-600 dark:text-gray-400">
                  {b.totalCompleted !== undefined && (
                    <span>✅ {b.totalCompleted} tasks</span>
                  )}
                  {b.apiCost !== undefined && (
                    <span>💰 ${b.apiCost.toFixed(4)}</span>
                  )}
                  {b.pendingApprovals !== undefined && b.pendingApprovals > 0 && (
                    <span className="text-yellow-600 dark:text-yellow-400">
                      ⏳ {b.pendingApprovals} pending
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* ─── Main: Briefing content ──────────────────────────────── */}
          <div className="lg:col-span-2">
            {selected === briefings[0]?.filename && selectedContent ? (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <MarkdownRenderer content={selectedContent} />
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
                <div className="text-4xl mb-3">📄</div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Select the latest briefing to view full content.
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  Historical briefing content is stored in vault/Briefings/
                </p>
              </div>
            )}
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
        <h2 key={i} className="text-base font-semibold text-gray-800 dark:text-gray-200 mt-5 mb-2 border-b border-gray-200 dark:border-gray-700 pb-1">
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
      elements.push(<hr key={i} className="border-gray-200 dark:border-gray-700 my-3" />);
    } else if (line.startsWith("| ")) {
      // Table block
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
      l
        .slice(1, -1)
        .split("|")
        .map((c) => c.trim())
    );

  if (rows.length === 0) return null;
  const [header, ...body] = rows;

  return (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full text-xs border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <thead className="bg-gray-50 dark:bg-gray-900">
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
            <tr key={i} className={i % 2 === 0 ? "bg-white dark:bg-gray-800" : "bg-gray-50 dark:bg-gray-900/50"}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-1.5 text-gray-600 dark:text-gray-400 border-t border-gray-100 dark:border-gray-700">
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
  // Handle **bold** and `code`
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return (
    <>
      {parts.map((p, i) => {
        if (p.startsWith("**") && p.endsWith("**")) {
          return <strong key={i} className="font-semibold text-gray-900 dark:text-white">{p.slice(2, -2)}</strong>;
        }
        if (p.startsWith("`") && p.endsWith("`")) {
          return <code key={i} className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded">{p.slice(1, -1)}</code>;
        }
        return <span key={i}>{p}</span>;
      })}
    </>
  );
}
