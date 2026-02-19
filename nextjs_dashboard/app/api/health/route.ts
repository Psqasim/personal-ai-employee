import { NextResponse } from "next/server";
import { auth } from "@/auth";
import fs from "fs";
import https from "https";
import axios from "axios";

// Force IPv4 — same fix as LinkedIn route
const ipv4Agent = new https.Agent({ family: 4 });

interface MCPServerHealth {
  name: string;
  status: "online" | "offline" | "unknown";
  lastCall: string | null;
  description: string;
}

async function checkLinkedIn(): Promise<MCPServerHealth> {
  const token = process.env.LINKEDIN_ACCESS_TOKEN;
  if (!token) return { name: "LinkedIn", status: "offline", lastCall: null, description: "Token not configured" };
  try {
    const res = await axios.get("https://api.linkedin.com/v2/userinfo", {
      headers: { Authorization: `Bearer ${token}`, "LinkedIn-Version": "202601" },
      httpsAgent: ipv4Agent,
      timeout: 6000,
      validateStatus: () => true,
    });
    return {
      name: "LinkedIn",
      status: res.status === 200 ? "online" : "offline",
      lastCall: new Date().toISOString(),
      description: res.status === 200 ? "Token valid · API reachable" : `HTTP ${res.status}`,
    };
  } catch {
    return { name: "LinkedIn", status: "offline", lastCall: null, description: "Connection failed" };
  }
}

async function checkOdoo(): Promise<MCPServerHealth> {
  const url = process.env.ODOO_URL;
  const user = process.env.ODOO_USER;
  if (!url) return { name: "Odoo", status: "offline", lastCall: null, description: "URL not configured" };
  try {
    const res = await axios.get(url, {
      httpsAgent: ipv4Agent,
      timeout: 6000,
      validateStatus: () => true,
    });
    return {
      name: "Odoo",
      status: res.status < 500 ? "online" : "offline",
      lastCall: new Date().toISOString(),
      description: res.status < 500 ? `Reachable · ${user || "configured"}` : `HTTP ${res.status}`,
    };
  } catch {
    return { name: "Odoo", status: "offline", lastCall: null, description: "Connection failed" };
  }
}

function checkEmail(): MCPServerHealth {
  const host = process.env.SMTP_HOST;
  const user = process.env.SMTP_USER;
  return {
    name: "Email",
    status: host && user ? "online" : "offline",
    lastCall: null,
    description: host && user ? `SMTP configured · ${user}` : "SMTP not configured",
  };
}

function checkGmail(): MCPServerHealth {
  const credPath = process.env.GMAIL_CREDENTIALS_PATH;
  const exists = credPath ? fs.existsSync(credPath) : false;
  return {
    name: "Gmail",
    status: exists ? "online" : "offline",
    lastCall: null,
    description: exists ? "Credentials found · Watcher active" : "Credentials not found",
  };
}

function checkWhatsApp(): MCPServerHealth {
  const sessionPath = process.env.WHATSAPP_SESSION_PATH || "/home/ps_qasim/.whatsapp_session_dir";
  try {
    const indexedDbPath = `${sessionPath}/Default/IndexedDB`;
    if (!fs.existsSync(indexedDbPath)) {
      return { name: "WhatsApp", status: "offline", lastCall: null, description: "Session not found — run wa_local_setup.py" };
    }
    const files = fs.readdirSync(indexedDbPath);
    return {
      name: "WhatsApp",
      status: files.length > 0 ? "online" : "offline",
      lastCall: null,
      description: files.length > 0 ? "Session active · Watcher running" : "Session empty — re-authenticate",
    };
  } catch {
    return { name: "WhatsApp", status: "unknown", lastCall: null, description: "Cannot read session directory" };
  }
}

function checkTwitter(): MCPServerHealth {
  const token = process.env.TWITTER_ACCESS_TOKEN;
  return {
    name: "Twitter",
    status: token ? "online" : "offline",
    lastCall: null,
    description: token ? "API credentials configured" : "Not configured",
  };
}

function checkFacebook(): MCPServerHealth {
  return { name: "Facebook", status: "offline", lastCall: null, description: "Not configured for this project" };
}

function checkInstagram(): MCPServerHealth {
  return { name: "Instagram", status: "offline", lastCall: null, description: "Not configured for this project" };
}

export async function GET() {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    // Run async checks in parallel
    const [linkedin, odoo] = await Promise.all([checkLinkedIn(), checkOdoo()]);

    const servers: MCPServerHealth[] = [
      checkEmail(),
      checkGmail(),
      checkWhatsApp(),
      linkedin,
      checkTwitter(),
      odoo,
      checkFacebook(),
      checkInstagram(),
    ];

    return NextResponse.json({ servers, timestamp: new Date().toISOString() });
  } catch (error) {
    console.error("Health check error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
