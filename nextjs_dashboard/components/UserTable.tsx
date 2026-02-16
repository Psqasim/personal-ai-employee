"use client";

import { useState } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "viewer";
  created_at: string;
}

interface UserTableProps {
  users: User[];
  currentUserId: string;
  onUserDeleted: () => void;
  onRoleUpdated: () => void;
}

export function UserTable({
  users,
  currentUserId,
  onUserDeleted,
  onRoleUpdated,
}: UserTableProps) {
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [newRole, setNewRole] = useState<"admin" | "viewer">("viewer");
  const [message, setMessage] = useState("");

  const handleDeleteUser = async (userId: string) => {
    if (!confirm("Are you sure you want to delete this user?")) {
      return;
    }

    setMessage("");

    try {
      const res = await fetch("/api/users/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
      });

      const data = await res.json();

      if (res.ok) {
        setMessage("User deleted successfully");
        onUserDeleted();
      } else {
        setMessage(data.error || "Failed to delete user");
      }
    } catch (error) {
      setMessage("Error deleting user");
    }
  };

  const handleUpdateRole = async (userId: string) => {
    setMessage("");

    try {
      const res = await fetch("/api/users/update-role", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, newRole }),
      });

      const data = await res.json();

      if (res.ok) {
        setMessage("Role updated successfully");
        setEditingUserId(null);
        onRoleUpdated();
      } else {
        setMessage(data.error || "Failed to update role");
      }
    } catch (error) {
      setMessage("Error updating role");
    }
  };

  return (
    <div>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Current Users
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {users.length} {users.length === 1 ? "user" : "users"} in the system
        </p>
      </div>

      {message && (
        <div
          className={`mb-4 p-3 rounded-lg text-sm ${
            message.includes("success")
              ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400"
              : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400"
          }`}
        >
          {message}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Email
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Role
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Created
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                  {user.email}
                  {user.id === currentUserId && (
                    <span className="ml-2 text-xs text-blue-600 dark:text-blue-400 font-medium">
                      (You)
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                  {user.name}
                </td>
                <td className="px-4 py-3 text-sm">
                  {editingUserId === user.id ? (
                    <div className="flex items-center gap-2">
                      <select
                        value={newRole}
                        onChange={(e) => setNewRole(e.target.value as "admin" | "viewer")}
                        className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      >
                        <option value="viewer">Viewer</option>
                        <option value="admin">Admin</option>
                      </select>
                      <button
                        onClick={() => handleUpdateRole(user.id)}
                        className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingUserId(null)}
                        className="px-2 py-1 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded ${
                        user.role === "admin"
                          ? "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300"
                          : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                      }`}
                    >
                      {user.role === "admin" ? "Admin" : "Viewer"}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-center justify-center gap-2">
                    {editingUserId !== user.id && (
                      <>
                        <button
                          onClick={() => {
                            setEditingUserId(user.id);
                            setNewRole(user.role);
                          }}
                          className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                          title="Edit Role"
                        >
                          Edit Role
                        </button>
                        {user.id !== currentUserId && (
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
                            title="Delete User"
                          >
                            🗑️ Delete
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
