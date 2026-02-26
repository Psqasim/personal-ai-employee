"use client";

import { Suspense } from "react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { motion, useMotionValue, useTransform } from "framer-motion";
import { ParticleBackground } from "@/components/ParticleBackground";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    if (result?.error) {
      setError("Invalid email or password");
      setLoading(false);
    } else {
      router.push(callbackUrl);
      router.refresh();
    }
  }

  const inputCls =
    "block w-full px-4 py-3.5 rounded-xl bg-white/[0.03] border border-white/[0.08] text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/40 focus:border-cyan-400/30 focus:bg-white/[0.06] transition-all duration-300 text-sm backdrop-blur-sm";

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div>
        <label
          htmlFor="email"
          className="block text-xs font-semibold uppercase tracking-wider text-cyan-300/60 mb-2"
        >
          Email
        </label>
        <div className="relative group">
          <input
            id="email"
            name="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCls}
            placeholder="you@company.com"
          />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-[1px] bg-gradient-to-r from-cyan-400 to-purple-500 group-focus-within:w-full transition-all duration-500" />
        </div>
      </div>

      <div>
        <label
          htmlFor="password"
          className="block text-xs font-semibold uppercase tracking-wider text-cyan-300/60 mb-2"
        >
          Password
        </label>
        <div className="relative group">
          <input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={`${inputCls} pr-12`}
            placeholder="Enter your password"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-cyan-400 transition-colors duration-200"
            title={showPassword ? "Hide password" : "Show password"}
          >
            <span className="text-lg">{showPassword ? "\u{1F648}" : "\u{1F441}\uFE0F"}</span>
          </button>
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-[1px] bg-gradient-to-r from-cyan-400 to-purple-500 group-focus-within:w-full transition-all duration-500" />
        </div>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 backdrop-blur-sm"
        >
          <p className="text-red-400 text-sm text-center font-medium">{error}</p>
        </motion.div>
      )}

      <motion.button
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.97 }}
        type="submit"
        disabled={loading}
        className="relative w-full flex justify-center items-center gap-2 py-3.5 px-4 rounded-xl font-semibold text-sm text-white overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed group/btn"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-purple-500 to-cyan-500 bg-[length:200%_100%] animate-[gradient-shift_3s_linear_infinite]" />
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-purple-500 to-cyan-500 blur-xl opacity-40 group-hover/btn:opacity-60 transition-opacity duration-300" />
        <span className="relative z-10 flex items-center gap-2">
          {loading ? (
            <>
              <motion.div
                className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />
              <span>Signing in...</span>
            </>
          ) : (
            <>
              <span>Sign in</span>
              <motion.span
                animate={{ x: [0, 4, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                →
              </motion.span>
            </>
          )}
        </span>
      </motion.button>
    </form>
  );
}

export default function LoginPage() {
  const mouseX = useMotionValue(0.5);
  const mouseY = useMotionValue(0.5);
  const rotateX = useTransform(mouseY, [0, 1], [8, -8]);
  const rotateY = useTransform(mouseX, [0, 1], [-8, 8]);

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    mouseX.set((e.clientX - rect.left) / rect.width);
    mouseY.set((e.clientY - rect.top) / rect.height);
  }

  function handleMouseLeave() {
    mouseX.set(0.5);
    mouseY.set(0.5);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden bg-[#050510]">
      <ParticleBackground />

      {/* Animated gradient mesh */}
      <div className="absolute inset-0 pointer-events-none">
        <motion.div
          animate={{ x: [0, 40, -20, 0], y: [0, -30, 20, 0], scale: [1, 1.15, 0.95, 1] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[10%] left-[15%] w-[500px] h-[500px] rounded-full bg-cyan-500/[0.07] blur-[120px]"
        />
        <motion.div
          animate={{ x: [0, -50, 30, 0], y: [0, 40, -25, 0], scale: [1, 0.9, 1.1, 1] }}
          transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
          className="absolute bottom-[10%] right-[10%] w-[550px] h-[550px] rounded-full bg-purple-600/[0.08] blur-[120px]"
        />
        <motion.div
          animate={{ x: [0, 30, -40, 0], y: [0, -20, 35, 0], scale: [1, 1.1, 0.85, 1] }}
          transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-blue-500/[0.05] blur-[140px]"
        />
        <motion.div
          animate={{ x: [0, -25, 45, 0], y: [0, 35, -15, 0], scale: [1, 1.05, 0.95, 1] }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[5%] right-[25%] w-[400px] h-[400px] rounded-full bg-fuchsia-500/[0.06] blur-[100px]"
        />
      </div>

      {/* Subtle lock icon */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <motion.svg
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.02 }}
          transition={{ delay: 1, duration: 2 }}
          width="500" height="500" viewBox="0 0 24 24"
          fill="none" stroke="white" strokeWidth="0.3" strokeLinecap="round" strokeLinejoin="round"
        >
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          <circle cx="12" cy="16" r="1" />
        </motion.svg>
      </div>

      {/* 3D floating card */}
      <div
        style={{ perspective: 1000 }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="relative z-10 max-w-[400px] w-full"
      >
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.92 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.7, type: "spring", stiffness: 70, damping: 15 }}
          style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
          className="relative"
        >
          {/* Neon border glow */}
          <div className="absolute -inset-[1px] rounded-3xl bg-gradient-to-br from-cyan-400/30 via-purple-500/20 to-cyan-400/30 blur-[1px]" />
          <div className="absolute -inset-[1px] rounded-3xl bg-gradient-to-br from-cyan-400/20 via-transparent to-purple-500/20" />
          <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-cyan-500/[0.08] via-purple-500/[0.05] to-cyan-500/[0.08] blur-2xl" />

          {/* Glass card */}
          <div className="relative rounded-3xl bg-white/[0.04] backdrop-blur-2xl border border-white/[0.08] p-8 shadow-2xl shadow-black/40">
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-white/[0.06] via-transparent to-transparent pointer-events-none" />

            {/* Brand */}
            <div className="text-center mb-8 relative">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 180, damping: 12 }}
                className="relative w-20 h-20 mx-auto mb-5"
              >
                <div className="absolute -inset-[2px] rounded-full bg-gradient-to-r from-cyan-400 via-purple-500 to-cyan-400 bg-[length:200%_100%] animate-[gradient-shift_3s_linear_infinite]" />
                <div className="relative w-full h-full rounded-full bg-[#0a0a1a]/80 backdrop-blur-xl flex items-center justify-center border border-white/[0.05]">
                  <span className="text-4xl relative z-10 drop-shadow-[0_0_12px_rgba(0,217,255,0.4)]">🤖</span>
                </div>
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-500 to-purple-600 blur-2xl opacity-30" />
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-3xl font-bold tracking-tight bg-gradient-to-r from-cyan-300 via-white to-purple-400 bg-clip-text text-transparent drop-shadow-[0_0_20px_rgba(0,255,255,0.3)]"
              >
                AI Employee
              </motion.h1>

              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="mt-2 text-sm font-medium tracking-widest uppercase bg-gradient-to-r from-cyan-400/50 to-purple-400/50 bg-clip-text text-transparent"
              >
                Executive Command Center
              </motion.p>
            </div>

            <Suspense
              fallback={
                <div className="space-y-5">
                  <div className="h-[68px] rounded-xl bg-white/[0.03] animate-pulse" />
                  <div className="h-[68px] rounded-xl bg-white/[0.03] animate-pulse" />
                  <div className="h-[52px] rounded-xl bg-white/[0.03] animate-pulse" />
                </div>
              }
            >
              <LoginForm />
            </Suspense>

            <div className="mt-6 mb-4 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
              className="text-center"
            >
              <p className="text-xs text-gray-600">
                Powered by{" "}
                <span className="font-semibold bg-gradient-to-r from-cyan-400 via-purple-400 to-cyan-400 bg-[length:200%_100%] bg-clip-text text-transparent animate-[gradient-shift_3s_linear_infinite]">
                  Claude AI
                </span>
              </p>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
