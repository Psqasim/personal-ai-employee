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

    // Move from Done to Archived
    const targetPath = sourcePath.replace("Done", "Archived");
    const targetDir = path.dirname(targetPath);

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    fs.renameSync(sourcePath, targetPath);

    return NextResponse.json({ message: "File archived successfully" });
  } catch (error) {
    console.error("Error archiving:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
