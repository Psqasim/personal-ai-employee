"use client";

import { useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter, usePathname } from "next/navigation";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { UserRoleBadge } from "@/components/UserRoleBadge";
import { QuickCreateModal } from "@/components/QuickCreateModal";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [counts, setCounts] = useState({ pending: 0, inProgress: 0, approved: 0 });
  const [showQuickCreate, setShowQuickCreate] = useState(false);

  // Compute role before any hooks that depend on it (session may be null during loading)
  const userRole = (session?.user as any)?.role;
  const isAdmin = userRole === "admin";

  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  useEffect(() => {
    if (status !== "authenticated") return;
    const fetchCounts = async () => {
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        setCounts(data.counts);
      } catch {}
    };
    fetchCounts();
    const interval = setInterval(fetchCounts, 5000);
    return () => clearInterval(interval);
  }, [status]);

  // Redirect viewers away from admin-only pages (hook must be before any early return)
  useEffect(() => {
    if (status !== "authenticated" || isAdmin) return;
    if (pathname === "/dashboard" || pathname === "/dashboard/briefings") {
      router.push("/dashboard/status");
    }
  }, [status, isAdmin, pathname]);

  if (status === "loading" || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  // Admin sees all tabs; viewer only sees non-sensitive pages
  const navItems = [
    ...(isAdmin ? [{ href: "/dashboard", label: "📋 Approvals", active: pathname === "/dashboard" }] : []),
    { href: "/dashboard/status", label: "🏥 MCP Health", active: pathname === "/dashboard/status" },
    { href: "/dashboard/activity", label: "📊 Activity", active: pathname === "/dashboard/activity" },
    ...(isAdmin ? [{ href: "/dashboard/briefings", label: "📊 CEO Briefings", active: pathname === "/dashboard/briefings" }] : []),
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">

      {/* ─── Header ───────────────────────────────────────────────────── */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">

          {/* Brand */}
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xl">🤖</span>
            <span className="font-bold text-gray-900 dark:text-white text-sm hidden sm:block">AI Employee</span>
            <span className="text-xs bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-full font-medium hidden sm:block">
              Platinum
            </span>
          </div>

          {/* Stats pills */}
          <div className="flex items-center gap-2 text-xs font-medium">
            <span className="flex items-center gap-1 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800 px-3 py-1 rounded-full">
              ⏳ {counts.pending} pending
            </span>
            <span className="flex items-center gap-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800 px-3 py-1 rounded-full">
              ⚙️ {counts.inProgress} active
            </span>
            <span className="hidden sm:flex items-center gap-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 px-3 py-1 rounded-full">
              ✅ {counts.approved} done
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            <DarkModeToggle />
            {isAdmin && (
              <>
                <button
                  onClick={() => setShowQuickCreate(true)}
                  className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors shadow-sm"
                >
                  ✨ <span className="hidden xs:inline sm:inline">Quick Create</span><span className="sm:hidden">Create</span>
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
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-800 text-xs font-semibold text-red-600 dark:text-red-400 transition-colors"
            >
              🚪 Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* ─── Sub Nav ──────────────────────────────────────────────────── */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-1 overflow-x-auto">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className={`px-4 py-2.5 text-sm whitespace-nowrap transition-colors ${
                item.active
                  ? "font-semibold text-blue-600 dark:text-blue-400 border-b-2 border-blue-600"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-t"
              }`}
            >
              {item.label}
              {item.href === "/dashboard" && counts.pending > 0 && (
                <span className="ml-1.5 bg-blue-600 text-white text-xs rounded-full px-1.5 py-0.5">
                  {counts.pending}
                </span>
              )}
            </a>
          ))}
        </div>
      </nav>

      {/* ─── Page Content ─────────────────────────────────────────────── */}
      <div className="flex-1">
        {children}
      </div>

      {/* ─── Footer ───────────────────────────────────────────────────── */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span>🤖</span>
            <span className="font-semibold text-gray-700 dark:text-gray-300">Personal AI Employee</span>
            <span>·</span>
            <span>Platinum Tier</span>
            <span>·</span>
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse inline-block" />
            <span>Live</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
            <span>Powered by Claude AI</span>
            <span>·</span>
            <span>Built for Hackathon 2026</span>
            <span>·</span>
            <span>© 2026</span>
          </div>
        </div>
      </footer>

      {/* ─── Modals ───────────────────────────────────────────────────── */}
      {isAdmin && (
        <QuickCreateModal
          isOpen={showQuickCreate}
          onClose={() => setShowQuickCreate(false)}
        />
      )}
    </div>
  );
}
