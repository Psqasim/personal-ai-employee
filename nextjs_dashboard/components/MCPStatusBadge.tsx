interface MCPStatusBadgeProps {
  name: string;
  status: "online" | "offline" | "unknown";
  lastCall: string | null;
}

export function MCPStatusBadge({ name, status, lastCall }: MCPStatusBadgeProps) {
  const statusStyles = {
    online: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    offline: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    unknown: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  };

  const statusIcons = {
    online: "✓",
    offline: "✗",
    unknown: "?",
  };

  const getTimeSince = (timestamp: string | null) => {
    if (!timestamp) return "Never";

    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-900 dark:text-white">{name}</span>
        <span
          className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded ${statusStyles[status]}`}
        >
          {statusIcons[status]} {status}
        </span>
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        Last call: {getTimeSince(lastCall)}
      </div>
    </div>
  );
}
