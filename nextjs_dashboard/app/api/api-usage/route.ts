import { NextResponse } from "next/server";
import { auth } from "@/auth";
import fs from "fs";
import path from "path";
import matter from "gray-matter";

export interface DayUsage {
  date: string;       // YYYY-MM-DD
  inputTokens: number;
  outputTokens: number;
  calls: number;
  cost: number;
}

function parseUsageFile(filePath: string): Omit<DayUsage, "date"> {
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    const { data } = matter(raw);
    return {
      inputTokens: Number(data.input_tokens ?? data.inputTokens ?? 0),
      outputTokens: Number(data.output_tokens ?? data.outputTokens ?? 0),
      calls: Number(data.calls ?? data.total_calls ?? 0),
      cost: Number(data.cost ?? data.total_cost ?? 0),
    };
  } catch {
    return { inputTokens: 0, outputTokens: 0, calls: 0, cost: 0 };
  }
}

export async function GET() {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const usagePath = path.join(process.cwd(), "..", "vault", "Logs", "API_Usage");
    const days: DayUsage[] = [];

    // Build last 7 days
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().slice(0, 10); // YYYY-MM-DD
      const filePath = path.join(usagePath, `${dateStr}.md`);

      if (fs.existsSync(filePath)) {
        const parsed = parseUsageFile(filePath);
        days.push({ date: dateStr, ...parsed });
      } else {
        days.push({ date: dateStr, inputTokens: 0, outputTokens: 0, calls: 0, cost: 0 });
      }
    }

    const totalCost = days.reduce((sum, d) => sum + d.cost, 0);
    const totalCalls = days.reduce((sum, d) => sum + d.calls, 0);
    const totalInputTokens = days.reduce((sum, d) => sum + d.inputTokens, 0);
    const totalOutputTokens = days.reduce((sum, d) => sum + d.outputTokens, 0);

    return NextResponse.json({
      days,
      totals: { cost: totalCost, calls: totalCalls, inputTokens: totalInputTokens, outputTokens: totalOutputTokens },
    });
  } catch (error) {
    console.error("api-usage error:", error);
    return NextResponse.json({ days: [], totals: { cost: 0, calls: 0, inputTokens: 0, outputTokens: 0 } });
  }
}
