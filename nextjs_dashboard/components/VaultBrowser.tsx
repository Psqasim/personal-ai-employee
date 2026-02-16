"use client";

import { useState } from "react";
import { VaultSection, ApprovalItem } from "@/lib/vault";

interface VaultBrowserProps {
  sections: VaultSection[];
  onRefresh: () => void;
}

export function VaultBrowser({ sections, onRefresh }: VaultBrowserProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const toggleSection = (sectionName: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionName)) {
      newExpanded.delete(sectionName);
    } else {
      newExpanded.add(sectionName);
    }
    setExpandedSections(newExpanded);
  };

  const toggleItemDetails = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const handleAction = async (
    action: string,
    filePath: string,
    itemId: string
  ) => {
    setActionLoading(itemId);
    setMessage("");

    try {
      const endpoint =
        action === "retry"
          ? "/api/vault/retry"
          : action === "archive"
          ? "/api/vault/archive"
          : action === "mark-done"
          ? "/api/vault/mark-done"
          : "/api/vault/create-task";

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filePath }),
      });

      if (res.ok) {
        setMessage(`Action "${action}" completed successfully`);
        onRefresh();
        setTimeout(() => setMessage(""), 3000);
      } else {
        const data = await res.json();
        setMessage(data.error || "Action failed");
      }
    } catch (error) {
      setMessage("Error performing action");
    } finally {
      setActionLoading(null);
    }
  };

  const getActionButtons = (section: VaultSection, item: ApprovalItem) => {
    const itemId = `${section.path}-${item.id}`;
    const isLoading = actionLoading === itemId;

    switch (section.path) {
      case "Needs_Action":
        return (
          <button
            onClick={() => handleAction("retry", item.filePath, itemId)}
            disabled={isLoading}
            className="px-3 py-1 text-xs bg-orange-600 hover:bg-orange-700 text-white rounded transition-colors disabled:opacity-50"
          >
            {isLoading ? "⏳ Retrying..." : "🔄 Retry"}
          </button>
        );
      case "Done":
        return (
          <button
            onClick={() => handleAction("archive", item.filePath, itemId)}
            disabled={isLoading}
            className="px-3 py-1 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors disabled:opacity-50"
          >
            {isLoading ? "⏳ Archiving..." : "📦 Archive"}
          </button>
        );
      case "In_Progress":
        return (
          <button
            onClick={() => handleAction("mark-done", item.filePath, itemId)}
            disabled={isLoading}
            className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded transition-colors disabled:opacity-50"
          >
            {isLoading ? "⏳ Marking..." : "✅ Mark Done"}
          </button>
        );
      case "Inbox":
        return (
          <button
            onClick={() => handleAction("create-task", item.filePath, itemId)}
            disabled={isLoading}
            className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50"
          >
            {isLoading ? "⏳ Creating..." : "📝 Create Task"}
          </button>
        );
      default:
        // Logs and Briefings are view-only
        return null;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Vault Browser
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Browse all vault folders and files (Admin only)
        </p>
      </div>

      {message && (
        <div
          className={`p-3 rounded-lg text-sm ${
            message.includes("success")
              ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400"
              : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400"
          }`}
        >
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sections.map((section) => (
          <div
            key={section.path}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
          >
            <button
              onClick={() => toggleSection(section.name)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-3xl">{section.icon}</span>
                <div className="text-left">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {section.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {section.count} {section.count === 1 ? "item" : "items"}
                  </p>
                </div>
              </div>
              <span className="text-gray-400 dark:text-gray-500">
                {expandedSections.has(section.name) ? "▼" : "▶"}
              </span>
            </button>

            {expandedSections.has(section.name) && (
              <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 max-h-[600px] overflow-y-auto">
                {section.items.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                    No items in this folder
                  </p>
                ) : (
                  <div className="space-y-3">
                    {section.items.map((item) => {
                      const itemId = `${section.path}-${item.id}`;
                      const isExpanded = expandedItems.has(itemId);

                      return (
                        <div
                          key={item.id}
                          className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
                        >
                          <div className="flex items-start justify-between gap-3 mb-3">
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                                {item.title}
                              </h4>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {new Date(item.timestamp).toLocaleDateString()} at{" "}
                                {new Date(item.timestamp).toLocaleTimeString()}
                              </p>
                              {!isExpanded && (
                                <p className="text-xs text-gray-600 dark:text-gray-300 mt-2 line-clamp-2">
                                  {item.preview}
                                </p>
                              )}
                            </div>
                            <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded whitespace-nowrap">
                              {item.category}
                            </span>
                          </div>

                          {isExpanded && (
                            <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-900 rounded text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                              {item.content}
                            </div>
                          )}

                          <div className="flex items-center gap-2 justify-between">
                            <button
                              onClick={() => toggleItemDetails(itemId)}
                              className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                            >
                              {isExpanded ? "▲ Hide Details" : "▼ Show Details"}
                            </button>
                            {getActionButtons(section, item)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
