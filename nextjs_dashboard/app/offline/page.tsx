"use client";

import { useState } from "react";

export default function OfflinePage() {
  const [retrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      if (res.ok) {
        window.location.href = "/dashboard";
        return;
      }
    } catch {
      // Still offline
    }
    setRetrying(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center max-w-md mx-auto px-6">
        <div className="mb-8">
          <div className="text-8xl mb-4">📡</div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
            You&apos;re Offline
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg leading-relaxed">
            The dashboard requires an internet connection. Check your network and try again.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700 mb-8">
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            While offline, use Obsidian directly:
          </p>
          <code className="text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-3 py-1 rounded-lg font-mono">
            vault/Pending_Approval/
          </code>
        </div>

        <button
          onClick={handleRetry}
          disabled={retrying}
          className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
        >
          {retrying ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Checking connection...
            </span>
          ) : (
            "🔄 Retry Connection"
          )}
        </button>

        <p className="mt-4 text-xs text-gray-400 dark:text-gray-500">
          Your AI employee continues working in the background
        </p>
      </div>
    </div>
  );
}
