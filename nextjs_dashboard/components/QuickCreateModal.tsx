"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AnimatedModal } from "./AnimatedLayout";

type TaskType = "email" | "whatsapp" | "odoo" | "linkedin";
type AiStep = "prompt" | "preview" | "done";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const TABS: { type: TaskType; icon: string; label: string }[] = [
  { type: "email",    icon: "📧", label: "Email"    },
  { type: "whatsapp", icon: "💬", label: "WhatsApp" },
  { type: "odoo",     icon: "🧾", label: "Invoice"  },
  { type: "linkedin", icon: "🔗", label: "LinkedIn" },
];

const INPUT_CLS =
  "w-full px-4 py-3 rounded-xl bg-black/5 dark:bg-white/5 border border-gray-200/50 dark:border-white/10 " +
  "text-gray-900 dark:text-white placeholder-gray-400 " +
  "focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all text-sm";

export function QuickCreateModal({ isOpen, onClose, onSuccess }: Props) {
  const [taskType, setTaskType] = useState<TaskType>("email");
  const [loading, setLoading]     = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError]         = useState("");
  const [aiPrompt, setAiPrompt]   = useState("");
  const [aiStep, setAiStep]       = useState<AiStep>("prompt");
  const abortRef = useRef<AbortController | null>(null);

  const [recipient, setRecipient] = useState("");
  const [subject, setSubject]     = useState("");
  const [content, setContent]     = useState("");

  const [waRecipient, setWaRecipient] = useState("");
  const [waMessage, setWaMessage]     = useState("");

  const [customer, setCustomer]           = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [amount, setAmount]               = useState("");
  const [currency, setCurrency]           = useState("USD");
  const [description, setDescription]     = useState("");

  const [liStep, setLiStep]       = useState<"input" | "preview" | "done">("input");
  const [topic, setTopic]         = useState("");
  const [postText, setPostText]   = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState("");
  const [liPosting, setLiPosting] = useState(false);
  const [liResult, setLiResult]   = useState<{ postUrl: string; hasImage: boolean } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function resetAll() {
    setAiPrompt(""); setAiStep("prompt"); setError("");
    setRecipient(""); setSubject(""); setContent("");
    setWaRecipient(""); setWaMessage("");
    setCustomer(""); setCustomerEmail(""); setAmount(""); setCurrency("USD"); setDescription("");
    setLiStep("input"); setTopic(""); setPostText("");
    setImageFile(null); setImagePreview(""); setLiResult(null);
  }

  function handleClose() {
    resetAll();
    setTaskType("email");
    onClose();
  }

  function handleTabChange(t: TaskType) {
    setTaskType(t);
    setAiStep("prompt");
    setError("");
  }

  function cancelGeneration() {
    abortRef.current?.abort();
    setGenerating(false);
    setError("Generation cancelled");
  }

  async function handleAiGenerate() {
    if (!aiPrompt.trim()) { setError("Describe what you want first"); return; }
    if (loading) return;
    abortRef.current?.abort(); // Cancel any previous request
    const controller = new AbortController();
    abortRef.current = controller;
    setError(""); setGenerating(true);
    try {
      const aiType = taskType === "odoo" ? "invoice" : taskType;
      const res = await fetch("/api/ai-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: aiType, prompt: aiPrompt }),
        signal: controller.signal,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Generation failed");

      if (taskType === "email") {
        setSubject(data.subject || "");
        setContent(data.body || "");
      } else if (taskType === "whatsapp") {
        setWaMessage(data.message || "");
      } else if (taskType === "odoo") {
        setCustomer(data.customer || "");
        setAmount(String(data.amount || ""));
        setCurrency(data.currency || "USD");
        setDescription(data.description || "");
      }
      setAiStep("preview");
    } catch (e: any) {
      if (e.name === "AbortError") return; // User cancelled, don't show error
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  function handleImageChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  }

  function removeImage() {
    setImageFile(null); setImagePreview("");
    if (fileRef.current) fileRef.current.value = "";
  }

  async function handleLiGenerate() {
    if (!topic.trim()) { setError("Enter a topic first"); return; }
    setError(""); setGenerating(true);
    try {
      const res = await fetch("/api/linkedin/post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "generate", topic }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Generation failed");
      setPostText(data.postText);
      setLiStep("preview");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  async function handleLinkedInPost() {
    if (!postText || postText.length > 3000) return;
    setError(""); setLiPosting(true);
    try {
      let imageBase64: string | undefined;
      let imageMime: string | undefined;
      if (imageFile) {
        imageMime = imageFile.type;
        imageBase64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve((e.target?.result as string).split(",")[1]);
          reader.onerror = reject;
          reader.readAsDataURL(imageFile);
        });
      }
      const res = await fetch("/api/linkedin/post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "post", postText, imageBase64, imageMime }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Post failed");
      setLiResult({ postUrl: data.postUrl, hasImage: data.hasImage });
      setLiStep("done");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLiPosting(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (generating) return; // Block submit while AI is generating
    setLoading(true); setError("");
    try {
      const payload: Record<string, any> = { type: taskType };
      if (taskType === "odoo") {
        payload.customer = customer;
        payload.customer_email = customerEmail;
        payload.amount = parseFloat(amount) || 0;
        payload.currency = currency;
        payload.description = description;
      } else if (taskType === "whatsapp") {
        payload.to = waRecipient;
        payload.content = waMessage;
      } else {
        payload.to = recipient;
        payload.content = content;
        payload.subject = subject;
      }
      const res = await fetch("/api/tasks/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        resetAll();
        onSuccess?.();
        handleClose();
      } else {
        setError(data.error || "Failed to create task");
      }
    } catch {
      setError("Error creating task");
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  const liCharOk = postText.length > 0 && postText.length <= 3000;

  const PLACEHOLDERS: Record<string, string> = {
    email:    "e.g. Write a follow-up email to Ali about the project invoice we discussed last week",
    whatsapp: "e.g. Message Tayyab saying the payment has been received and thank him",
    odoo:     "e.g. Invoice Ali for 5000 PKR for web design services delivered in January",
  };

  const AI_LABELS: Record<string, string> = {
    email:    "Describe the email you want to send",
    whatsapp: "Describe the WhatsApp message",
    odoo:     "Describe the invoice (who, how much, for what)",
  };

  return (
    <AnimatedModal isOpen={isOpen} onClose={handleClose}>
      <div className="glass-card rounded-t-3xl sm:rounded-3xl w-full max-w-2xl mx-auto max-h-[95vh] sm:max-h-[92vh] overflow-y-auto flex flex-col">

        {/* Header */}
        <div className="px-4 sm:px-6 pt-4 sm:pt-5 pb-3 sm:pb-4 border-b border-white/10 shrink-0">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Quick Create</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Describe what you want — Claude AI will generate it
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleClose}
              className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors text-lg"
            >
              ✕
            </motion.button>
          </div>

          <div className="grid grid-cols-4 gap-1.5 sm:gap-2">
            {TABS.map((tab) => (
              <motion.button
                key={tab.type}
                type="button"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => handleTabChange(tab.type)}
                className={`flex flex-col items-center gap-1 sm:gap-1.5 py-2 sm:py-3 rounded-xl border transition-all ${
                  taskType === tab.type
                    ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-500 shadow-lg shadow-cyan-500/10"
                    : "border-white/10 text-gray-400 hover:border-white/20 hover:bg-white/5"
                }`}
              >
                <span className="text-xl sm:text-2xl">{tab.icon}</span>
                <span className="text-xs font-semibold">{tab.label}</span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div className="px-4 sm:px-6 py-4 sm:py-5 space-y-4 sm:space-y-5 flex-1">

          {/* LINKEDIN TAB */}
          {taskType === "linkedin" && (
            <>
              {liStep === "done" && liResult && (
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="text-center py-10 space-y-4"
                >
                  <motion.div
                    className="text-5xl"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.5 }}
                  >
                    🎉
                  </motion.div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">Posted Successfully!</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Your post is live on LinkedIn{liResult.hasImage ? " with image" : ""}.
                  </p>
                  <motion.a
                    whileHover={{ scale: 1.05 }}
                    href={liResult.postUrl} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25"
                  >
                    View Post on LinkedIn ↗
                  </motion.a>
                  <div>
                    <button onClick={() => { setLiStep("input"); setTopic(""); setPostText(""); setImageFile(null); setImagePreview(""); setLiResult(null); }}
                      className="text-sm text-gray-400 hover:text-white transition-colors">
                      Post another
                    </button>
                  </div>
                </motion.div>
              )}

              {(liStep === "input" || liStep === "preview") && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                      What should the post be about?
                    </label>
                    <div className="flex flex-col sm:flex-row gap-2">
                      <input
                        type="text" value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleLiGenerate()}
                        placeholder="e.g. AI trends in 2026, new feature launch..."
                        className={`flex-1 ${INPUT_CLS}`}
                      />
                      <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={handleLiGenerate} disabled={generating || !topic.trim()}
                        className="w-full sm:w-auto px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 disabled:opacity-50 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-1.5"
                      >
                        {generating
                          ? <><motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>⟳</motion.span> Generating...</>
                          : <>{liStep === "preview" ? "Regenerate" : "Generate"}</>}
                      </motion.button>
                    </div>
                  </div>

                  <AnimatePresence>
                    {liStep === "preview" && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-4 overflow-hidden"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1.5">
                            <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                              Post Content <span className="text-gray-500">(edit freely)</span>
                            </label>
                            <span className={`text-xs font-mono ${postText.length > 3000 ? "text-red-500" : postText.length > 2500 ? "text-amber-500" : "text-gray-500"}`}>
                              {postText.length} / 3000
                            </span>
                          </div>
                          <textarea value={postText} onChange={(e) => setPostText(e.target.value)} rows={8}
                            className={`${INPUT_CLS} resize-y leading-relaxed`}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                            Attach Image <span className="text-gray-500">(optional)</span>
                          </label>
                          {imagePreview ? (
                            <div className="relative inline-block">
                              <img src={imagePreview} alt="Preview" className="h-32 rounded-xl object-cover border border-white/10" />
                              <button onClick={removeImage} className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600 shadow-lg">✕</button>
                            </div>
                          ) : (
                            <button onClick={() => fileRef.current?.click()}
                              className="flex items-center gap-2 border-2 border-dashed border-white/10 rounded-xl px-4 py-3 text-sm text-gray-400 hover:border-cyan-500/30 hover:text-cyan-400 transition-colors">
                              📷 Click to attach image
                            </button>
                          )}
                          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/gif" onChange={handleImageChange} className="hidden" />
                        </div>

                        {/* LinkedIn preview */}
                        <div className="glass-card rounded-2xl overflow-hidden">
                          <div className="px-4 py-2 border-b border-white/10">
                            <span className="text-xs text-gray-500">LinkedIn Preview</span>
                          </div>
                          <div className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0">AI</div>
                              <div>
                                <div className="text-sm font-semibold text-gray-900 dark:text-white leading-tight">Your Name</div>
                                <div className="text-xs text-gray-500">Just now</div>
                              </div>
                            </div>
                            {imagePreview && <img src={imagePreview} alt="" className="w-full rounded-xl mb-3 max-h-40 object-cover" />}
                            <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">{postText}</p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {error && (
                    <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
                      className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-400">
                      {error}
                    </motion.div>
                  )}

                  <div className="flex justify-between items-center pt-2 border-t border-white/10">
                    <button onClick={handleClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors font-medium">Cancel</button>
                    {liStep === "preview" && (
                      <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={handleLinkedInPost} disabled={liPosting || !liCharOk}
                        className="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-indigo-600 disabled:opacity-50 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/25 flex items-center gap-2"
                      >
                        {liPosting
                          ? <><motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>⟳</motion.span> Posting...</>
                          : <>🚀 Post to LinkedIn{imageFile ? " + Image" : ""}</>}
                      </motion.button>
                    )}
                  </div>
                </>
              )}
            </>
          )}

          {/* EMAIL / WHATSAPP / INVOICE */}
          {taskType !== "linkedin" && (
            <form onSubmit={handleSubmit} className="space-y-5">

              {/* AI Prompt */}
              <div className="glass-card rounded-2xl p-4 space-y-3 border-cyan-500/10">
                <div className="flex items-center gap-2">
                  <span className="text-base">✨</span>
                  <label className="text-sm font-semibold text-cyan-600 dark:text-cyan-400">
                    {AI_LABELS[taskType]}
                  </label>
                  <span className="text-xs bg-cyan-500/10 text-cyan-500 px-2 py-0.5 rounded-full font-medium border border-cyan-500/20">Claude AI</span>
                </div>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="text"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); if (!generating && !loading) handleAiGenerate(); } }}
                    placeholder={PLACEHOLDERS[taskType]}
                    disabled={loading}
                    className={INPUT_CLS}
                  />
                  {generating ? (
                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={cancelGeneration}
                      className="w-full sm:w-auto px-4 py-2 bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-xl text-sm font-semibold shadow-lg shadow-red-500/25 flex items-center justify-center gap-1.5"
                    >
                      <motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>⟳</motion.span>
                      Cancel
                    </motion.button>
                  ) : (
                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={handleAiGenerate}
                      disabled={loading || !aiPrompt.trim()}
                      className="w-full sm:w-auto px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-1.5"
                    >
                      {aiStep === "preview" ? "Regenerate" : "Generate"}
                    </motion.button>
                  )}
                </div>
                {aiStep === "preview" && (
                  <p className="text-xs text-cyan-500 flex items-center gap-1">
                    <span>✅</span> AI generated — edit freely below before submitting
                  </p>
                )}
              </div>

              {/* INVOICE fields */}
              {taskType === "odoo" && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Customer Name</label>
                    <input type="text" value={customer} onChange={(e) => setCustomer(e.target.value)} required placeholder="Acme Corp" className={INPUT_CLS} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                      Customer Email <span className="text-gray-500">(optional)</span>
                    </label>
                    <input type="email" value={customerEmail} onChange={(e) => setCustomerEmail(e.target.value)} placeholder="client@example.com" className={INPUT_CLS} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Amount</label>
                      <input type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required placeholder="500.00" className={INPUT_CLS} />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Currency</label>
                      <select value={currency} onChange={(e) => setCurrency(e.target.value)} className={INPUT_CLS}>
                        {["USD", "EUR", "GBP", "PKR", "AED", "SAR"].map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Description / Service</label>
                    <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} required placeholder="Consulting services — Q1 2026" className={INPUT_CLS} />
                    <p className="text-xs text-gray-500 mt-1.5">Draft queued in Pending Approvals — approve to create in Odoo.</p>
                  </div>
                </>
              )}

              {/* EMAIL fields */}
              {taskType === "email" && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">To (Email address)</label>
                    <input type="email" value={recipient} onChange={(e) => setRecipient(e.target.value)} required placeholder="client@example.com" className={INPUT_CLS} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">Subject</label>
                    <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)} required placeholder="Project Update — Q1 Review" className={INPUT_CLS} />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Email Body</label>
                      <span className={`text-xs font-mono ${content.length > 2900 ? "text-red-500" : "text-gray-500"}`}>
                        {content.length} / 3000
                      </span>
                    </div>
                    <textarea
                      value={content}
                      onChange={(e) => { if (e.target.value.length <= 3000) setContent(e.target.value); }}
                      required rows={8}
                      placeholder={"Hi there,\n\nI wanted to follow up on..."}
                      className={`${INPUT_CLS} resize-none`}
                    />
                    <p className="text-xs text-gray-500 mt-1.5">
                      Draft goes to Pending Approvals for review before sending.
                    </p>
                  </div>
                </>
              )}

              {/* WHATSAPP fields */}
              {taskType === "whatsapp" && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1.5">To (Contact name or phone)</label>
                    <input type="text" value={waRecipient} onChange={(e) => setWaRecipient(e.target.value)} required placeholder="Ali Hassan or 923001234567" className={INPUT_CLS} />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Message</label>
                      <span className={`text-xs font-mono ${waMessage.length > 2900 ? "text-red-500" : "text-gray-500"}`}>
                        {waMessage.length} / 3000
                      </span>
                    </div>
                    <textarea
                      value={waMessage}
                      onChange={(e) => { if (e.target.value.length <= 3000) setWaMessage(e.target.value); }}
                      required rows={6}
                      placeholder="Hello! I wanted to reach out about..."
                      className={`${INPUT_CLS} resize-none`}
                    />
                    <p className="text-xs text-emerald-500 mt-1.5 flex items-center gap-1">
                      <span>⚡</span> WhatsApp messages are sent directly — no approval needed.
                    </p>
                  </div>
                </>
              )}

              {error && (
                <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
                  className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                  <p className="text-red-400 text-sm font-medium">{error}</p>
                </motion.div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-white/10">
                <button type="button" onClick={handleClose}
                  className="px-5 py-2.5 text-sm font-semibold text-gray-400 hover:text-white transition-colors rounded-xl hover:bg-white/5">
                  Cancel
                </button>
                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  disabled={
                    loading || generating ||
                    (taskType === "odoo"     ? !customer || !amount || !description :
                     taskType === "email"    ? !recipient || !subject || !content :
                     taskType === "whatsapp" ? !waRecipient || !waMessage : false)
                  }
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
                >
                  {loading ? (
                    <><motion.div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} /> Creating...</>
                  ) : taskType === "whatsapp" ? "⚡ Send Now" :
                    taskType === "odoo"     ? "🧾 Create Invoice Draft" :
                                             "📧 Create Email Draft"}
                </motion.button>
              </div>
            </form>
          )}

        </div>
      </div>
    </AnimatedModal>
  );
}
