"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { signOut } from "next-auth/react";
import { UserTable } from "@/components/UserTable";

interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "viewer";
  created_at: string;
}

export default function SettingsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"password" | "users">("password");

  // Password change form
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");

  // Add user form
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [newUserRole, setNewUserRole] = useState<"admin" | "viewer">("viewer");
  const [userMessage, setUserMessage] = useState("");

  // User list
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") {
      const userRole = (session?.user as any)?.role;
      if (userRole !== "admin") {
        // Don't auto-redirect — show access denied UI instead
      } else {
        fetchUsers();
      }
    }
  }, [status, session, router]);

  const fetchUsers = async () => {
    try {
      const res = await fetch("/api/users/list");
      if (res.ok) {
        const data = await res.json();
        setUsers(data.users);
      }
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage("");

    if (newPassword !== confirmPassword) {
      setPasswordMessage("Passwords do not match");
      return;
    }

    try {
      const res = await fetch("/api/users/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: (session?.user as any)?.id,
          password: newPassword,
        }),
      });

      if (res.ok) {
        setPasswordMessage("Password updated successfully");
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      } else {
        setPasswordMessage("Failed to update password");
      }
    } catch (error) {
      setPasswordMessage("Error updating password");
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setUserMessage("");

    try {
      const res = await fetch("/api/users/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: newUserEmail,
          password: newUserPassword,
          name: newUserName,
          role: newUserRole,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setUserMessage(`User ${newUserEmail} created successfully`);
        setNewUserEmail("");
        setNewUserPassword("");
        setNewUserName("");
        setNewUserRole("viewer");
        fetchUsers(); // Refresh user list
      } else {
        setUserMessage(data.error || "Failed to create user");
      }
    } catch (error) {
      setUserMessage("Error creating user");
    }
  };

  if (status === "loading") {
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

  const currentRole = (session.user as any)?.role;
  if (currentRole !== "admin") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
        <div className="text-center max-w-sm">
          <div className="text-6xl mb-5">🔒</div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Access Denied</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
            Settings are only available to administrators. Your current role is{" "}
            <span className="font-semibold text-gray-700 dark:text-gray-300">{currentRole}</span>.
          </p>
          <a
            href="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow transition-all"
          >
            ← Back to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Settings
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Admin configuration
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
              className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white pb-3"
            >
              Activity Log
            </a>
            <a
              href="/dashboard/settings"
              className="text-sm font-medium text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 pb-3"
            >
              Settings
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab("password")}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === "password"
                  ? "border-blue-600 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              }`}
            >
              Change Password
            </button>
            <button
              onClick={() => setActiveTab("users")}
              className={`py-2 px-4 border-b-2 font-medium text-sm ${
                activeTab === "users"
                  ? "border-blue-600 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              }`}
            >
              Manage Users
            </button>
          </div>
        </div>

        {/* Password Change Tab */}
        {activeTab === "password" && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Change Your Password
            </h2>
            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>

              {passwordMessage && (
                <div
                  className={`text-sm ${
                    passwordMessage.includes("success")
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {passwordMessage}
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Update Password
              </button>
            </form>
          </div>
        )}

        {/* Manage Users Tab */}
        {activeTab === "users" && (
          <div className="space-y-6">
            {/* User Table */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <UserTable
                users={users}
                currentUserId={(session?.user as any)?.id}
                onUserDeleted={fetchUsers}
                onRoleUpdated={fetchUsers}
              />
            </div>

            {/* Add New User Form */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Add New User
              </h2>
              <form onSubmit={handleAddUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Role
                </label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value as "admin" | "viewer")}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                >
                  <option value="viewer">Viewer (Read-only)</option>
                  <option value="admin">Admin (Full access)</option>
                </select>
              </div>

              {userMessage && (
                <div
                  className={`text-sm ${
                    userMessage.includes("success")
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {userMessage}
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Add User
              </button>
            </form>
            </div>
          </div>
        )}

        {/* Sign Out */}
        <div className="mt-8">
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            Sign Out
          </button>
        </div>
      </main>
    </div>
  );
}
