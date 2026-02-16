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

    // Only admin can create tasks
    if (userRole !== "admin") {
      return NextResponse.json({ error: "Forbidden - admin only" }, { status: 403 });
    }

    const body = await req.json();
    const { type, to, subject, content } = body;

    // Validate inputs
    if (!type || !to || !content) {
      return NextResponse.json(
        { error: "Missing required fields: type, to, content" },
        { status: 400 }
      );
    }

    if (!["email", "linkedin", "whatsapp"].includes(type)) {
      return NextResponse.json(
        { error: "Invalid type. Must be email, linkedin, or whatsapp" },
        { status: 400 }
      );
    }

    if (type === "email" && !subject) {
      return NextResponse.json(
        { error: "Subject required for email tasks" },
        { status: 400 }
      );
    }

    // Determine folder based on type
    const folderMap: Record<string, string> = {
      email: "Email",
      linkedin: "LinkedIn",
      whatsapp: "WhatsApp",
    };

    const folder = folderMap[type];
    const timestamp = Date.now();
    const userName = (session.user.name || "User").replace(/\s+/g, "_");
    const fileName = `MANUAL_${type.toUpperCase()}_${userName}_${timestamp}.md`;

    // Create file path
    const vaultPath = path.join(process.cwd(), "..", "vault");
    const categoryPath = path.join(vaultPath, "Pending_Approval", folder);
    const filePath = path.join(categoryPath, fileName);

    // Ensure directory exists
    if (!fs.existsSync(categoryPath)) {
      fs.mkdirSync(categoryPath, { recursive: true });
    }

    // Build frontmatter
    const frontmatter: Record<string, any> = {
      type,
      to,
      created_by: session.user.name,
      created_at: new Date().toISOString(),
      status: "pending_approval",
      source: "manual_dashboard",
    };

    if (type === "email" && subject) {
      frontmatter.subject = subject;
    }

    // Build file content
    const frontmatterStr = Object.entries(frontmatter)
      .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
      .join("\n");

    const fileContent = `---
${frontmatterStr}
---

${content}
`;

    // Write file
    fs.writeFileSync(filePath, fileContent, "utf-8");

    return NextResponse.json({
      success: true,
      message: "Task created successfully",
      filePath: path.relative(vaultPath, filePath),
    });
  } catch (error) {
    console.error("Error creating task:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
