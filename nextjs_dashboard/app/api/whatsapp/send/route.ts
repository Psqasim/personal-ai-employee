import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  const session = await auth();

  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userRole = (session.user as any).role;
  if (userRole !== "admin") {
    return NextResponse.json({ error: "Forbidden - admin only" }, { status: 403 });
  }

  try {
    const { chat_id, message } = await request.json();

    if (!chat_id || !message) {
      return NextResponse.json({ error: "Missing chat_id or message" }, { status: 400 });
    }

    const projectRoot = path.join(process.cwd(), "..");
    const venvPython = path.join(projectRoot, "venv", "bin", "python");
    const script = path.join(projectRoot, "scripts", "whatsapp_send.py");

    // Escape args to avoid shell injection
    const safeChatId = chat_id.replace(/"/g, '\\"');
    const safeMessage = message.replace(/"/g, '\\"');

    const cmd = `"${venvPython}" "${script}" --chat_id "${safeChatId}" --message "${safeMessage}"`;

    const { stdout, stderr } = await execAsync(cmd, {
      timeout: 120000, // 2 min (browser open + send)
      cwd: projectRoot,
    });

    let result: any = {};
    try {
      result = JSON.parse(stdout.trim());
    } catch {
      result = { success: false, error: stderr || stdout || "Unknown error" };
    }

    if (result.success) {
      return NextResponse.json({ success: true, chat_id, message });
    } else {
      return NextResponse.json({ error: result.error || "Send failed" }, { status: 500 });
    }
  } catch (error: any) {
    console.error("WhatsApp send error:", error);
    return NextResponse.json(
      { error: error?.message || "Internal server error" },
      { status: 500 }
    );
  }
}
