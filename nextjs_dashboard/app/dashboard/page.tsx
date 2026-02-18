"use client";

import { useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { ApprovalCard } from "@/components/ApprovalCard";
import { UserRoleBadge } from "@/components/UserRoleBadge";
import { VaultBrowser } from "@/components/VaultBrowser";
import { CreateTaskModal } from "@/components/CreateTaskModal";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { APIUsageChart } from "@/components/APIUsageChart";
import { ApprovalItem, VaultSection } from "@/lib/vault";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [counts, setCounts] = useState({ pending: 0, inProgress: 0, approved: 0 });
  const [vaultSections, setVaultSections] = useState<VaultSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [showVault, setShowVault] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
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
      setApprovals(data.approvals);
      setCounts(data.counts);

      const userRole = (session?.user as any)?.role;
      if (userRole === "admin") {
        const vaultRes = await fetch("/api/vault");
        if (vaultRes.ok) {
          const vaultData = await vaultRes.json();
          setVaultSections(vaultData.sections);
        }
      }
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

  if (status === "loading" || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mx-auto" />
          <p className="mt-3 text-gray-500 dark:text-gray-400 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!session) return null;

  const userRole = (session.user as any).role;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">

      {/* ─── Header ─────────────────────────────────────────────── */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">

          {/* Left: Brand */}
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xl">🤖</span>
            <span className="font-bold text-gray-900 dark:text-white text-sm hidden sm:block">
              AI Employee
            </span>
            <span className="text-xs bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-full font-medium hidden sm:block">
              Platinum
            </span>
          </div>

          {/* Center: Quick stats pills */}
          <div className="flex items-center gap-2 text-xs font-medium">
            <span className="flex items-center gap-1 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800 px-3 py-1 rounded-full">
              ⏳ {counts.pending} pending
            </span>
            <span className="flex items-center gap-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800 px-3 py-1 rounded-full">
              ⚙️ {counts.inProgress} active
            </span>
            <span className="flex items-center gap-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 px-3 py-1 rounded-full hidden sm:flex">
              ✅ {counts.approved} done
            </span>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2 shrink-0">
            <DarkModeToggle />
            {userRole === "admin" && (
              <>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="hidden sm:flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors"
                >
                  ➕ New Task
                </button>
                <a
                  href="/dashboard/settings"
                  className="w-8 h-8 flex items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm"
                  title="Settings"
                >
                  ⚙️
                </a>
              </>
            )}
            <div className="hidden sm:flex items-center gap-1 border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-1">
              <span className="text-xs text-gray-700 dark:text-gray-300 font-medium">{session.user?.name}</span>
              <UserRoleBadge role={userRole} />
            </div>
            <button
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="w-8 h-8 flex items-center justify-center rounded-lg bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-800 text-sm transition-colors"
              title="Sign Out"
            >
              🚪
            </button>
          </div>
        </div>
      </header>

      {/* ─── Sub Nav ─────────────────────────────────────────────── */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-1 overflow-x-auto">
          <a href="/dashboard" className="px-4 py-2.5 text-sm font-semibold text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 whitespace-nowrap">
            📋 Approvals
            {counts.pending > 0 && (
              <span className="ml-1.5 bg-blue-600 text-white text-xs rounded-full px-1.5 py-0.5">
                {counts.pending}
              </span>
            )}
          </a>
          <a href="/dashboard/status" className="px-4 py-2.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-t transition-colors whitespace-nowrap">
            🏥 MCP Health
          </a>
          <a href="/dashboard/activity" className="px-4 py-2.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-t transition-colors whitespace-nowrap">
            📊 Activity
          </a>
        </div>
      </nav>

      {/* ─── Main Content ─────────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

        {/* ── Pending Approvals (PRIMARY content — first thing you see) ── */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Pending Approvals</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {approvals.length === 0
                  ? "All clear — nothing waiting"
                  : `${approvals.length} item${approvals.length === 1 ? "" : "s"} need your review`}
              </p>
            </div>
            <span className="flex items-center gap-1.5 text-xs text-gray-400">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              Live — updates every 5s
            </span>
          </div>

          {approvals.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-10 text-center">
              <div className="text-5xl mb-3">🎉</div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">All caught up!</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Your AI employee is working — nothing needs your attention right now.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {approvals.map((item) => (
                <ApprovalCard
                  key={item.id}
                  item={item}
                  userRole={userRole}
                  onApprove={handleApprove}
                  onReject={handleReject}
                />
              ))}
            </div>
          )}
        </section>

        {/* ── API Usage Chart (collapsible) ── */}
        <section>
          <button
            onClick={() => setShowChart(!showChart)}
            className="w-full flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-5 py-3.5 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group"
          >
            <div className="flex items-center gap-2">
              <span className="text-base">📈</span>
              <span className="font-semibold text-gray-900 dark:text-white text-sm">API Usage & Cost</span>
              <span className="text-xs text-gray-400">Last 7 days</span>
            </div>
            <span className="text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-200 transition-colors text-sm">
              {showChart ? "▲ Collapse" : "▼ Expand"}
            </span>
          </button>
          {showChart && (
            <div className="mt-2">
              <APIUsageChart />
            </div>
          )}
        </section>

        {/* ── Vault Browser (admin, collapsible) ── */}
        {userRole === "admin" && (
          <section>
            <button
              onClick={() => setShowVault(!showVault)}
              className="w-full flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-5 py-3.5 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group"
            >
              <div className="flex items-center gap-2">
                <span className="text-base">📁</span>
                <span className="font-semibold text-gray-900 dark:text-white text-sm">Vault Browser</span>
                <span className="text-xs text-gray-400">Admin only</span>
              </div>
              <span className="text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-200 transition-colors text-sm">
                {showVault ? "▲ Collapse" : "▼ Expand"}
              </span>
            </button>
            {showVault && vaultSections.length > 0 && (
              <div className="mt-2">
                <VaultBrowser sections={vaultSections} onRefresh={fetchStatus} />
              </div>
            )}
          </section>
        )}
      </main>

      {/* Create Task Modal */}
      {userRole === "admin" && (
        <CreateTaskModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={fetchStatus}
        />
      )}
    </div>
  );
}
