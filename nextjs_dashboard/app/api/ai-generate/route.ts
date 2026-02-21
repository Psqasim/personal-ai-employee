import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic({ apiKey: process.env.CLAUDE_API_KEY });
const MODEL = process.env.CLAUDE_MODEL || "claude-sonnet-4-6";

// ── Prompt templates ─────────────────────────────────────────────────────────

function emailPrompt(prompt: string): string {
  return `You are a professional email writer. Write a professional business email based on this request:

"${prompt}"

Requirements:
- Subject line: clear and specific (one line, no "Subject:" prefix)
- Body: professional, concise, warm tone
- 100-200 words
- Include greeting and sign-off
- Do NOT include placeholders like [Your Name] — just write a natural sign-off like "Best regards,"

Return ONLY this exact format (two sections separated by exactly "---BODY---"):
<subject line here>
---BODY---
<email body here>`;
}

function whatsappPrompt(prompt: string): string {
  return `You are helping draft a WhatsApp message. Write a conversational WhatsApp message based on this request:

"${prompt}"

Requirements:
- Casual but professional tone (this is WhatsApp, not email)
- Keep it concise — 1-4 short paragraphs or bullet points if needed
- No excessive formality, no "Dear Sir/Madam"
- Can use light formatting (but no markdown headers)
- 30-120 words is ideal
- End naturally, no forced sign-off needed

Return ONLY the message text, nothing else.`;
}

function invoicePrompt(prompt: string): string {
  return `You are helping fill out an invoice. Based on this request, extract the invoice details:

"${prompt}"

Requirements:
- Extract: customer name, amount (number only), currency (USD/EUR/GBP/PKR/AED/SAR), description of services
- If currency not mentioned, default to USD
- Description should be professional, concise (5-15 words)
- If amount is not clear, use 0

Return ONLY this exact JSON (no markdown, no code block):
{"customer":"<name>","amount":<number>,"currency":"<currency>","description":"<service description>"}`;
}

// ── POST /api/ai-generate ─────────────────────────────────────────────────────
export async function POST(request: NextRequest) {
  const session = await auth();
  if (!session?.user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  if ((session.user as any).role !== "admin")
    return NextResponse.json({ error: "Admin only" }, { status: 403 });

  try {
    const { type, prompt } = await request.json();
    if (!prompt?.trim()) return NextResponse.json({ error: "Prompt is required" }, { status: 400 });

    if (type === "email") {
      const msg = await anthropic.messages.create({
        model: MODEL,
        max_tokens: 500,
        messages: [{ role: "user", content: emailPrompt(prompt.trim()) }],
      });
      const raw = msg.content[0].type === "text" ? msg.content[0].text.trim() : "";
      const [subjectLine, ...bodyParts] = raw.split("---BODY---");
      return NextResponse.json({
        subject: subjectLine.trim(),
        body: bodyParts.join("---BODY---").trim(),
      });
    }

    if (type === "whatsapp") {
      const msg = await anthropic.messages.create({
        model: MODEL,
        max_tokens: 300,
        messages: [{ role: "user", content: whatsappPrompt(prompt.trim()) }],
      });
      const text = msg.content[0].type === "text" ? msg.content[0].text.trim() : "";
      return NextResponse.json({ message: text });
    }

    if (type === "invoice") {
      const msg = await anthropic.messages.create({
        model: MODEL,
        max_tokens: 200,
        messages: [{ role: "user", content: invoicePrompt(prompt.trim()) }],
      });
      const raw = msg.content[0].type === "text" ? msg.content[0].text.trim() : "{}";
      // Strip any accidental markdown code blocks
      const cleaned = raw.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
      try {
        const parsed = JSON.parse(cleaned);
        return NextResponse.json(parsed);
      } catch {
        return NextResponse.json({ error: "AI returned invalid format, please try again" }, { status: 500 });
      }
    }

    return NextResponse.json({ error: "Invalid type. Use: email, whatsapp, invoice" }, { status: 400 });
  } catch (err: any) {
    console.error("[AI-GEN] error:", err?.message);
    return NextResponse.json({ error: err?.message || "AI generation failed" }, { status: 500 });
  }
}
