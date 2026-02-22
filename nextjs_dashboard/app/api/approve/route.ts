import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { approveItem } from "@/lib/vault";
import path from "path";
import fs from "fs";
import matter from "gray-matter";
import nodemailer from "nodemailer";

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), "..", "vault");

async function sendEmailDirectly(filePath: string): Promise<{ sent: boolean; error?: string }> {
  try {
    const fullPath = path.join(VAULT_PATH, filePath.replace("Pending_Approval", "Approved"));
    const raw = fs.readFileSync(fullPath, "utf-8");
    const { data, content } = matter(raw);

    if (data.type !== "email") return { sent: false };

    const smtpPass = process.env.SMTP_PASSWORD || process.env.SMTP_PASS;
    if (!smtpPass) {
      console.error("Email approve: SMTP_PASSWORD not set, skipping send");
      return { sent: false, error: "SMTP_PASSWORD not configured" };
    }

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
      text: content.trim(),
    });

    console.log(`Email sent to ${data.to}: ${data.subject}`);
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
      itemType = data.type || "";
    } catch {}

    const success = approveItem(filePath);

    if (!success) {
      return NextResponse.json({ error: "Failed to approve item" }, { status: 500 });
    }

    // After moving to Approved/ — send email directly if it's an email task
    let emailResult: { sent: boolean; error?: string } = { sent: false };
    if (itemType === "email") {
      emailResult = await sendEmailDirectly(filePath);
    }

    return NextResponse.json({
      success: true,
      message: "Item approved successfully",
      ...(itemType === "email" && {
        emailSent: emailResult.sent,
        emailError: emailResult.error,
      }),
    });
  } catch (error) {
    console.error("Error in approve API:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
