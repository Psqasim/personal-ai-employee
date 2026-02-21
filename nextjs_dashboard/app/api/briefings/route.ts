import { NextResponse } from "next/server";
import { auth } from "@/auth";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

const VAULT_PATH = path.join(process.cwd(), "..", "vault");

interface BriefingMeta {
  filename: string;
  date: string;
  weekStart?: string;
  weekEnd?: string;
  totalCompleted?: number;
  apiCost?: number;
  pendingApprovals?: number;
  generatedAt?: string;
}

function parseBriefingFrontmatter(content: string): Record<string, string> {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const fm: Record<string, string> = {};
  for (const line of match[1].split("\n")) {
    const m = line.match(/^(\w+):\s*(.+)$/);
    if (m) fm[m[1].trim()] = m[2].trim();
  }
  return fm;
}

export async function GET() {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // CEO Briefings are admin-only — contain cost data and business insights
  const userRole = (session.user as any)?.role;
  if (userRole !== "admin") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const briefingsDir = path.join(VAULT_PATH, "Briefings");

  if (!fs.existsSync(briefingsDir)) {
    return NextResponse.json({ briefings: [], latest: null });
  }

  try {
    const files = fs
      .readdirSync(briefingsDir)
      .filter((f) => f.endsWith(".md"))
      .sort()
      .reverse(); // newest first

    const briefings: BriefingMeta[] = files.map((filename) => {
      const filePath = path.join(briefingsDir, filename);
      const content = fs.readFileSync(filePath, "utf-8");
      const fm = parseBriefingFrontmatter(content);
      const stat = fs.statSync(filePath);
      return {
        filename,
        date: fm.briefing_date || filename.replace("_Monday_Briefing.md", ""),
        weekStart: fm.week_start,
        weekEnd: fm.week_end,
        totalCompleted: fm.total_completed ? parseInt(fm.total_completed) : undefined,
        apiCost: fm.api_cost_week ? parseFloat(fm.api_cost_week) : undefined,
        pendingApprovals: fm.pending_approvals ? parseInt(fm.pending_approvals) : undefined,
        generatedAt: fm.generated_at || new Date(stat.mtimeMs).toISOString(),
      };
    });

    // Return latest briefing content too
    let latestContent: string | null = null;
    if (files.length > 0) {
      const latestPath = path.join(briefingsDir, files[0]);
      const raw = fs.readFileSync(latestPath, "utf-8");
      // Strip frontmatter, return body only
      latestContent = raw.replace(/^---[\s\S]*?---\r?\n/, "").trim();
    }

    return NextResponse.json({ briefings, latest: latestContent });
  } catch (error) {
    console.error("Error reading briefings:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
