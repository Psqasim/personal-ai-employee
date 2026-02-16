import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import fs from "fs";
import path from "path";

export async function POST(req: NextRequest) {
  try {
    const session = await auth();

    if (!session || !session.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userRole = (session.user as any).role;

    if (userRole !== "admin") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const body = await req.json();
    const { filePath } = body;

    if (!filePath) {
      return NextResponse.json({ error: "File path required" }, { status: 400 });
    }

    const vaultPath = path.join(process.cwd(), "..", "vault");
    const sourcePath = path.join(vaultPath, filePath);

    // Move from Inbox to Pending_Approval
    const targetPath = sourcePath.replace("Inbox", "Pending_Approval");
    const targetDir = path.dirname(targetPath);

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    fs.renameSync(sourcePath, targetPath);

    return NextResponse.json({ message: "Task created from inbox item" });
  } catch (error) {
    console.error("Error creating task:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
