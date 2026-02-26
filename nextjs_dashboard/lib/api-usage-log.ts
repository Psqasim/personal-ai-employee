import fs from "fs";
import path from "path";
import matter from "gray-matter";

const VAULT_USAGE_DIR = path.join(process.cwd(), "..", "vault", "Logs", "API_Usage");

/**
 * Log Claude API usage to vault/Logs/API_Usage/{date}.md
 * Called after each Claude API call to track tokens and cost.
 */
export function logApiUsage(usage: { input_tokens: number; output_tokens: number }, model: string) {
  try {
    if (!fs.existsSync(VAULT_USAGE_DIR)) fs.mkdirSync(VAULT_USAGE_DIR, { recursive: true });

    const today = new Date().toISOString().slice(0, 10);
    const filePath = path.join(VAULT_USAGE_DIR, `${today}.md`);
    const inputTokens = usage.input_tokens ?? 0;
    const outputTokens = usage.output_tokens ?? 0;
    // Rough cost: Sonnet input $3/MTok, output $15/MTok
    const callCost = (inputTokens * 3 + outputTokens * 15) / 1_000_000;

    if (fs.existsSync(filePath)) {
      const raw = fs.readFileSync(filePath, "utf-8");
      const { data, content } = matter(raw);
      data.input_tokens = (Number(data.input_tokens) || 0) + inputTokens;
      data.output_tokens = (Number(data.output_tokens) || 0) + outputTokens;
      data.calls = (Number(data.calls) || 0) + 1;
      data.cost = Number(((Number(data.cost) || 0) + callCost).toFixed(6));
      data.last_updated = new Date().toISOString();
      fs.writeFileSync(filePath, matter.stringify(content, data));
    } else {
      const data = {
        date: today,
        input_tokens: inputTokens,
        output_tokens: outputTokens,
        calls: 1,
        cost: Number(callCost.toFixed(6)),
        model,
        last_updated: new Date().toISOString(),
      };
      fs.writeFileSync(filePath, matter.stringify(`\n# API Usage for ${today}\n\nAuto-tracked by dashboard Quick Create.\n`, data));
    }
  } catch (err) {
    console.error("[API-USAGE-LOG] Failed to log usage:", err);
  }
}
