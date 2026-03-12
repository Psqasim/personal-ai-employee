import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { approveItem } from "@/lib/vault";
import path from "path";
import fs from "fs";
import matter from "gray-matter";
import nodemailer from "nodemailer";

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), "..", "vault");

async function createOdooInvoice(filePath: string): Promise<{ created: boolean; invoiceId?: number; error?: string }> {
  try {
    const fullPath = path.join(VAULT_PATH, filePath.replace("Pending_Approval", "Approved"));
    const raw = fs.readFileSync(fullPath, "utf-8");
    const { data } = matter(raw);

    const isOdoo = data.type === "odoo_invoice" || data.action === "create_draft_invoice";
    if (!isOdoo) return { created: false };

    const odooUrl = process.env.ODOO_URL;
    const odooDb = process.env.ODOO_DB;
    const odooUser = process.env.ODOO_USER;
    const odooPass = process.env.ODOO_API_KEY || process.env.ODOO_PASSWORD;

    if (!odooUrl || !odooDb || !odooUser || !odooPass) {
      console.error("Odoo approve: missing ODOO_URL/ODOO_DB/ODOO_USER/ODOO_API_KEY");
      return { created: false, error: "Odoo credentials not configured" };
    }

    // Authenticate via JSON-RPC
    const authRes = await fetch(`${odooUrl}/jsonrpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0", method: "call", id: 1,
        params: { service: "common", method: "login", args: [odooDb, odooUser, odooPass] }
      }),
    });
    const authData = await authRes.json();
    const uid = authData.result;
    if (!uid) return { created: false, error: "Odoo authentication failed" };

    // Find or create partner
    const customer = data.customer || "Unknown";
    const searchRes = await fetch(`${odooUrl}/jsonrpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0", method: "call", id: 2,
        params: {
          service: "object", method: "execute_kw",
          args: [odooDb, uid, odooPass, "res.partner", "search", [[["name", "ilike", customer]]], { limit: 1 }]
        }
      }),
    });
    const searchData = await searchRes.json();
    let partnerId = searchData.result?.[0];

    if (!partnerId) {
      const createPartner = await fetch(`${odooUrl}/jsonrpc`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0", method: "call", id: 3,
          params: {
            service: "object", method: "execute_kw",
            args: [odooDb, uid, odooPass, "res.partner", "create", [{ name: customer }]]
          }
        }),
      });
      const partnerData = await createPartner.json();
      partnerId = partnerData.result;
    }

    // Create draft invoice
    const amount = parseFloat(data.amount) || 0;
    const description = data.description || "Invoice";
    const invoiceDate = new Date().toISOString().split("T")[0];

    const invoiceRes = await fetch(`${odooUrl}/jsonrpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0", method: "call", id: 4,
        params: {
          service: "object", method: "execute_kw",
          args: [odooDb, uid, odooPass, "account.move", "create", [{
            move_type: "out_invoice",
            partner_id: partnerId,
            invoice_date: invoiceDate,
            ref: description,
            invoice_line_ids: [[0, 0, { name: description, quantity: 1, price_unit: amount }]]
          }]]
        }
      }),
    });
    const invoiceData = await invoiceRes.json();
    const invoiceId = invoiceData.result;

    if (!invoiceId) {
      return { created: false, error: invoiceData.error?.data?.message || "Odoo create failed" };
    }

    console.log(`Odoo invoice created: ID ${invoiceId} for ${customer} (${amount})`);

    // Move to Done/
    try {
      const donePath = fullPath.replace("/Approved/", "/Done/");
      const doneDir = path.dirname(donePath);
      if (!fs.existsSync(doneDir)) fs.mkdirSync(doneDir, { recursive: true });
      if (fs.existsSync(fullPath)) fs.renameSync(fullPath, donePath);
    } catch (_) { /* non-fatal */ }

    return { created: true, invoiceId };
  } catch (err: any) {
    console.error("Odoo invoice creation failed:", err.message);
    return { created: false, error: err.message };
  }
}

async function sendEmailDirectly(filePath: string): Promise<{ sent: boolean; error?: string }> {
  try {
    const fullPath = path.join(VAULT_PATH, filePath.replace("Pending_Approval", "Approved"));
    const raw = fs.readFileSync(fullPath, "utf-8");
    const { data, content } = matter(raw);

    // Support both: type=email (manual drafts) AND action=send_email (command_router drafts)
    const isEmail = data.type === "email" || data.action === "send_email";
    if (!isEmail) return { sent: false };

    const smtpPass = process.env.SMTP_PASSWORD || process.env.SMTP_PASS;
    if (!smtpPass) {
      console.error("Email approve: SMTP_PASSWORD not set, skipping send");
      return { sent: false, error: "SMTP_PASSWORD not configured" };
    }

    // draft_body is set by command_router; content is the markdown body for manual drafts
    const emailBody = (data.draft_body as string) || content.trim();

    const transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST || "smtp.gmail.com",
      port: 587,
      secure: false,
      auth: {
        user: process.env.SMTP_USER,
        pass: smtpPass,
      },
    });

    await transporter.sendMail({
      from: `"AI Employee" <${process.env.SMTP_USER}>`,
      to: data.to,
      subject: data.subject || "(no subject)",
      text: emailBody,
    });

    console.log(`Email sent to ${data.to}: ${data.subject}`);

    // Move to Done/ immediately after sending — prevents duplicate send on double-click
    try {
      const donePath = fullPath.replace("/Approved/", "/Done/");
      const doneDir = path.dirname(donePath);
      if (!fs.existsSync(doneDir)) fs.mkdirSync(doneDir, { recursive: true });
      if (fs.existsSync(fullPath)) fs.renameSync(fullPath, donePath);
    } catch (_) { /* non-fatal — email already sent */ }

    return { sent: true };
  } catch (err: any) {
    console.error("Email send failed after approve:", err.message);
    return { sent: false, error: err.message };
  }
}

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
    const { filePath } = await request.json();

    if (!filePath) {
      return NextResponse.json({ error: "Missing filePath" }, { status: 400 });
    }

    // Read type BEFORE moving (while still in Pending_Approval)
    let itemType = "";
    try {
      const raw = fs.readFileSync(path.join(VAULT_PATH, filePath), "utf-8");
      const { data } = matter(raw);
      // Support type=email (manual) and action=send_email (command_router)
      if (data.type === "email" || data.action === "send_email") {
        itemType = "email";
      } else if (data.type === "odoo_invoice" || data.action === "create_draft_invoice") {
        itemType = "odoo";
      } else {
        itemType = data.type || "";
      }
    } catch {}

    const success = approveItem(filePath);

    if (!success) {
      return NextResponse.json({ error: "Failed to approve item" }, { status: 500 });
    }

    // After moving to Approved/ — execute the action based on type
    let emailResult: { sent: boolean; error?: string } = { sent: false };
    let odooResult: { created: boolean; invoiceId?: number; error?: string } = { created: false };

    if (itemType === "email") {
      emailResult = await sendEmailDirectly(filePath);
    } else if (itemType === "odoo") {
      odooResult = await createOdooInvoice(filePath);
    }

    return NextResponse.json({
      success: true,
      message: "Item approved successfully",
      ...(itemType === "email" && {
        emailSent: emailResult.sent,
        emailError: emailResult.error,
      }),
      ...(itemType === "odoo" && {
        odooCreated: odooResult.created,
        odooInvoiceId: odooResult.invoiceId,
        odooError: odooResult.error,
      }),
    });
  } catch (error) {
    console.error("Error in approve API:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
