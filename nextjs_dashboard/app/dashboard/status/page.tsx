"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { GlassSpinner } from "@/components/LoadingStates";

const Tilt = dynamic(() => import("react-parallax-tilt"), { ssr: false });

interface MCPServer {
  name: string;
  status: "online" | "offline" | "unknown";
  lastCall: string | null;
  description?: string;
}

const serverIcons: Record<string, string> = {
  Email: "📧", Gmail: "📩", WhatsApp: "💬", LinkedIn: "🔗",
  Twitter: "🐦", Facebook: "👤", Instagram: "📸", Odoo: "🏢",
};

export default function StatusPage() {
  const { data: session } = useSession();
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      setServers(data.servers || []);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Error fetching health:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <GlassSpinner size={56} label="Checking services..." />
      </div>
    );
  }

  const onlineCount = servers.filter((s) => s.status === "online").length;
  const offlineCount = servers.filter((s) => s.status === "offline").length;
  const unknownCount = servers.filter((s) => s.status === "unknown").length;

  return (
    <main className="px-6 py-6 space-y-6">

      {/* ── Header ───────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-wrap items-start justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-extrabold bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent">
            MCP Server Health
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Live status of all connected services
          </p>
        </div>

        {/* Summary pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <motion.span
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="flex items-center gap-2 glass-card px-4 py-2 rounded-full"
          >
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-lg shadow-emerald-500/50" />
            <span className="text-sm font-semibold text-emerald-500">{onlineCount}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">online</span>
          </motion.span>

          <motion.span
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15 }}
            className="flex items-center gap-2 glass-card px-4 py-2 rounded-full"
          >
            <span className="w-2 h-2 bg-red-500 rounded-full shadow-lg shadow-red-500/50" />
            <span className="text-sm font-semibold text-red-500">{offlineCount}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">offline</span>
          </motion.span>

          {unknownCount > 0 && (
            <motion.span
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="flex items-center gap-2 glass-card px-4 py-2 rounded-full"
            >
              <span className="w-2 h-2 bg-gray-400 rounded-full" />
              <span className="text-sm font-semibold text-gray-400">{unknownCount}</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">unknown</span>
            </motion.span>
          )}

          {lastUpdated && (
            <span className="text-xs text-gray-400 dark:text-gray-500 hidden sm:block ml-1">
              Updated {lastUpdated}
            </span>
          )}
        </div>
      </motion.div>

      {/* ── Server Grid ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {servers.map((server, index) => (
          <motion.div
            key={server.name}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06, type: "spring", stiffness: 120, damping: 14 }}
          >
            <Tilt
              tiltMaxAngleX={8}
              tiltMaxAngleY={8}
              glareEnable={true}
              glareMaxOpacity={0.08}
              glareColor={server.status === "online" ? "#10b981" : "#ffffff"}
              glarePosition="all"
              perspective={700}
              transitionSpeed={300}
              scale={1.03}
            >
              <div
                className={`glass-card rounded-2xl p-5 flex flex-col gap-3 relative overflow-hidden transition-shadow duration-300 ${
                  server.status === "online"
                    ? "hover:shadow-lg hover:shadow-emerald-500/10"
                    : server.status === "offline"
                      ? "hover:shadow-lg hover:shadow-red-500/10"
                      : "hover:shadow-lg"
                }`}
              >
                {/* Status glow accent bar */}
                <div
                  className={`absolute top-0 left-0 right-0 h-[2px] ${
                    server.status === "online"
                      ? "bg-gradient-to-r from-emerald-500/0 via-emerald-500 to-emerald-500/0"
                      : server.status === "offline"
                        ? "bg-gradient-to-r from-red-500/0 via-red-500 to-red-500/0"
                        : "bg-gradient-to-r from-gray-500/0 via-gray-500 to-gray-500/0"
                  }`}
                />

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-lg">
                      {serverIcons[server.name] || "⚙️"}
                    </div>
                    <span className="font-semibold text-sm text-gray-900 dark:text-white">
                      {server.name}
                    </span>
                  </div>
                  <span
                    className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${
                      server.status === "online"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-sm shadow-emerald-500/20"
                        : server.status === "offline"
                          ? "bg-red-500/10 text-red-400 border-red-500/20 shadow-sm shadow-red-500/20"
                          : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        server.status === "online"
                          ? "bg-emerald-400 animate-pulse"
                          : server.status === "offline"
                            ? "bg-red-400"
                            : "bg-gray-400"
                      }`}
                    />
                    {server.status === "online" ? "Online" : server.status === "offline" ? "Offline" : "Unknown"}
                  </span>
                </div>

                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  {server.description || (server.status === "unknown" ? "Status unavailable" : server.status === "online" ? "Service running" : "Service not configured")}
                </p>

                <div className="flex items-center justify-between pt-1 border-t border-white/5">
                  <p className="text-[11px] text-gray-400 dark:text-gray-500">
                    {server.lastCall ? `Checked: ${new Date(server.lastCall).toLocaleTimeString()}` : "Last call: Never"}
                  </p>
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
                      server.status === "online" ? "bg-emerald-500/10 text-emerald-400" : "bg-white/5 text-gray-500"
                    }`}
                  >
                    {server.status === "online" ? "✓" : "–"}
                  </div>
                </div>
              </div>
            </Tilt>
          </motion.div>
        ))}
      </div>

      {servers.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card rounded-2xl p-16 text-center"
        >
          <div className="text-5xl mb-4">🔌</div>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No MCP Servers Configured
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Connect your services to see their health status here.
          </p>
        </motion.div>
      )}
    </main>
  );
}
