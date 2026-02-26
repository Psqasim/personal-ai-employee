"use client";

import { useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { UserRoleBadge } from "@/components/UserRoleBadge";
import { QuickCreateModal } from "@/components/QuickCreateModal";
import { AnimatedPage } from "@/components/AnimatedLayout";
import { ParticleBackground } from "@/components/ParticleBackground";
import { GlassSpinner } from "@/components/LoadingStates";

/* ── Sidebar animation variants ──────────────────────────────────────── */
const sidebarVariants = {
  expanded: {
    width: 260,
    transition: { type: "spring" as const, stiffness: 300, damping: 30 },
  },
  collapsed: {
    width: 72,
    transition: { type: "spring" as const, stiffness: 300, damping: 30 },
  },
};

const mobileSidebarVariants = {
  open: {
    x: 0,
    transition: { type: "spring" as const, stiffness: 300, damping: 30 },
  },
  closed: {
    x: -280,
    transition: { type: "spring" as const, stiffness: 300, damping: 30 },
  },
};

const backdropVariants = {
  open: { opacity: 1, transition: { duration: 0.2 } },
  closed: { opacity: 0, transition: { duration: 0.2 } },
};

/* ── Page title mapping ──────────────────────────────────────────────── */
function getPageTitle(pathname: string): string {
  switch (pathname) {
    case "/dashboard":
      return "Approvals";
    case "/dashboard/status":
      return "MCP Health";
    case "/dashboard/activity":
      return "Activity";
    case "/dashboard/briefings":
      return "CEO Briefings";
    case "/dashboard/settings":
      return "Settings";
    default:
      return "Dashboard";
  }
}

/* ── Chevron icon component ──────────────────────────────────────────── */
function ChevronIcon({ direction }: { direction: "left" | "right" }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="transition-transform duration-200"
    >
      {direction === "left" ? (
        <polyline points="10 2 4 8 10 14" />
      ) : (
        <polyline points="6 2 12 8 6 14" />
      )}
    </svg>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [counts, setCounts] = useState({ pending: 0, inProgress: 0, approved: 0 });
  const [showQuickCreate, setShowQuickCreate] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  const userRole = (session?.user as any)?.role;
  const isAdmin = userRole === "admin";

  /* ── Detect mobile breakpoint ──────────────────────────────────────── */
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false);
      }
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  /* ── Auth redirect ─────────────────────────────────────────────────── */
  useEffect(() => {
    if (status === "unauthenticated") router.push("/login");
  }, [status, router]);

  /* ── Fetch status counts every 5s ──────────────────────────────────── */
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

  /* ── Viewer redirect (non-admin can't see /dashboard or /briefings) ── */
  useEffect(() => {
    if (status !== "authenticated" || isAdmin) return;
    if (pathname === "/dashboard" || pathname === "/dashboard/briefings") {
      router.push("/dashboard/status");
    }
  }, [status, isAdmin, pathname]);

  /* ── Track scroll for header shadow ────────────────────────────────── */
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  /* ── Close mobile sidebar on route change ──────────────────────────── */
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  /* ── Loading state ─────────────────────────────────────────────────── */
  if (status === "loading" || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <GlassSpinner size={56} label="Loading dashboard..." />
      </div>
    );
  }

  /* ── Nav items ─────────────────────────────────────────────────────── */
  const navItems = [
    ...(isAdmin
      ? [{ href: "/dashboard", label: "Approvals", icon: "\uD83D\uDCCB", active: pathname === "/dashboard" }]
      : []),
    { href: "/dashboard/status", label: "MCP Health", icon: "\uD83C\uDFE5", active: pathname === "/dashboard/status" },
    { href: "/dashboard/activity", label: "Activity", icon: "\uD83D\uDCCA", active: pathname === "/dashboard/activity" },
    ...(isAdmin
      ? [{ href: "/dashboard/briefings", label: "CEO Briefings", icon: "\uD83D\uDCCA", active: pathname === "/dashboard/briefings" }]
      : []),
    ...(isAdmin
      ? [{ href: "/dashboard/settings", label: "Settings", icon: "\u2699\uFE0F", active: pathname === "/dashboard/settings" }]
      : []),
  ];

  /* ── User initials for avatar ──────────────────────────────────────── */
  const userName = session.user?.name || "User";
  const initials = userName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  /* ── Sidebar content (shared between desktop and mobile) ───────────── */
  const renderSidebarContent = (isExpanded: boolean) => (
    <div className="flex flex-col h-full">
      {/* ── Logo area ─────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2.5 px-4 h-16 shrink-0 border-b border-gray-200/50 dark:border-white/[0.06]">
        <motion.span
          className="text-2xl shrink-0"
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity, repeatDelay: 5 }}
        >
          🤖
        </motion.span>
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              className="flex items-center gap-2 overflow-hidden"
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2 }}
            >
              <span className="font-bold text-gray-900 dark:text-white text-sm whitespace-nowrap">
                AI Employee
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full font-semibold whitespace-nowrap bg-gradient-to-r from-indigo-500/10 to-purple-500/10 text-indigo-600 dark:text-indigo-300 border border-indigo-500/20 dark:border-indigo-500/30">
                Platinum
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Navigation ────────────────────────────────────────────────── */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <motion.a
            key={item.href}
            href={item.href}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={`relative flex items-center gap-3 rounded-xl transition-all duration-200 group ${
              isExpanded ? "px-3 py-2.5" : "px-0 py-2.5 justify-center"
            } ${
              item.active
                ? "bg-blue-500/10 text-blue-600 dark:bg-cyan-500/10 dark:text-cyan-400"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/[0.06]"
            }`}
          >
            {/* Active indicator - cyan left border */}
            {item.active && (
              <motion.div
                layoutId="sidebar-active-indicator"
                className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-blue-500 dark:bg-cyan-400 shadow-[0_0_8px_rgba(0,100,255,0.4)] dark:shadow-[0_0_8px_rgba(0,217,255,0.6)]"
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
              />
            )}

            {/* Icon */}
            <span className="text-lg shrink-0 w-6 text-center">{item.icon}</span>

            {/* Label */}
            <AnimatePresence>
              {isExpanded && (
                <motion.span
                  className="text-sm font-medium whitespace-nowrap overflow-hidden"
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: "auto" }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {item.label}
                </motion.span>
              )}
            </AnimatePresence>

            {/* Pending badge on Approvals */}
            {item.href === "/dashboard" && counts.pending > 0 && isExpanded && (
              <motion.span
                className="ml-auto bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-[10px] rounded-full px-1.5 py-0.5 font-bold shadow-lg shadow-cyan-500/30"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 20 }}
              >
                {counts.pending}
              </motion.span>
            )}

            {/* Collapsed pending badge - show as dot */}
            {item.href === "/dashboard" && counts.pending > 0 && !isExpanded && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-cyan-400 rounded-full shadow-[0_0_6px_rgba(0,217,255,0.6)]" />
            )}
          </motion.a>
        ))}
      </nav>

      {/* ── Sidebar Stats ───────────────────────────────────────────── */}
      {isExpanded && isAdmin && (
        <div className="shrink-0 border-t border-gray-200/50 dark:border-white/[0.06] px-3 py-2.5 space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 px-1">
            Overview
          </p>
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-amber-500/5 dark:bg-amber-500/10">
            <span className="text-sm">⏳</span>
            <span className="text-xs font-medium text-amber-700 dark:text-amber-400 flex-1">Pending</span>
            <span className="text-xs font-bold text-amber-700 dark:text-amber-400 bg-amber-500/10 dark:bg-amber-500/20 px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
              {counts.pending}
            </span>
          </div>
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-emerald-500/5 dark:bg-emerald-500/10">
            <span className="text-sm">✅</span>
            <span className="text-xs font-medium text-emerald-700 dark:text-emerald-400 flex-1">Completed</span>
            <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 dark:bg-emerald-500/20 px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
              {counts.approved}
            </span>
          </div>
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-blue-500/5 dark:bg-blue-500/10">
            <span className="text-sm">⚙️</span>
            <span className="text-xs font-medium text-blue-700 dark:text-blue-400 flex-1">In Progress</span>
            <span className="text-xs font-bold text-blue-700 dark:text-blue-400 bg-blue-500/10 dark:bg-blue-500/20 px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
              {counts.inProgress}
            </span>
          </div>
        </div>
      )}

      {/* ── Bottom section ────────────────────────────────────────────── */}
      <div className="shrink-0 border-t border-gray-200/50 dark:border-white/[0.06] p-3 space-y-2">
        {/* Dark mode toggle */}
        <div className={`flex items-center ${isExpanded ? "justify-between px-1" : "justify-center"}`}>
          {isExpanded && (
            <span className="text-xs text-gray-500 font-medium">Theme</span>
          )}
          <DarkModeToggle />
        </div>

        {/* User card */}
        <div
          className={`flex items-center gap-2.5 rounded-xl p-2 bg-gray-100/80 dark:bg-white/[0.04] border border-gray-200/50 dark:border-white/[0.06] ${
            isExpanded ? "" : "justify-center"
          }`}
        >
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-bold text-white bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
            {initials}
          </div>
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                className="flex-1 min-w-0 overflow-hidden"
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }}
              >
                <div className="text-xs font-semibold text-gray-900 dark:text-white truncate">
                  {userName}
                </div>
                <div className="mt-0.5">
                  <UserRoleBadge role={userRole} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Sign out button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => signOut({ callbackUrl: "/login" })}
          className={`w-full flex items-center gap-2 rounded-xl text-xs font-semibold transition-all bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 ${
            isExpanded ? "px-3 py-2 justify-start" : "px-0 py-2 justify-center"
          }`}
        >
          <span>🚪</span>
          <AnimatePresence>
            {isExpanded && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }}
                className="whitespace-nowrap overflow-hidden"
              >
                Sign Out
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>

        {/* Collapse toggle (desktop only) */}
        {!isMobile && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSidebarOpen((prev) => !prev)}
            className="w-full flex items-center justify-center py-1.5 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-colors"
            title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            <ChevronIcon direction={sidebarOpen ? "left" : "right"} />
          </motion.button>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex relative">
      {/* Particle Background */}
      <ParticleBackground />

      {/* ═══════════════════════════════════════════════════════════════════
          DESKTOP SIDEBAR
         ═══════════════════════════════════════════════════════════════════ */}
      <motion.aside
        className="hidden md:flex flex-col fixed top-0 left-0 h-screen z-40 sidebar-glass"
        variants={sidebarVariants}
        animate={sidebarOpen ? "expanded" : "collapsed"}
        initial={false}
      >
        {renderSidebarContent(sidebarOpen)}
      </motion.aside>

      {/* ═══════════════════════════════════════════════════════════════════
          MOBILE SIDEBAR OVERLAY
         ═══════════════════════════════════════════════════════════════════ */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
              variants={backdropVariants}
              initial="closed"
              animate="open"
              exit="closed"
              onClick={() => setMobileOpen(false)}
            />
            {/* Slide-over sidebar */}
            <motion.aside
              className="fixed top-0 left-0 h-screen z-50 w-[260px] sidebar-glass md:hidden"
              variants={mobileSidebarVariants}
              initial="closed"
              animate="open"
              exit="closed"
            >
              {renderSidebarContent(true)}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN CONTENT AREA
         ═══════════════════════════════════════════════════════════════════ */}
      <motion.div
        className="flex-1 flex flex-col min-h-screen"
        animate={{
          marginLeft: isMobile ? 0 : sidebarOpen ? 260 : 72,
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        {/* ── Top Header Bar ──────────────────────────────────────────── */}
        <header
          className={`sticky top-0 z-30 glass-header transition-all duration-300 ${
            scrolled ? "shadow-lg shadow-black/5 dark:shadow-black/20" : ""
          }`}
        >
          <div className="px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
            {/* Left: Mobile hamburger + Breadcrumb */}
            <div className="flex items-center gap-3">
              {/* Mobile menu button */}
              <button
                className="md:hidden flex items-center justify-center w-8 h-8 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                onClick={() => setMobileOpen(true)}
                aria-label="Open sidebar"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <rect x="2" y="4" width="16" height="1.5" rx="0.75" />
                  <rect x="2" y="9.25" width="16" height="1.5" rx="0.75" />
                  <rect x="2" y="14.5" width="16" height="1.5" rx="0.75" />
                </svg>
              </button>

              {/* Breadcrumb */}
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500 dark:text-gray-500 hidden sm:inline">Dashboard</span>
                <span className="text-gray-400 dark:text-gray-600 hidden sm:inline">/</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {getPageTitle(pathname)}
                </span>
              </div>
            </div>

            {/* Center/Right: Stats pills + Quick Create */}
            <div className="flex items-center gap-2">
              {/* Stats pills */}
              <div className="flex items-center gap-1.5 text-xs font-medium">
                <motion.span
                  className="flex items-center gap-1 px-2.5 py-1 rounded-full glass-card"
                  whileHover={{ scale: 1.05 }}
                >
                  <span className="text-amber-500">⏳</span>
                  <span className="text-amber-600 dark:text-amber-400">{counts.pending}</span>
                  <span className="text-gray-500 dark:text-gray-400 hidden lg:inline">pending</span>
                </motion.span>
                <motion.span
                  className="flex items-center gap-1 px-2.5 py-1 rounded-full glass-card"
                  whileHover={{ scale: 1.05 }}
                >
                  <span className="text-blue-500">⚙️</span>
                  <span className="text-blue-600 dark:text-blue-400">{counts.inProgress}</span>
                  <span className="text-gray-500 dark:text-gray-400 hidden lg:inline">active</span>
                </motion.span>
                <motion.span
                  className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-full glass-card"
                  whileHover={{ scale: 1.05 }}
                >
                  <span className="text-emerald-500">✅</span>
                  <span className="text-emerald-600 dark:text-emerald-400">{counts.approved}</span>
                  <span className="text-gray-500 dark:text-gray-400">done</span>
                </motion.span>
              </div>

              {/* Quick Create button (admin only) */}
              {isAdmin && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowQuickCreate(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg shadow-blue-500/25"
                >
                  <span>✨</span>
                  <span className="hidden sm:inline">Quick Create</span>
                  <span className="sm:hidden">Create</span>
                </motion.button>
              )}
            </div>
          </div>
        </header>

        {/* ── Page Content ────────────────────────────────────────────── */}
        <div className="flex-1">
          <AnimatedPage>{children}</AnimatedPage>
        </div>
      </motion.div>

      {/* ── Modals ────────────────────────────────────────────────────── */}
      {isAdmin && (
        <QuickCreateModal
          isOpen={showQuickCreate}
          onClose={() => setShowQuickCreate(false)}
        />
      )}
    </div>
  );
}
