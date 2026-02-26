"use client";

import { motion } from "framer-motion";

/* ── Skeleton Card with gradient shimmer ──────────────────────────────── */
export function SkeletonCard({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="glass-card rounded-2xl p-6 space-y-4"
          style={{ animationDelay: `${i * 0.15}s` }}
        >
          <div className="flex items-center gap-3">
            <div className="w-16 h-6 rounded-full skeleton-shimmer" />
            <div className="w-32 h-4 rounded skeleton-shimmer" />
          </div>
          <div className="w-3/4 h-5 rounded skeleton-shimmer" />
          <div className="space-y-2">
            <div className="w-full h-3 rounded skeleton-shimmer" />
            <div className="w-5/6 h-3 rounded skeleton-shimmer" />
          </div>
          <div className="flex gap-3 pt-2">
            <div className="flex-1 h-10 rounded-lg skeleton-shimmer" />
            <div className="flex-1 h-10 rounded-lg skeleton-shimmer" />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Pulsing dots loader ──────────────────────────────────────────────── */
export function PulsingDots() {
  return (
    <div className="flex items-center justify-center gap-1.5 pulse-dots">
      <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 dark:bg-cyan-400" />
      <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 dark:bg-cyan-400" />
      <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 dark:bg-cyan-400" />
    </div>
  );
}

/* ── Glass spinner ────────────────────────────────────────────────────── */
export function GlassSpinner({ size = 48, label }: { size?: number; label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className="relative"
        style={{ width: size, height: size }}
      >
        {/* Outer ring */}
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-transparent"
          style={{
            borderTopColor: "rgba(0, 217, 255, 0.8)",
            borderRightColor: "rgba(102, 126, 234, 0.4)",
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        {/* Inner ring */}
        <motion.div
          className="absolute rounded-full border-2 border-transparent"
          style={{
            inset: "4px",
            borderBottomColor: "rgba(118, 75, 162, 0.6)",
            borderLeftColor: "rgba(0, 217, 255, 0.3)",
          }}
          animate={{ rotate: -360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
        />
        {/* Center dot */}
        <motion.div
          className="absolute rounded-full bg-cyan-400/50"
          style={{
            width: size * 0.2,
            height: size * 0.2,
            top: "50%",
            left: "50%",
            marginTop: -(size * 0.1),
            marginLeft: -(size * 0.1),
          }}
          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.2, repeat: Infinity }}
        />
      </div>
      {label && (
        <p className="text-sm text-gray-400 dark:text-gray-500 font-medium">{label}</p>
      )}
    </div>
  );
}

/* ── Progress bar with glow ───────────────────────────────────────────── */
export function GlowProgress({ progress = 0 }: { progress: number }) {
  return (
    <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
      <motion.div
        className="h-full rounded-full"
        style={{
          background: "linear-gradient(90deg, #667eea, #00d9ff, #764ba2)",
          backgroundSize: "200% 100%",
          boxShadow: "0 0 12px rgba(0, 217, 255, 0.4)",
        }}
        initial={{ width: 0 }}
        animate={{
          width: `${progress}%`,
          backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
        }}
        transition={{
          width: { duration: 0.5, ease: "easeOut" },
          backgroundPosition: { duration: 3, repeat: Infinity },
        }}
      />
    </div>
  );
}

/* ── Full-page glass loader ───────────────────────────────────────────── */
export function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center"
      >
        <GlassSpinner size={56} />
        <motion.p
          className="mt-4 text-sm text-gray-400 dark:text-gray-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Loading...
        </motion.p>
      </motion.div>
    </div>
  );
}

/* ── Empty state with animation ───────────────────────────────────────── */
export function EmptyState({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 100 }}
      className="glass-card rounded-2xl p-10 text-center"
    >
      <motion.div
        className="text-5xl mb-3"
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        {icon}
      </motion.div>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{title}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
    </motion.div>
  );
}
