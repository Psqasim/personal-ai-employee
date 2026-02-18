"use client";

import { useState } from "react";
import { ApprovalItem } from "@/lib/vault";

interface ApprovalCardProps {
  item: ApprovalItem;
  userRole: "admin" | "viewer";
  onApprove?: (filePath: string) => void;
  onReject?: (filePath: string, reason?: string) => void;
}

export function ApprovalCard({ item, userRole, onApprove, onReject }: ApprovalCardProps) {
  const [loading, setLoading] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [sendStatus, setSendStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [sendError, setSendError] = useState("");

  const isWhatsApp = item.category === "WhatsApp";

  const handleApprove = async () => {
    if (userRole !== "admin") return;
    setLoading(true);
    await onApprove?.(item.filePath);
    setLoading(false);
  };

  const handleApproveAndSend = async () => {
    if (userRole !== "admin") return;
    const chatId = item.metadata?.chat_id || item.metadata?.to || "";
    const message = item.content?.trim() || item.preview;
    if (!chatId || !message) {
      setSendError("Missing chat_id or message in item metadata");
      setSendStatus("error");
      return;
    }

    setLoading(true);
    setSendStatus("sending");
    setSendError("");

    // First approve (move file to Approved/)
    await onApprove?.(item.filePath);

    // Then send via WhatsApp
    try {
      const res = await fetch("/api/whatsapp/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, message }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSendStatus("sent");
      } else {
        setSendStatus("error");
        setSendError(data.error || "Send failed");
      }
    } catch (e: any) {
      setSendStatus("error");
      setSendError(e?.message || "Network error");
    }
    setLoading(false);
  };

  const handleReject = async () => {
    if (userRole !== "admin") return;
    setLoading(true);
    await onReject?.(item.filePath, rejectReason);
    setLoading(false);
    setShowRejectModal(false);
    setRejectReason("");
  };

  const categoryColors: Record<string, string> = {
    Email: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    LinkedIn: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200",
    Odoo: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
    WhatsApp: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    Facebook: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    Instagram: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
    Twitter: "bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-200",
  };

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`text-xs font-semibold px-2.5 py-0.5 rounded ${
                  categoryColors[item.category] || "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                }`}
              >
                {item.category}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {new Date(item.timestamp).toLocaleString()}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {item.title}
            </h3>
          </div>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
            {item.preview}
          </p>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline mt-2"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        </div>

        {expanded && (
          <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
            <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {item.content}
            </pre>
          </div>
        )}

        {userRole === "admin" && (
          <div className="flex flex-col gap-2">
            <div className="flex gap-3">
              {isWhatsApp ? (
                <button
                  onClick={handleApproveAndSend}
                  disabled={loading || sendStatus === "sent"}
                  className="flex-1 min-h-[44px] bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sendStatus === "sending"
                    ? "Sending..."
                    : sendStatus === "sent"
                    ? "✓ Sent!"
                    : "✓ Approve & Send"}
                </button>
              ) : (
                <button
                  onClick={handleApprove}
                  disabled={loading}
                  className="flex-1 min-h-[44px] bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Processing..." : "✓ Approve"}
                </button>
              )}
              <button
                onClick={() => setShowRejectModal(true)}
                disabled={loading}
                className="flex-1 min-h-[44px] bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ✗ Reject
              </button>
            </div>
            {sendStatus === "error" && sendError && (
              <p className="text-xs text-red-600 dark:text-red-400">{sendError}</p>
            )}
            {sendStatus === "sent" && (
              <p className="text-xs text-green-600 dark:text-green-400">Message sent via WhatsApp</p>
            )}
          </div>
        )}

        {userRole === "viewer" && (
          <div className="text-center text-sm text-gray-500 dark:text-gray-400 py-2">
            Read-only access - contact admin to approve
          </div>
        )}
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Reject Item
            </h3>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Optional: Reason for rejection..."
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white mb-4"
              rows={4}
            />
            <div className="flex gap-3">
              <button
                onClick={handleReject}
                disabled={loading}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
              >
                Confirm Reject
              </button>
              <button
                onClick={() => setShowRejectModal(false)}
                disabled={loading}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
