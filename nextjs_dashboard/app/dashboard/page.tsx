"use client";

import { useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { ApprovalCard } from "@/components/ApprovalCard";
import { StatsCards } from "@/components/StatsCards";
import { UserRoleBadge } from "@/components/UserRoleBadge";
import { VaultBrowser } from "@/components/VaultBrowser";
import { CreateTaskModal } from "@/components/CreateTaskModal";
import { ApprovalItem, VaultSection } from "@/lib/vault";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [counts, setCounts] = useState({ pending: 0, inProgress: 0, approved: 0 });
  const [vaultSections, setVaultSections] = useState<VaultSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

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

      // Fetch vault sections for admin
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-lg font-medium text-gray-700 dark:text-gray-300">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  const userRole = (session.user as any).role;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm shadow-lg border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-2xl">🤖</span>
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    AI Employee Dashboard
                  </h1>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 font-medium">
                    ✨ Platinum Tier - Autonomous Workflow Management
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right bg-white dark:bg-gray-700 rounded-lg px-4 py-2 shadow-sm border border-gray-200 dark:border-gray-600">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {session.user?.name}
                </p>
                <div className="flex items-center justify-end gap-2 mt-1">
                  <UserRoleBadge role={userRole} />
                </div>
              </div>
              {userRole === "admin" && (
                <>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all"
                    title="Create New Task"
                  >
                    <span className="text-xl">➕</span>
                    <span className="text-sm">New Task</span>
                  </button>
                  <a
                    href="/dashboard/settings"
                    className="w-10 h-10 flex items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    title="Settings"
                  >
                    <span className="text-xl">⚙️</span>
                  </a>
                </>
              )}
              <button
                onClick={() => signOut({ callbackUrl: "/login" })}
                className="px-4 py-2 flex items-center justify-center gap-2 rounded-lg bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors border border-red-200 dark:border-red-800"
                title="Sign Out"
              >
                <span className="text-xl">🚪</span>
                <span className="text-sm font-semibold text-red-700 dark:text-red-300">Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-2">
            <a
              href="/dashboard"
              className="px-4 py-3 text-sm font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 border-b-2 border-blue-600 rounded-t-lg"
            >
              📋 Pending Approvals
            </a>
            <a
              href="/dashboard/status"
              className="px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700/50 rounded-t-lg transition-colors"
            >
              🏥 MCP Health
            </a>
            <a
              href="/dashboard/activity"
              className="px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700/50 rounded-t-lg transition-colors"
            >
              📊 Activity Log
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="mb-8">
          <StatsCards
            pending={counts.pending}
            inProgress={counts.inProgress}
            approved={counts.approved}
          />
        </div>

        {/* Approvals Section */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Pending Approvals
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {approvals.length} {approvals.length === 1 ? "item" : "items"} waiting for review
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Auto-updating every 5s
            </div>
          </div>

          {approvals.length === 0 ? (
            <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-16 text-center border border-gray-200 dark:border-gray-700 shadow-lg">
              <div className="text-6xl mb-4">🎉</div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                All caught up!
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                No pending approvals. Your AI employee is working smoothly.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
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
        </div>

        {/* Vault Browser - Admin Only */}
        {userRole === "admin" && vaultSections.length > 0 && (
          <div>
            <VaultBrowser sections={vaultSections} onRefresh={fetchStatus} />
          </div>
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
