"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { ActivityTimeline } from "@/components/ActivityTimeline";

export default function ActivityPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") {
      // Mock activities for demo
      // In production, fetch from vault logs
      const mockActivities = [
        {
          timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          agent: "Cloud" as const,
          action: "created draft email",
          details: "Draft reply for john@example.com - Meeting Request",
        },
        {
          timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          agent: "Local" as const,
          action: "approved LinkedIn post",
          details: "Posted to LinkedIn: Product Launch Announcement",
        },
        {
          timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          agent: "Cloud" as const,
          action: "synced vault via Git",
          details: "Pushed 3 new files to remote repository",
        },
      ];

      setActivities(mockActivities);
      setLoading(false);
    }
  }, [status]);

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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Recent Activity
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Last 24 hours
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
              className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white pb-3"
            >
              MCP Health
            </a>
            <a
              href="/dashboard/activity"
              className="text-sm font-medium text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 pb-3"
            >
              Activity Log
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ActivityTimeline activities={activities} />
      </main>
    </div>
  );
}
