"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { MCPStatusBadge } from "@/components/MCPStatusBadge";

interface MCPServer {
  name: string;
  status: "online" | "offline" | "unknown";
  lastCall: string | null;
  error?: string;
}

export default function StatusPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") {
      fetchHealth();
      const interval = setInterval(fetchHealth, 10000); // Poll every 10 seconds
      return () => clearInterval(interval);
    }
  }, [status]);

  const fetchHealth = async () => {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      setServers(data.servers);
    } catch (error) {
      console.error("Error fetching health:", error);
    } finally {
      setLoading(false);
    }
  };

  if (status === "loading" || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  const onlineCount = servers.filter((s) => s.status === "online").length;
  const offlineCount = servers.filter((s) => s.status === "offline").length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            MCP Server Health
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {onlineCount} online, {offlineCount} offline
          </p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-6 py-3">
            <a
              href="/dashboard"
              className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white pb-3"
            >
              Pending Approvals
            </a>
            <a
              href="/dashboard/status"
              className="text-sm font-medium text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 pb-3"
            >
              MCP Health
            </a>
            <a
              href="/dashboard/activity"
              className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white pb-3"
            >
              Activity Log
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {servers.map((server) => (
            <MCPStatusBadge
              key={server.name}
              name={server.name}
              status={server.status}
              lastCall={server.lastCall}
            />
          ))}
        </div>

        {servers.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-12 text-center border border-gray-200 dark:border-gray-700">
            <p className="text-gray-500 dark:text-gray-400">
              No MCP servers configured
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
