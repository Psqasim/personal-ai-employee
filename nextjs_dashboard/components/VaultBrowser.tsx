"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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

  const handleAction = async (action: string, filePath: string, itemId: string) => {
    setActionLoading(itemId);
    setMessage("");

    try {
      const endpoint =
        action === "retry"       ? "/api/vault/retry" :
        action === "archive"     ? "/api/vault/archive" :
        action === "mark-done"   ? "/api/vault/mark-done" :
                                   "/api/vault/create-task";

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

    const btnCls = "px-3 py-1 text-xs rounded-lg font-medium transition-all disabled:opacity-50";

    switch (section.path) {
      case "Needs_Action":
        return (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleAction("retry", item.filePath, itemId)}
            disabled={isLoading}
            className={`${btnCls} bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500/20`}
          >
            {isLoading ? "Retrying..." : "🔄 Retry"}
          </motion.button>
        );
      case "Done":
        return (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleAction("archive", item.filePath, itemId)}
            disabled={isLoading}
            className={`${btnCls} bg-gray-500/10 text-gray-400 border border-gray-500/20 hover:bg-gray-500/20`}
          >
            {isLoading ? "Archiving..." : "📦 Archive"}
          </motion.button>
        );
      case "In_Progress":
        return (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleAction("mark-done", item.filePath, itemId)}
            disabled={isLoading}
            className={`${btnCls} bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20`}
          >
            {isLoading ? "Marking..." : "✅ Mark Done"}
          </motion.button>
        );
      case "Inbox":
        return (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleAction("create-task", item.filePath, itemId)}
            disabled={isLoading}
            className={`${btnCls} bg-blue-500/10 text-blue-500 border border-blue-500/20 hover:bg-blue-500/20`}
          >
            {isLoading ? "Creating..." : "📝 Create Task"}
          </motion.button>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Vault Browser
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Browse all vault folders and files
        </p>
      </div>

      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`p-3 rounded-xl text-sm ${
              message.includes("success")
                ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                : "bg-red-500/10 text-red-500 border border-red-500/20"
            }`}
          >
            {message}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sections.map((section, index) => (
          <motion.div
            key={section.path}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="glass-card rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => toggleSection(section.name)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-white/5 transition-colors"
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
              <motion.span
                className="text-gray-400 dark:text-gray-500"
                animate={{ rotate: expandedSections.has(section.name) ? 90 : 0 }}
              >
                ▶
              </motion.span>
            </button>

            <AnimatePresence>
              {expandedSections.has(section.name) && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className="overflow-hidden"
                >
                  <div className="px-6 py-4 bg-white/[0.02] border-t border-white/5 max-h-[600px] overflow-y-auto">
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
                              className="rounded-xl p-4 bg-white/[0.03] border border-white/5"
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
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 line-clamp-2">
                                      {item.preview}
                                    </p>
                                  )}
                                </div>
                                <span className="px-2 py-1 text-xs font-medium bg-blue-500/10 text-blue-400 rounded-lg whitespace-nowrap border border-blue-500/20">
                                  {item.category}
                                </span>
                              </div>

                              <AnimatePresence>
                                {isExpanded && (
                                  <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="mb-3 space-y-2 text-xs overflow-hidden"
                                  >
                                    {item.metadata && (() => {
                                      const m = item.metadata;
                                      const rows: { label: string; value: string }[] = [];
                                      if (m.to)           rows.push({ label: "To",      value: String(m.to) });
                                      if (m.from)         rows.push({ label: "From",    value: String(m.from) });
                                      if (m.subject)      rows.push({ label: "Subject", value: String(m.subject) });
                                      if (m.status)       rows.push({ label: "Status",  value: String(m.status) });
                                      if (m.sent_at)      rows.push({ label: "Sent",    value: new Date(m.sent_at).toLocaleString() });
                                      if (m.created_at)   rows.push({ label: "Created", value: new Date(m.created_at).toLocaleString() });
                                      if (m.created_by)   rows.push({ label: "By",      value: String(m.created_by) });
                                      if (m.priority)     rows.push({ label: "Priority",value: String(m.priority) });
                                      if (m.chat_id)      rows.push({ label: "Chat ID", value: String(m.chat_id) });
                                      if (m.source)       rows.push({ label: "Source",  value: String(m.source) });
                                      return rows.length > 0 ? (
                                        <div className="rounded-lg p-2 space-y-1 bg-white/[0.03] border border-white/5">
                                          {rows.map(({ label, value }) => (
                                            <div key={label} className="flex gap-2">
                                              <span className="font-semibold text-gray-500 w-16 shrink-0">{label}:</span>
                                              <span className="text-gray-300 break-all">{value}</span>
                                            </div>
                                          ))}
                                        </div>
                                      ) : null;
                                    })()}
                                    {(() => {
                                      const body = item.metadata?.draft_body || item.content || item.metadata?.body || "";
                                      return body ? (
                                        <div>
                                          <p className="font-semibold text-gray-500 mb-1">Message:</p>
                                          <div className="rounded-lg p-2 text-gray-300 whitespace-pre-wrap max-h-[200px] overflow-y-auto bg-white/[0.03] border border-white/5">
                                            {body}
                                          </div>
                                        </div>
                                      ) : null;
                                    })()}
                                  </motion.div>
                                )}
                              </AnimatePresence>

                              <div className="flex items-center gap-2 justify-between">
                                <button
                                  onClick={() => toggleItemDetails(itemId)}
                                  className="text-xs text-cyan-500 hover:text-cyan-400 transition-colors"
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
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
