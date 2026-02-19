import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import Anthropic from "@anthropic-ai/sdk";
import axios from "axios";
import https from "https";

// Force IPv4 — WSL2 Node.js gets AggregateError when IPv6 + IPv4 both attempted
const ipv4Agent = new https.Agent({ family: 4 });

const anthropic = new Anthropic({ apiKey: process.env.CLAUDE_API_KEY });

const LI_TOKEN = process.env.LINKEDIN_ACCESS_TOKEN!;
const LI_URN   = process.env.LINKEDIN_AUTHOR_URN!;
const LI_VER   = "202601";

function liHeaders(extra: Record<string, string> = {}) {
  return {
    Authorization: `Bearer ${LI_TOKEN}`,
    "LinkedIn-Version": LI_VER,
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json",
    ...extra,
  };
}

// ── Generate post text with Claude ──────────────────────────────────────────
async function generatePostText(topic: string): Promise<string> {
  const msg = await anthropic.messages.create({
    model: process.env.CLAUDE_MODEL || "claude-sonnet-4-6",
    max_tokens: 600,
    messages: [
      {
        role: "user",
        content: `Write a compelling LinkedIn post about: "${topic}"

Requirements:
- Professional and engaging tone
- 150-250 words (ideal LinkedIn length)
- Start with a strong hook (no "I" as the first word)
- Include 2-3 relevant insights or points
- End with a thought-provoking question or call to action
- Add 3-5 relevant hashtags at the end
- Max 3000 characters total
- Sound like a real professional, not AI-generated

Return ONLY the post text, no extra commentary.`,
      },
    ],
  });

  let text = msg.content[0].type === "text" ? msg.content[0].text : "";
  // Strip any preamble Claude sometimes adds before the actual post
  text = text.replace(/^(here'?s?\s+(your\s+)?linkedin\s+post[:\s\-—]*\n*)/i, "").trim();
  text = text.replace(/^---\n*/m, "").trim();
  return text.slice(0, 3000);
}

// ── Upload image to LinkedIn (2-step, using axios) ───────────────────────────
async function uploadImage(imageBase64: string, mimeType: string): Promise<string> {
  // Step 1: Initialize upload
  const initRes = await axios.post(
    "https://api.linkedin.com/rest/images?action=initializeUpload",
    { initializeUploadRequest: { owner: LI_URN } },
    { headers: liHeaders(), httpsAgent: ipv4Agent }
  );

  const uploadUrl: string = initRes.data.value.uploadUrl;
  const imageUrn: string  = initRes.data.value.image;

  // Step 2: Upload bytes
  const imageBytes = Buffer.from(imageBase64, "base64");
  await axios.put(uploadUrl, imageBytes, {
    headers: {
      Authorization: `Bearer ${LI_TOKEN}`,
      "Content-Type": mimeType,
      "LinkedIn-Version": LI_VER,
    },
    httpsAgent: ipv4Agent,
    maxBodyLength: Infinity,
    maxContentLength: Infinity,
  });

  return imageUrn;
}

// ── POST /api/linkedin/post ──────────────────────────────────────────────────
export async function POST(request: NextRequest) {
  const session = await auth();
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  if ((session.user as any).role !== "admin")
    return NextResponse.json({ error: "Admin only" }, { status: 403 });

  if (!LI_TOKEN || !LI_URN)
    return NextResponse.json({ error: "LinkedIn not configured (missing token or URN)" }, { status: 500 });

  try {
    const body = await request.json();
    const { action, topic, postText, imageBase64, imageMime } = body;
    console.log("[LI] action:", action, "| postText len:", postText?.length, "| hasImage:", !!imageBase64);

    // ── Action: generate text only ──────────────────────────────────────────
    if (action === "generate") {
      if (!topic?.trim()) return NextResponse.json({ error: "Topic is required" }, { status: 400 });
      const text = await generatePostText(topic.trim());
      return NextResponse.json({ success: true, postText: text, charCount: text.length });
    }

    // ── Action: post to LinkedIn ─────────────────────────────────────────────
    if (action === "post") {
      if (!postText?.trim()) return NextResponse.json({ error: "Post text is required" }, { status: 400 });
      if (postText.length > 3000) return NextResponse.json({ error: "Post exceeds 3000 chars" }, { status: 400 });

      console.log("[LI] token set:", !!LI_TOKEN, "| urn:", LI_URN);

      const payload: Record<string, unknown> = {
        author: LI_URN,
        commentary: postText,
        visibility: "PUBLIC",
        distribution: {
          feedDistribution: "MAIN_FEED",
          targetEntities: [],
          thirdPartyDistributionChannels: [],
        },
        lifecycleState: "PUBLISHED",
        isReshareDisabledByAuthor: false,
      };

      // Attach image if provided
      if (imageBase64 && imageMime) {
        console.log("[LI] uploading image, mime:", imageMime, "base64 len:", imageBase64.length);
        try {
          const imageUrn = await uploadImage(imageBase64, imageMime);
          console.log("[LI] image uploaded:", imageUrn);
          payload.content = { media: { id: imageUrn, title: "Post image" } };
        } catch (imgErr: any) {
          console.warn("[LI] Image upload failed, posting without image:", imgErr.message, imgErr.response?.data);
        }
      }

      console.log("[LI] posting to LinkedIn...");
      const res = await axios.post(
        "https://api.linkedin.com/rest/posts",
        payload,
        { headers: liHeaders(), httpsAgent: ipv4Agent, validateStatus: () => true }
      );

      console.log("[LI] response status:", res.status, "| headers:", JSON.stringify(res.headers));
      if (res.status >= 400) console.error("[LI] error body:", JSON.stringify(res.data));

      if (res.status === 401) return NextResponse.json({ error: "LinkedIn token expired" }, { status: 401 });
      if (res.status === 429) return NextResponse.json({ error: "LinkedIn rate limit — try again in 60 min" }, { status: 429 });
      if (res.status >= 400) {
        return NextResponse.json(
          { error: `LinkedIn error ${res.status}: ${JSON.stringify(res.data)}` },
          { status: 500 }
        );
      }

      const postId = res.headers["x-restli-id"] || "";
      const postUrl = postId
        ? `https://www.linkedin.com/feed/update/${postId}`
        : "https://www.linkedin.com/feed/";

      console.log("[LI] success! postId:", postId);
      return NextResponse.json({ success: true, postId, postUrl, hasImage: !!payload.content });
    }

    return NextResponse.json({ error: "Invalid action" }, { status: 400 });
  } catch (err: any) {
    const detail = {
      message: err?.message ?? "(none)",
      cause: err?.cause?.message ?? err?.cause?.code ?? "(none)",
      axiosData: err?.response?.data ?? "(none)",
      type: err?.constructor?.name ?? "(none)",
      str: String(err),
    };
    console.error("[LI] CAUGHT ERROR:", JSON.stringify(detail));
    return NextResponse.json({ error: JSON.stringify(detail) }, { status: 500 });
  }
}
