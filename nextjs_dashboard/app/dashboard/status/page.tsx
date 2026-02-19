"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { MCPStatusBadge } from "@/components/MCPStatusBadge";

interface MCPServer {
  name: string;
  status: "online" | "offline" | "unknown";
  lastCall: string | null;
  description?: string;
}

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
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mx-auto" />
          <p className="mt-3 text-gray-500 dark:text-gray-400 text-sm">Checking services...</p>
        </div>
      </div>
    );
  }

  const onlineCount = servers.filter((s) => s.status === "online").length;
  const offlineCount = servers.filter((s) => s.status === "offline").length;
  const unknownCount = servers.filter((s) => s.status === "unknown").length;

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

      {/* Summary bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">MCP Server Health</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Live status of all connected services
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs font-medium">
          <span className="flex items-center gap-1.5 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 px-3 py-1.5 rounded-full">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
            {onlineCount} online
          </span>
          <span className="flex items-center gap-1.5 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 px-3 py-1.5 rounded-full">
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
            {offlineCount} offline
          </span>
          {unknownCount > 0 && (
            <span className="flex items-center gap-1.5 bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-600 px-3 py-1.5 rounded-full">
              {unknownCount} unknown
            </span>
          )}
          {lastUpdated && (
            <span className="text-gray-400 dark:text-gray-500 hidden sm:block">
              Updated {lastUpdated}
            </span>
          )}
        </div>
      </div>

      {/* Server grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {servers.map((server) => (
          <div
            key={server.name}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex flex-col gap-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">
                  {server.name === "Email" ? "📧" :
                   server.name === "Gmail" ? "📩" :
                   server.name === "WhatsApp" ? "💬" :
                   server.name === "LinkedIn" ? "🔗" :
                   server.name === "Twitter" ? "🐦" :
                   server.name === "Facebook" ? "👤" :
                   server.name === "Instagram" ? "📸" :
                   server.name === "Odoo" ? "🏢" : "⚙️"}
                </span>
                <span className="font-semibold text-sm text-gray-900 dark:text-white">{server.name}</span>
              </div>
              <span className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${
                server.status === "online"
                  ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                  : server.status === "offline"
                  ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  server.status === "online" ? "bg-green-500 animate-pulse" :
                  server.status === "offline" ? "bg-red-500" : "bg-gray-400"
                }`} />
                {server.status === "online" ? "Online" : server.status === "offline" ? "Offline" : "Unknown"}
              </span>
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-400">
              {server.description || (server.status === "unknown" ? "Status unavailable" : server.status === "online" ? "Service running" : "Service not configured")}
            </p>

            <p className="text-xs text-gray-400 dark:text-gray-500">
              {server.lastCall ? `Checked: ${new Date(server.lastCall).toLocaleTimeString()}` : "Last call: Never"}
            </p>
          </div>
        ))}
      </div>

      {servers.length === 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <div className="text-4xl mb-3">🔌</div>
          <p className="text-gray-500 dark:text-gray-400">No MCP servers configured</p>
        </div>
      )}
    </main>
  );
}
