"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { PulsingDots } from "./LoadingStates";

interface DayUsage {
  date: string;
  inputTokens: number;
  outputTokens: number;
  calls: number;
  cost: number;
}

interface ApiUsageResponse {
  days: DayUsage[];
  totals: { cost: number; calls: number; inputTokens: number; outputTokens: number };
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function APIUsageChart() {
  const [data, setData] = useState<ApiUsageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchUsage();
  }, []);

  const fetchUsage = async () => {
    try {
      const res = await fetch("/api/api-usage");
      if (!res.ok) throw new Error("fetch failed");
      const json: ApiUsageResponse = await res.json();
      setData(json);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const chartData = data?.days.map((d) => ({
    date: formatDate(d.date),
    "Input Tokens": d.inputTokens,
    "Output Tokens": d.outputTokens,
    "Cost ($)": Number(d.cost.toFixed(4)),
    Calls: d.calls,
  })) ?? [];

  const tooltipStyle = {
    backgroundColor: "rgba(10, 10, 15, 0.9)",
    border: "1px solid rgba(255, 255, 255, 0.1)",
    borderRadius: "12px",
    fontSize: "12px",
    backdropFilter: "blur(12px)",
    color: "#e5e5e5",
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            📈 Claude API Usage — Last 7 Days
          </h3>
          {data && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {data.totals.calls > 0
                ? `${data.totals.calls} calls · $${data.totals.cost.toFixed(4)} total · ${(data.totals.inputTokens + data.totals.outputTokens).toLocaleString()} tokens`
                : "No API calls logged yet — tracking starts once the cloud agent runs"}
            </p>
          )}
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          onClick={fetchUsage}
          className="text-xs text-cyan-500 hover:text-cyan-400 transition-colors"
        >
          Refresh
        </motion.button>
      </div>

      {loading && (
        <div className="h-48 flex items-center justify-center">
          <PulsingDots />
        </div>
      )}

      {error && !loading && (
        <div className="h-32 flex items-center justify-center">
          <div className="text-center">
            <p className="text-2xl mb-2">📊</p>
            <p className="text-gray-300 text-sm font-medium">No cost data logged yet</p>
            <p className="text-xs text-gray-500 mt-1 max-w-xs">
              Cost tracking starts once the cloud agent runs. Logs saved to{" "}
              <code className="bg-white/10 px-1 rounded">vault/Logs/API_Usage/</code>
            </p>
          </div>
        </div>
      )}

      {!loading && !error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="mb-6">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              Token Usage by Day
            </p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6b7280" }} />
                <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: "12px" }} />
                <Bar dataKey="Input Tokens" fill="#667eea" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Output Tokens" fill="#00d9ff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              Daily Cost (USD)
            </p>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6b7280" }} />
                <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]}
                  contentStyle={tooltipStyle}
                />
                <Bar dataKey="Cost ($)" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      )}
    </div>
  );
}
