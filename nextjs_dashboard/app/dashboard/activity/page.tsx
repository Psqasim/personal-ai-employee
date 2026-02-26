"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { GlassSpinner } from "@/components/LoadingStates";

export default function ActivityPage() {
  const { data: session } = useSession();
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const mockActivities = [
      {
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        agent: "Cloud" as const,
        action: "created draft email",
        details: "Draft reply for client — Meeting Request",
      },
      {
        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        agent: "Local" as const,
        action: "posted to LinkedIn",
        details: "AI-generated post: AI Automation Trends 2026",
      },
      {
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        agent: "Cloud" as const,
        action: "synced vault via Git",
        details: "Pushed 3 new files to remote repository",
      },
      {
        timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
        agent: "Local" as const,
        action: "processed WhatsApp message",
        details: "AI reply drafted for urgent message",
      },
    ];
    setActivities(mockActivities);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <GlassSpinner size={56} />
      </div>
    );
  }

  return (
    <main className="px-6 py-6 space-y-6">

      {/* ── Header ───────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-start justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-extrabold bg-gradient-to-r from-violet-400 via-purple-500 to-fuchsia-500 bg-clip-text text-transparent">
            Activity Log
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Recent AI employee actions and events
          </p>
        </div>
        <motion.span
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.15 }}
          className="flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500 glass-card px-4 py-2 rounded-full shrink-0"
        >
          <span className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-pulse shadow-lg shadow-violet-500/50" />
          Last 24 hours
        </motion.span>
      </motion.div>

      {/* ── Stats Bar ────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        className="flex items-center gap-3 flex-wrap"
      >
        {[
          { label: "Total Actions", value: activities.length, color: "text-violet-400" },
          { label: "Cloud Agent", value: activities.filter(a => a.agent === "Cloud").length, color: "text-cyan-400" },
          { label: "Local Agent", value: activities.filter(a => a.agent === "Local").length, color: "text-amber-400" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.05 }}
            className="glass-card rounded-xl px-4 py-2.5 flex items-center gap-3"
          >
            <span className={`text-lg font-bold ${stat.color}`}>{stat.value}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">{stat.label}</span>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Timeline ─────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        <ActivityTimeline activities={activities} />
      </motion.div>
    </main>
  );
}
