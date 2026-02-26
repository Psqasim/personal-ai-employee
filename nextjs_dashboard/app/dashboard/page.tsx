"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ApprovalCard } from "@/components/ApprovalCard";
import { VaultBrowser } from "@/components/VaultBrowser";
import { APIUsageChart } from "@/components/APIUsageChart";
import { StatsCards } from "@/components/StatsCards";
import { SkeletonCard, EmptyState } from "@/components/LoadingStates";
import { GlassCard, GlassCardList, GlassCardItem } from "@/components/GlassCard";
import { ApprovalItem, VaultSection } from "@/lib/vault";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [recentDone, setRecentDone] = useState<ApprovalItem[]>([]);
  const [counts, setCounts] = useState({ pending: 0, inProgress: 0, approved: 0 });
  const [vaultSections, setVaultSections] = useState<VaultSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"approvals" | "completed" | "usage" | "vault">("approvals");

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") {
      fetchStatus();
      const interval = setInterval(fetchStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [status]);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      setApprovals(data.approvals || []);
      setRecentDone(data.recentDone || []);
      setCounts(data.counts);
      // Fetch vault sections for the Vault tab
      try {
        const vaultRes = await fetch("/api/vault");
        if (vaultRes.ok) {
          const vaultData = await vaultRes.json();
          setVaultSections(vaultData.sections || []);
        }
      } catch {}
    } catch (error) {
      console.error("Error fetching status:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (filePath: string) => {
    try {
      const res = await fetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filePath }),
      });
      if (res.ok) {
        setApprovals((prev) => prev.filter((item) => item.filePath !== filePath));
        await fetchStatus();
      }
    } catch (error) {
      console.error("Error approving:", error);
    }
  };

  const handleReject = async (filePath: string, reason?: string) => {
    try {
      const res = await fetch("/api/reject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filePath, reason }),
      });
      if (res.ok) {
        setApprovals((prev) => prev.filter((item) => item.filePath !== filePath));
        await fetchStatus();
      }
    } catch (error) {
      console.error("Error rejecting:", error);
    }
  };

  if (loading) {
    return (
      <div className="px-6 py-6 space-y-6">
        {/* Stats skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card rounded-2xl p-6 h-28 skeleton-shimmer" />
          ))}
        </div>
        <SkeletonCard count={3} />
      </div>
    );
  }

  if (!session) return null;

  const userRole = (session.user as any).role;
  const isAdmin = userRole === "admin";

  // Viewer gets a read-only status overview
  if (!isAdmin) {
    return (
      <main className="px-6 py-6 space-y-6">
        <section>
          <GlassCard>
            <div className="p-8 text-center">
              <motion.div
                className="text-5xl mb-4"
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                🤖
              </motion.div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                AI Employee is Running
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                Your AI assistant is actively managing tasks and communications.
              </p>
              <div className="flex justify-center gap-6">
                {[
                  { value: counts.pending, label: "Pending", color: "text-amber-500" },
                  { value: counts.inProgress, label: "In Progress", color: "text-blue-500" },
                  { value: counts.approved, label: "Completed", color: "text-emerald-500" },
                ].map((stat, i) => (
                  <motion.div
                    key={stat.label}
                    className="text-center"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                  >
                    <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{stat.label}</div>
                  </motion.div>
                ))}
              </div>
            </div>
          </GlassCard>
        </section>
        <div className="text-center">
          <motion.a
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            href="/dashboard/status"
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-blue-500/25"
          >
            🏥 View MCP Health
          </motion.a>
        </div>
      </main>
    );
  }

  const catIcon: Record<string, string> = {
    Email: "📧", WhatsApp: "💬", LinkedIn: "🔗", Odoo: "🧾",
    Facebook: "📘", Instagram: "📸", Twitter: "🐦",
  };

  const tabs = [
    { id: "approvals" as const, label: "Pending Approvals", icon: "⏳", count: approvals.length },
    { id: "completed" as const, label: "Recently Completed", icon: "✅", count: recentDone.length },
    { id: "usage" as const, label: "API Usage", icon: "📈", count: null },
    { id: "vault" as const, label: "Vault Browser", icon: "📁", count: null },
  ];

  return (
    <main className="px-6 py-6 space-y-6">

      {/* ── Welcome Header ─────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-2xl font-extrabold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
          Welcome back, {session.user?.name || "Admin"} 👋
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Your Personal AI Employee is active and managing tasks
        </p>
      </motion.div>

      {/* ── Stats Cards ────────────────────────────────────────────── */}
      <StatsCards
        pending={counts.pending}
        inProgress={counts.inProgress}
        approved={counts.approved}
      />

      {/* ── Tab Navigation ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2 border-b border-gray-200 dark:border-white/[0.06] pb-0">
        {tabs.map((tab) => (
          <motion.button
            key={tab.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-xl transition-all ${
              activeTab === tab.id
                ? "text-blue-600 dark:text-cyan-400 bg-blue-500/5 dark:bg-cyan-500/10"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/[0.04]"
            }`}
          >
            <span>{tab.icon}</span>
            <span className="hidden sm:inline">{tab.label}</span>
            {tab.count !== null && tab.count > 0 && (
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                activeTab === tab.id
                  ? "bg-blue-500/20 dark:bg-cyan-500/20 text-blue-600 dark:text-cyan-400"
                  : "bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-400"
              }`}>
                {tab.count}
              </span>
            )}
            {activeTab === tab.id && (
              <motion.div
                layoutId="tab-underline"
                className="absolute bottom-0 left-0 right-0 h-[2px] bg-blue-500 dark:bg-cyan-400"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
          </motion.button>
        ))}
        <span className="ml-auto flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 px-2">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
          Live
        </span>
      </div>

      {/* ── Tab Content ────────────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        {/* ── Pending Approvals Tab ──────────────────────────────────── */}
        {activeTab === "approvals" && (
          <motion.section
            key="approvals"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {approvals.length === 0 ? (
              <EmptyState
                icon="🎉"
                title="All caught up!"
                description="Your AI employee is working — nothing needs your attention right now."
              />
            ) : (
              <GlassCardList className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                {approvals.map((item) => (
                  <GlassCardItem key={item.id}>
                    <ApprovalCard
                      item={item}
                      userRole={userRole}
                      onApprove={handleApprove}
                      onReject={handleReject}
                    />
                  </GlassCardItem>
                ))}
              </GlassCardList>
            )}
          </motion.section>
        )}

        {/* ── Recently Completed Tab ─────────────────────────────────── */}
        {activeTab === "completed" && (
          <motion.section
            key="completed"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {recentDone.length === 0 ? (
              <EmptyState
                icon="📭"
                title="No completed items"
                description="Completed tasks will appear here."
              />
            ) : (
              <GlassCardList className="space-y-2">
                {recentDone.map((item) => {
                  const icon = catIcon[item.category] ?? "📄";
                  const isOdoo = item.metadata?.type === "odoo_invoice" || item.metadata?.type === "odoo";
                  return (
                    <GlassCardItem key={item.id}>
                      <div className="flex items-center gap-3 glass-card rounded-xl px-4 py-3 hover:shadow-lg hover:shadow-emerald-500/5 transition-shadow duration-300">
                        <span className="text-xl shrink-0">{icon}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {item.title}
                          </p>
                          {isOdoo && item.metadata?.amount && (
                            <p className="text-xs text-emerald-500 font-medium">
                              {item.metadata.currency ?? "USD"} {item.metadata.amount} · {item.metadata.customer}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 dark:text-gray-500">
                            {new Date(item.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <span className="shrink-0 text-xs bg-emerald-500/10 text-emerald-500 px-2.5 py-1 rounded-full font-semibold border border-emerald-500/20">
                          Done
                        </span>
                      </div>
                    </GlassCardItem>
                  );
                })}
              </GlassCardList>
            )}
          </motion.section>
        )}

        {/* ── API Usage Tab ──────────────────────────────────────────── */}
        {activeTab === "usage" && (
          <motion.section
            key="usage"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <div className="glass-card rounded-2xl p-5">
              <APIUsageChart />
            </div>
          </motion.section>
        )}

        {/* ── Vault Browser Tab ────────────────────────────────────────── */}
        {activeTab === "vault" && (
          <motion.section
            key="vault"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <VaultBrowser sections={vaultSections} onRefresh={fetchStatus} />
          </motion.section>
        )}
      </AnimatePresence>

    </main>
  );
}
