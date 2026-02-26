"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { ApprovalItem } from "@/lib/vault";
import { AnimatedModal } from "./AnimatedLayout";

const Tilt = dynamic(() => import("react-parallax-tilt"), { ssr: false });

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

    await onApprove?.(item.filePath);

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

  const categoryConfig: Record<string, { color: string; glow: string }> = {
    Email: {
      color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      glow: "rgba(59, 130, 246, 0.1)",
    },
    LinkedIn: {
      color: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
      glow: "rgba(99, 102, 241, 0.1)",
    },
    Odoo: {
      color: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      glow: "rgba(168, 85, 247, 0.1)",
    },
    WhatsApp: {
      color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      glow: "rgba(16, 185, 129, 0.1)",
    },
    Facebook: {
      color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      glow: "rgba(59, 130, 246, 0.1)",
    },
    Instagram: {
      color: "bg-pink-500/10 text-pink-400 border-pink-500/20",
      glow: "rgba(236, 72, 153, 0.1)",
    },
    Twitter: {
      color: "bg-sky-500/10 text-sky-400 border-sky-500/20",
      glow: "rgba(14, 165, 233, 0.1)",
    },
  };

  const catStyle = categoryConfig[item.category] || {
    color: "bg-gray-500/10 text-gray-400 border-gray-500/20",
    glow: "rgba(107, 114, 128, 0.1)",
  };

  return (
    <>
      <Tilt
        tiltMaxAngleX={3}
        tiltMaxAngleY={3}
        glareEnable={true}
        glareMaxOpacity={0.05}
        glareColor="#ffffff"
        glarePosition="all"
        perspective={1000}
        transitionSpeed={400}
        scale={1.01}
      >
        <div
          className="glass-card rounded-2xl p-6 transition-all duration-300"
          style={{ boxShadow: `0 4px 24px ${catStyle.glow}` }}
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${catStyle.color}`}
                >
                  {item.category}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-500">
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
              className="text-sm text-cyan-600 dark:text-cyan-400 hover:text-cyan-500 dark:hover:text-cyan-300 mt-2 transition-colors"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          </div>

          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="mb-4 p-4 rounded-xl bg-black/5 dark:bg-white/5 border border-gray-200/50 dark:border-white/5">
                  <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {item.content}
                  </pre>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {userRole === "admin" && (
            <div className="flex flex-col gap-2">
              <div className="flex gap-3">
                {isWhatsApp ? (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleApproveAndSend}
                    disabled={loading || sendStatus === "sent"}
                    className="flex-1 min-h-[44px] bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-medium py-2 px-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-500/20"
                  >
                    {sendStatus === "sending"
                      ? "Sending..."
                      : sendStatus === "sent"
                        ? "Sent!"
                        : "Approve & Send"}
                  </motion.button>
                ) : (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleApprove}
                    disabled={loading}
                    className="flex-1 min-h-[44px] bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-medium py-2 px-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-500/20"
                  >
                    {loading ? "Processing..." : "Approve"}
                  </motion.button>
                )}
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowRejectModal(true)}
                  disabled={loading}
                  className="flex-1 min-h-[44px] bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white font-medium py-2 px-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-500/20"
                >
                  Reject
                </motion.button>
              </div>
              {sendStatus === "error" && sendError && (
                <p className="text-xs text-red-400">{sendError}</p>
              )}
              {sendStatus === "sent" && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-xs text-emerald-400"
                >
                  Message sent via WhatsApp
                </motion.p>
              )}
            </div>
          )}

          {userRole === "viewer" && (
            <div className="text-center text-sm text-gray-500 dark:text-gray-500 py-2">
              Read-only access — contact admin to approve
            </div>
          )}
        </div>
      </Tilt>

      {/* Reject Modal */}
      <AnimatedModal isOpen={showRejectModal} onClose={() => setShowRejectModal(false)}>
        <div className="glass-card rounded-2xl p-6 max-w-md mx-auto">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Reject Item
          </h3>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Optional: Reason for rejection..."
            className="w-full p-3 rounded-xl bg-black/5 dark:bg-white/5 border border-gray-200/50 dark:border-white/10 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all mb-4"
            rows={4}
          />
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleReject}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-red-500 to-rose-600 text-white font-medium py-2 px-4 rounded-xl transition-all disabled:opacity-50 shadow-lg shadow-red-500/20"
            >
              Confirm Reject
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowRejectModal(false)}
              disabled={loading}
              className="flex-1 bg-gray-500/20 hover:bg-gray-500/30 text-gray-700 dark:text-gray-300 font-medium py-2 px-4 rounded-xl transition-all disabled:opacity-50"
            >
              Cancel
            </motion.button>
          </div>
        </div>
      </AnimatedModal>
    </>
  );
}
