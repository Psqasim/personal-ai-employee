interface StatsCardsProps {
  pending: number;
  inProgress: number;
  approved: number;
}

export function StatsCards({ pending, inProgress, approved }: StatsCardsProps) {
  const stats = [
    {
      label: "Pending Approval",
      value: pending,
      icon: "⏳",
      gradient: "from-yellow-400 to-orange-500",
      bg: "bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20",
      border: "border-yellow-200 dark:border-yellow-800",
    },
    {
      label: "In Progress",
      value: inProgress,
      icon: "⚙️",
      gradient: "from-blue-400 to-cyan-500",
      bg: "bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20",
      border: "border-blue-200 dark:border-blue-800",
    },
    {
      label: "Approved Today",
      value: approved,
      icon: "✅",
      gradient: "from-green-400 to-emerald-500",
      bg: "bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20",
      border: "border-green-200 dark:border-green-800",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className={`${stat.bg} rounded-2xl p-6 border ${stat.border} shadow-lg hover:shadow-xl transition-shadow duration-300`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                {stat.label}
              </p>
              <p className={`text-4xl font-bold mt-3 bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent`}>
                {stat.value}
              </p>
            </div>
            <div className={`text-5xl p-4 rounded-xl bg-gradient-to-br ${stat.gradient} bg-opacity-10`}>
              {stat.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
