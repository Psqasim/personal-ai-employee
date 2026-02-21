"use client";

import { useState, useRef } from "react";

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
  "w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg " +
  "bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 " +
  "focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all";

export function QuickCreateModal({ isOpen, onClose, onSuccess }: Props) {
  // ── Active tab ────────────────────────────────────────────────────────
  const [taskType, setTaskType] = useState<TaskType>("email");

  // ── Shared ────────────────────────────────────────────────────────────
  const [loading, setLoading]     = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError]         = useState("");

  // ── AI prompt (shared across email/whatsapp/odoo) ─────────────────────
  const [aiPrompt, setAiPrompt]   = useState("");
  const [aiStep, setAiStep]       = useState<AiStep>("prompt");

  // ── Email ─────────────────────────────────────────────────────────────
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject]     = useState("");
  const [content, setContent]     = useState("");

  // ── WhatsApp ──────────────────────────────────────────────────────────
  const [waRecipient, setWaRecipient] = useState("");
  const [waMessage, setWaMessage]     = useState("");

  // ── Odoo Invoice ──────────────────────────────────────────────────────
  const [customer, setCustomer]           = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [amount, setAmount]               = useState("");
  const [currency, setCurrency]           = useState("USD");
  const [description, setDescription]     = useState("");

  // ── LinkedIn ──────────────────────────────────────────────────────────
  const [liStep, setLiStep]       = useState<"input" | "preview" | "done">("input");
  const [topic, setTopic]         = useState("");
  const [postText, setPostText]   = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState("");
  const [liPosting, setLiPosting] = useState(false);
  const [liResult, setLiResult]   = useState<{ postUrl: string; hasImage: boolean } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // ── Helpers ───────────────────────────────────────────────────────────
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

  // ── AI generate for email / whatsapp / invoice ────────────────────────
  async function handleAiGenerate() {
    if (!aiPrompt.trim()) { setError("Describe what you want first"); return; }
    setError(""); setGenerating(true);
    try {
      // Map "odoo" → "invoice" for the AI generate API
      const aiType = taskType === "odoo" ? "invoice" : taskType;
      const res = await fetch("/api/ai-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: aiType, prompt: aiPrompt }),
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
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  // ── LinkedIn handlers ─────────────────────────────────────────────────
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

  // ── Email / WhatsApp / Odoo submit ────────────────────────────────────
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
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

  // ── AI prompt placeholders per tab ────────────────────────────────────
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[92vh] overflow-y-auto flex flex-col">

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="px-6 pt-5 pb-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">✨ Quick Create</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Describe what you want — Claude AI will generate it for you
              </p>
            </div>
            <button
              onClick={handleClose}
              className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors text-lg"
            >
              ✕
            </button>
          </div>

          {/* Type tabs */}
          <div className="grid grid-cols-4 gap-2">
            {TABS.map((tab) => (
              <button
                key={tab.type}
                type="button"
                onClick={() => handleTabChange(tab.type)}
                className={`flex flex-col items-center gap-1.5 py-3 rounded-xl border-2 font-medium transition-all ${
                  taskType === tab.type
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 shadow-sm"
                    : "border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                }`}
              >
                <span className="text-2xl">{tab.icon}</span>
                <span className="text-xs font-semibold">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Body ───────────────────────────────────────────────────── */}
        <div className="px-6 py-5 space-y-5 flex-1">

          {/* ══════════════════════════════════════════════════════════════
              LINKEDIN TAB (unchanged flow)
          ══════════════════════════════════════════════════════════════ */}
          {taskType === "linkedin" && (
            <>
              {liStep === "done" && liResult && (
                <div className="text-center py-10 space-y-4">
                  <div className="text-5xl">🎉</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">Posted Successfully!</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Your post is live on LinkedIn{liResult.hasImage ? " with image" : ""}.
                  </p>
                  <a
                    href={liResult.postUrl} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm transition-colors"
                  >
                    View Post on LinkedIn ↗
                  </a>
                  <div>
                    <button onClick={() => { setLiStep("input"); setTopic(""); setPostText(""); setImageFile(null); setImagePreview(""); setLiResult(null); }}
                      className="text-sm text-gray-500 dark:text-gray-400 hover:underline">
                      Post another
                    </button>
                  </div>
                </div>
              )}

              {(liStep === "input" || liStep === "preview") && (
                <>
                  {/* Topic input + generate */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                      What should the post be about?
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text" value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleLiGenerate()}
                        placeholder="e.g. AI trends in 2026, new feature launch, productivity tips..."
                        className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button onClick={handleLiGenerate} disabled={generating || !topic.trim()}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap">
                        {generating
                          ? <><span className="animate-spin inline-block">⟳</span> Generating...</>
                          : <>✨ {liStep === "preview" ? "Regenerate" : "Generate"}</>}
                      </button>
                    </div>
                  </div>

                  {liStep === "preview" && (
                    <>
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                            Post Content <span className="font-normal text-gray-400">(edit freely)</span>
                          </label>
                          <span className={`text-xs font-mono ${postText.length > 3000 ? "text-red-500" : postText.length > 2500 ? "text-yellow-500" : "text-gray-400"}`}>
                            {postText.length} / 3000
                          </span>
                        </div>
                        <textarea value={postText} onChange={(e) => setPostText(e.target.value)} rows={8}
                          className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y font-sans leading-relaxed"
                        />
                      </div>

                      {/* Image upload */}
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                          Attach Image <span className="font-normal text-gray-400">(optional)</span>
                        </label>
                        {imagePreview ? (
                          <div className="relative inline-block">
                            <img src={imagePreview} alt="Preview" className="h-32 rounded-lg object-cover border border-gray-200 dark:border-gray-600" />
                            <button onClick={removeImage} className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600">✕</button>
                          </div>
                        ) : (
                          <button onClick={() => fileRef.current?.click()}
                            className="flex items-center gap-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-sm text-gray-500 dark:text-gray-400 hover:border-blue-400 hover:text-blue-500 transition-colors">
                            📷 Click to attach image (JPG, PNG, GIF)
                          </button>
                        )}
                        <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/gif" onChange={handleImageChange} className="hidden" />
                      </div>

                      {/* LinkedIn preview card */}
                      <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                        <div className="bg-gray-50 dark:bg-gray-900/50 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                          <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">LinkedIn Preview</span>
                        </div>
                        <div className="p-4 bg-white dark:bg-gray-800">
                          <div className="flex items-center gap-2 mb-3">
                            <div className="w-9 h-9 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0">AI</div>
                            <div>
                              <div className="text-sm font-semibold text-gray-900 dark:text-white leading-tight">Your Name</div>
                              <div className="text-xs text-gray-500 dark:text-gray-400">Just now • 🌐</div>
                            </div>
                          </div>
                          {imagePreview && <img src={imagePreview} alt="" className="w-full rounded-lg mb-3 max-h-40 object-cover" />}
                          <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">{postText}</p>
                        </div>
                      </div>
                    </>
                  )}

                  {error && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3 text-sm text-red-700 dark:text-red-400">⚠️ {error}</div>
                  )}

                  <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-gray-700">
                    <button onClick={handleClose} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors font-medium">Cancel</button>
                    {liStep === "preview" && (
                      <button onClick={handleLinkedInPost} disabled={liPosting || !liCharOk}
                        className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-2">
                        {liPosting
                          ? <><span className="animate-spin inline-block">⟳</span> Posting...</>
                          : <>🚀 Post to LinkedIn{imageFile ? " + Image" : ""}</>}
                      </button>
                    )}
                  </div>
                </>
              )}
            </>
          )}

          {/* ══════════════════════════════════════════════════════════════
              EMAIL / WHATSAPP / INVOICE — AI generation flow
          ══════════════════════════════════════════════════════════════ */}
          {taskType !== "linkedin" && (
            <form onSubmit={handleSubmit} className="space-y-5">

              {/* ── STEP 1: AI Prompt ───────────────────────────────────── */}
              <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">✨</span>
                  <label className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
                    {AI_LABELS[taskType]}
                  </label>
                  <span className="text-xs bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded-full font-medium">Claude AI</span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); if (!generating) handleAiGenerate(); } }}
                    placeholder={PLACEHOLDERS[taskType]}
                    className="flex-1 border border-indigo-300 dark:border-indigo-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={handleAiGenerate}
                    disabled={generating || !aiPrompt.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap"
                  >
                    {generating
                      ? <><span className="animate-spin inline-block">⟳</span> Generating...</>
                      : <>✨ {aiStep === "preview" ? "Regenerate" : "Generate"}</>}
                  </button>
                </div>
                {aiStep === "preview" && (
                  <p className="text-xs text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                    <span>✅</span> AI generated — edit freely below before submitting
                  </p>
                )}
              </div>

              {/* ── STEP 2: Preview / Edit fields ───────────────────────── */}
              {/* INVOICE fields */}
              {taskType === "odoo" && (
                <>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Customer Name</label>
                    <input type="text" value={customer} onChange={(e) => setCustomer(e.target.value)} required placeholder="Acme Corp" className={INPUT_CLS} />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                      Customer Email <span className="font-normal text-gray-400">(optional — Odoo will send PDF)</span>
                    </label>
                    <input type="email" value={customerEmail} onChange={(e) => setCustomerEmail(e.target.value)} placeholder="client@example.com" className={INPUT_CLS} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Amount</label>
                      <input type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required placeholder="500.00" className={INPUT_CLS} />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Currency</label>
                      <select value={currency} onChange={(e) => setCurrency(e.target.value)} className={INPUT_CLS}>
                        {["USD", "EUR", "GBP", "PKR", "AED", "SAR"].map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Description / Service</label>
                    <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} required placeholder="Consulting services – Q1 2026" className={INPUT_CLS} />
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1.5">Draft queued in Pending Approvals → approve to create in Odoo.</p>
                  </div>
                </>
              )}

              {/* EMAIL fields */}
              {taskType === "email" && (
                <>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">To (Email address)</label>
                    <input type="email" value={recipient} onChange={(e) => setRecipient(e.target.value)} required placeholder="client@example.com" className={INPUT_CLS} />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Subject</label>
                    <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)} required placeholder="Project Update – Q1 Review" className={INPUT_CLS} />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300">Email Body</label>
                      <span className={`text-xs font-mono ${content.length > 2900 ? "text-red-600" : "text-gray-400"}`}>
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
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1.5">
                      Draft goes to Pending Approvals for review before sending.
                    </p>
                  </div>
                </>
              )}

              {/* WHATSAPP fields */}
              {taskType === "whatsapp" && (
                <>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">To (Contact name or phone)</label>
                    <input type="text" value={waRecipient} onChange={(e) => setWaRecipient(e.target.value)} required placeholder="Ali Hassan or 923001234567" className={INPUT_CLS} />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300">Message</label>
                      <span className={`text-xs font-mono ${waMessage.length > 2900 ? "text-red-600" : "text-gray-400"}`}>
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
                    <p className="text-xs text-green-600 dark:text-green-400 mt-1.5 flex items-center gap-1">
                      <span>⚡</span> WhatsApp messages are sent directly — no approval needed.
                    </p>
                  </div>
                </>
              )}

              {/* Error */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
                  <p className="text-red-600 dark:text-red-400 text-sm font-medium">{error}</p>
                </div>
              )}

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-200 dark:border-gray-700">
                <button type="button" onClick={handleClose}
                  className="px-5 py-2.5 text-sm font-semibold text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={
                    loading ||
                    (taskType === "odoo"     ? !customer || !amount || !description :
                     taskType === "email"    ? !recipient || !subject || !content :
                     taskType === "whatsapp" ? !waRecipient || !waMessage : false)
                  }
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? (
                    <><div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" /> Creating...</>
                  ) : taskType === "whatsapp" ? "⚡ Send Now" :
                    taskType === "odoo"     ? "🧾 Create Invoice Draft" :
                                             "📧 Create Email Draft"}
                </button>
              </div>
            </form>
          )}

        </div>
      </div>
    </div>
  );
}
