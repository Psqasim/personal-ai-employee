"use client";

import { motion } from "framer-motion";

interface Activity {
  timestamp: string;
  agent: "Cloud" | "Local";
  action: string;
  details: string;
}

interface ActivityTimelineProps {
  activities: Activity[];
}

export function ActivityTimeline({ activities }: ActivityTimelineProps) {
  const agentConfig = {
    Cloud: {
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-purple-500/20",
      icon: "☁️",
      dot: "bg-purple-500",
    },
    Local: {
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
      icon: "💻",
      dot: "bg-blue-500",
    },
  };

  if (activities.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-2xl p-6"
      >
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Recent Activity
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          No recent activity
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass-card rounded-2xl p-6"
    >
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
        Recent Activity
      </h3>
      <div className="space-y-1">
        {activities.map((activity, index) => {
          const config = agentConfig[activity.agent];
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.08, type: "spring", stiffness: 100 }}
              className="flex gap-3 py-3 group"
            >
              {/* Timeline line + dot */}
              <div className="flex flex-col items-center shrink-0">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${config.bg} border ${config.border}`}>
                  {config.icon}
                </div>
                {index < activities.length - 1 && (
                  <div className="w-px flex-1 bg-white/5 mt-1" />
                )}
              </div>

              <div className="flex-1 min-w-0 pb-2">
                <p className="text-sm text-gray-900 dark:text-white">
                  <span className={`font-semibold ${config.color}`}>
                    {activity.agent}
                  </span>{" "}
                  {activity.action}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {activity.details}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {new Date(activity.timestamp).toLocaleString()}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
