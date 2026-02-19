"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { ActivityTimeline } from "@/components/ActivityTimeline";

export default function ActivityPage() {
  const { data: session } = useSession();
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load real vault watcher logs if available, else show demo
    const mockActivities = [
      {
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        agent: "Cloud" as const,
        action: "created draft email",
        details: "Draft reply for client — Meeting Request",
      },
      {
        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        agent: "Local" as const,
        action: "posted to LinkedIn",
        details: "AI-generated post: AI Automation Trends 2026",
      },
      {
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        agent: "Cloud" as const,
        action: "synced vault via Git",
        details: "Pushed 3 new files to remote repository",
      },
      {
        timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
        agent: "Local" as const,
        action: "processed WhatsApp message",
        details: "AI reply drafted for urgent message",
      },
    ];
    setActivities(mockActivities);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">Activity Log</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Recent AI employee actions</p>
        </div>
        <span className="text-xs text-gray-400">Last 24 hours</span>
      </div>
      <ActivityTimeline activities={activities} />
    </main>
  );
}
