"use client";

import { useState, useRef } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

type Step = "input" | "preview" | "done";

export function LinkedInPostModal({ isOpen, onClose }: Props) {
  const [step, setStep] = useState<Step>("input");
  const [topic, setTopic]     = useState("");
  const [postText, setPostText] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const [generating, setGenerating] = useState(false);
  const [posting, setPosting]       = useState(false);
  const [error, setError]           = useState("");
  const [result, setResult]         = useState<{ postUrl: string; hasImage: boolean } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const charCount = postText.length;
  const charOk    = charCount > 0 && charCount <= 3000;

  function handleImageChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  }

  function removeImage() {
    setImageFile(null);
    setImagePreview("");
    if (fileRef.current) fileRef.current.value = "";
  }

  async function handleGenerate() {
    if (!topic.trim()) { setError("Enter a topic first"); return; }
    setError("");
    setGenerating(true);
    try {
      const res = await fetch("/api/linkedin/post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "generate", topic }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Generation failed");
      setPostText(data.postText);
      setStep("preview");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  async function handlePost() {
    if (!charOk) return;
    setError("");
    setPosting(true);
    try {
      let imageBase64: string | undefined;
      let imageMime: string | undefined;

      if (imageFile) {
        imageMime = imageFile.type;
        imageBase64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const result = e.target?.result as string;
            resolve(result.split(",")[1]); // strip "data:image/...;base64,"
          };
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
      setResult({ postUrl: data.postUrl, hasImage: data.hasImage });
      setStep("done");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setPosting(false);
    }
  }

  function handleClose() {
    setStep("input");
    setTopic("");
    setPostText("");
    setImageFile(null);
    setImagePreview("");
    setError("");
    setResult(null);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔗</span>
            <h2 className="font-bold text-gray-900 dark:text-white">Post to LinkedIn</h2>
            <span className="text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full">
              AI Generated
            </span>
          </div>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl leading-none">✕</button>
        </div>

        <div className="px-6 py-5 space-y-5">

          {/* ── STEP: Done ────────────────────────────────────────────── */}
          {step === "done" && result && (
            <div className="text-center py-8 space-y-4">
              <div className="text-5xl">🎉</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Posted Successfully!</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Your post is live on LinkedIn{result.hasImage ? " with image" : ""}.
              </p>
              <a
                href={result.postUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm transition-colors"
              >
                View Post on LinkedIn ↗
              </a>
              <div>
                <button
                  onClick={() => { setStep("input"); setTopic(""); setPostText(""); setImageFile(null); setImagePreview(""); setResult(null); }}
                  className="text-sm text-gray-500 dark:text-gray-400 hover:underline"
                >
                  Post another
                </button>
              </div>
            </div>
          )}

          {/* ── STEP: Input / Preview ─────────────────────────────────── */}
          {(step === "input" || step === "preview") && (
            <>
              {/* Topic input */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                  What should the post be about?
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                    placeholder="e.g. AI trends in 2026, how I built this app, productivity tips..."
                    className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleGenerate}
                    disabled={generating || !topic.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition-colors whitespace-nowrap flex items-center gap-1.5"
                  >
                    {generating ? (
                      <><span className="animate-spin">⟳</span> Generating...</>
                    ) : (
                      <>✨ {step === "preview" ? "Regenerate" : "Generate"}</>
                    )}
                  </button>
                </div>
              </div>

              {/* Post text editor (shown after generate) */}
              {step === "preview" && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Post Content <span className="font-normal text-gray-400">(edit freely)</span>
                    </label>
                    <span className={`text-xs font-mono ${charCount > 3000 ? "text-red-500" : charCount > 2500 ? "text-yellow-500" : "text-gray-400"}`}>
                      {charCount} / 3000
                    </span>
                  </div>
                  <textarea
                    value={postText}
                    onChange={(e) => setPostText(e.target.value)}
                    rows={10}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y font-sans leading-relaxed"
                  />

                  {/* Image upload */}
                  <div className="mt-3">
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                      Attach Image <span className="font-normal text-gray-400">(optional)</span>
                    </label>

                    {imagePreview ? (
                      <div className="relative inline-block">
                        <img
                          src={imagePreview}
                          alt="Preview"
                          className="h-36 rounded-lg object-cover border border-gray-200 dark:border-gray-600"
                        />
                        <button
                          onClick={removeImage}
                          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600 transition-colors"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => fileRef.current?.click()}
                        className="flex items-center gap-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-sm text-gray-500 dark:text-gray-400 hover:border-blue-400 hover:text-blue-500 transition-colors"
                      >
                        📷 Click to attach image (JPG, PNG, GIF)
                      </button>
                    )}
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/jpeg,image/png,image/gif"
                      onChange={handleImageChange}
                      className="hidden"
                    />
                  </div>

                  {/* Preview card */}
                  <div className="mt-4 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                    <div className="bg-gray-50 dark:bg-gray-900/50 px-4 py-2 flex items-center gap-1.5 border-b border-gray-200 dark:border-gray-700">
                      <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">LinkedIn Preview</span>
                    </div>
                    <div className="p-4 bg-white dark:bg-gray-800">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-9 h-9 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                          AI
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-gray-900 dark:text-white leading-tight">Your Name</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">Just now • 🌐</div>
                        </div>
                      </div>
                      {imagePreview && (
                        <img src={imagePreview} alt="" className="w-full rounded-lg mb-3 max-h-48 object-cover" />
                      )}
                      <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
                        {postText}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3 text-sm text-red-700 dark:text-red-400">
                  ⚠️ {error}
                </div>
              )}

              {/* Footer buttons */}
              <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Cancel
                </button>
                {step === "preview" && (
                  <button
                    onClick={handlePost}
                    disabled={posting || !charOk}
                    className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-2"
                  >
                    {posting ? (
                      <><span className="animate-spin">⟳</span> Posting...</>
                    ) : (
                      <>🚀 Post to LinkedIn{imageFile ? " + Image" : ""}</>
                    )}
                  </button>
                )}
              </div>
            </>
          )}

        </div>
      </div>
    </div>
  );
}
