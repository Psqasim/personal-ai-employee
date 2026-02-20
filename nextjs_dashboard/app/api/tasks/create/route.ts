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
    const { type, to, subject, content, customer, customer_email, amount, currency, description } = body;

    // Validate inputs
    if (!type) {
      return NextResponse.json(
        { error: "Missing required field: type" },
        { status: 400 }
      );
    }

    if (!["email", "linkedin", "whatsapp", "odoo"].includes(type)) {
      return NextResponse.json(
        { error: "Invalid type. Must be email, linkedin, whatsapp, or odoo" },
        { status: 400 }
      );
    }

    if (type === "odoo") {
      if (!customer || amount === undefined || !description) {
        return NextResponse.json(
          { error: "Odoo tasks require: customer, amount, description" },
          { status: 400 }
        );
      }
    } else {
      if (!to || !content) {
        return NextResponse.json(
          { error: "Missing required fields: to, content" },
          { status: 400 }
        );
      }
      if (type === "email" && !subject) {
        return NextResponse.json(
          { error: "Subject required for email tasks" },
          { status: 400 }
        );
      }
    }

    const timestamp = Date.now();
    const userName = (session.user.name || "User").replace(/\s+/g, "_");
    const vaultPath = path.join(process.cwd(), "..", "vault");

    // ── Odoo draft ──────────────────────────────────────────────────────────────
    if (type === "odoo") {
      const odooDir = path.join(vaultPath, "Pending_Approval", "Odoo");
      if (!fs.existsSync(odooDir)) fs.mkdirSync(odooDir, { recursive: true });

      const draftId = `MANUAL_${userName}_${timestamp}`;
      const fileName = `INVOICE_DRAFT_${draftId}.md`;
      const filePath = path.join(odooDir, fileName);

      const amountNum = parseFloat(amount) || 0;
      const curr = (currency || "USD").toUpperCase();
      const now = new Date().toISOString();

      const emailLine = customer_email ? `customer_email: ${customer_email}\n` : "";
      const fileContent = `---
type: odoo_invoice
draft_id: ${draftId}
action: create_draft_invoice
status: pending
customer: ${customer}
${emailLine}amount: ${amountNum.toFixed(2)}
currency: ${curr}
description: ${description}
source_email_id: manual
source_email_from: ${session.user.email || "dashboard"}
created: ${now}
mcp_server: odoo-mcp
---

## Odoo Invoice Draft

**Customer:** ${customer}
**Amount:** ${curr} ${amountNum.toFixed(2)}
**Description:** ${description}

---

*Created manually via dashboard by ${session.user.name} on ${now}*
`;

      fs.writeFileSync(filePath, fileContent, "utf-8");

      return NextResponse.json({
        success: true,
        message: "Odoo invoice draft created successfully",
        filePath: path.relative(vaultPath, filePath),
      });
    }

    // ── Email / WhatsApp / LinkedIn ──────────────────────────────────────────────
    const folderMap: Record<string, string> = {
      email: "Email",
      linkedin: "LinkedIn",
      whatsapp: "WhatsApp",
    };

    const folder = folderMap[type];
    const fileName = `MANUAL_${type.toUpperCase()}_${userName}_${timestamp}.md`;

    // Create file path
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
