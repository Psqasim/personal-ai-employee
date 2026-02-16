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
  const agentColors = {
    Cloud: "text-purple-600 dark:text-purple-400",
    Local: "text-blue-600 dark:text-blue-400",
  };

  const agentIcons = {
    Cloud: "☁️",
    Local: "💻",
  };

  if (activities.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Recent Activity
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          No recent activity
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
        Recent Activity
      </h3>
      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={index} className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
              {agentIcons[activity.agent]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900 dark:text-white">
                <span className={`font-semibold ${agentColors[activity.agent]}`}>
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
          </div>
        ))}
      </div>
    </div>
  );
}
