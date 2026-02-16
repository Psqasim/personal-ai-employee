"use client";

import { useState } from "react";

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type TaskType = "email" | "linkedin" | "whatsapp";

export function CreateTaskModal({ isOpen, onClose, onSuccess }: CreateTaskModalProps) {
  const [taskType, setTaskType] = useState<TaskType>("email");
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const maxChars = 3000;
  const remainingChars = maxChars - content.length;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/tasks/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: taskType,
          to: recipient,
          subject: taskType === "email" ? subject : undefined,
          content,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        // Reset form
        setRecipient("");
        setSubject("");
        setContent("");
        setTaskType("email");
        onSuccess();
        onClose();
      } else {
        setError(data.error || "Failed to create task");
      }
    } catch (error) {
      setError("Error creating task");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Create New Task
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Create a draft that will appear in Pending Approvals
              </p>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="Close"
            >
              <span className="text-xl">✕</span>
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Task Type */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Task Type
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setTaskType("email")}
                className={`px-4 py-3 rounded-lg border-2 font-medium transition-all ${
                  taskType === "email"
                    ? "border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                    : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                }`}
              >
                <span className="text-2xl mb-1 block">📧</span>
                <span className="text-sm">Email</span>
              </button>
              <button
                type="button"
                onClick={() => setTaskType("linkedin")}
                className={`px-4 py-3 rounded-lg border-2 font-medium transition-all ${
                  taskType === "linkedin"
                    ? "border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                    : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                }`}
              >
                <span className="text-2xl mb-1 block">💼</span>
                <span className="text-sm">LinkedIn</span>
              </button>
              <button
                type="button"
                onClick={() => setTaskType("whatsapp")}
                className={`px-4 py-3 rounded-lg border-2 font-medium transition-all ${
                  taskType === "whatsapp"
                    ? "border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                    : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                }`}
              >
                <span className="text-2xl mb-1 block">💬</span>
                <span className="text-sm">WhatsApp</span>
              </button>
            </div>
          </div>

          {/* Recipient */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              {taskType === "email" ? "To (Email)" : taskType === "whatsapp" ? "To (Phone)" : "Recipient"}
            </label>
            <input
              type={taskType === "email" ? "email" : "text"}
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              required
              placeholder={
                taskType === "email"
                  ? "client@example.com"
                  : taskType === "whatsapp"
                  ? "923001234567"
                  : "Recipient name or handle"
              }
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          {/* Subject (Email only) */}
          {taskType === "email" && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
                placeholder="Project Update"
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          )}

          {/* Content */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300">
                {taskType === "email" ? "Message" : taskType === "linkedin" ? "Post Content" : "Message"}
              </label>
              <span
                className={`text-xs font-medium ${
                  remainingChars < 100
                    ? "text-red-600 dark:text-red-400"
                    : "text-gray-500 dark:text-gray-400"
                }`}
              >
                {remainingChars} / {maxChars} characters
              </span>
            </div>
            <textarea
              value={content}
              onChange={(e) => {
                if (e.target.value.length <= maxChars) {
                  setContent(e.target.value);
                }
              }}
              required
              rows={8}
              placeholder={
                taskType === "email"
                  ? "Hi there,\n\nI wanted to follow up on..."
                  : taskType === "linkedin"
                  ? "Excited to share that..."
                  : "Hello! I wanted to reach out about..."
              }
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-red-600 dark:text-red-400 text-sm font-medium">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2.5 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !recipient || !content || (taskType === "email" && !subject)}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Creating...
                </span>
              ) : (
                "Create Draft"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
