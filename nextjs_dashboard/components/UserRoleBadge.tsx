interface UserRoleBadgeProps {
  role: "admin" | "viewer";
}

export function UserRoleBadge({ role }: UserRoleBadgeProps) {
  const styles = {
    admin: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
    viewer: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  };

  const icons = {
    admin: "👑",
    viewer: "👁️",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded ${styles[role]}`}
    >
      <span>{icons[role]}</span>
      <span>{role.charAt(0).toUpperCase() + role.slice(1)}</span>
    </span>
  );
}
