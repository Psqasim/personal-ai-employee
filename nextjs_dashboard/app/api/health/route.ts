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
  // Check env vars that the cloud orchestrator uses for Gmail
  const credPath = process.env.GMAIL_CREDENTIALS_PATH;
  const gmailUser = process.env.GMAIL_ADDRESS || process.env.SMTP_USER;
  const hasCredFile = credPath ? fs.existsSync(credPath) : false;
  // If SMTP is configured with a Gmail address, Gmail watcher is active
  const isConfigured = hasCredFile || !!gmailUser;
  return {
    name: "Gmail",
    status: isConfigured ? "online" : "offline",
    lastCall: null,
    description: isConfigured ? `Watcher active · ${gmailUser || "configured"}` : "Credentials not found",
  };
}

function checkWhatsApp(): MCPServerHealth {
  // Try multiple possible session paths (local WSL2 and cloud VM)
  const candidates = [
    process.env.WHATSAPP_SESSION_PATH,
    "/home/ubuntu/.whatsapp_session_dir",
    "/home/ps_qasim/.whatsapp_session_dir",
  ].filter(Boolean) as string[];

  for (const sessionPath of candidates) {
    try {
      const indexedDbPath = `${sessionPath}/Default/IndexedDB`;
      if (fs.existsSync(indexedDbPath)) {
        const files = fs.readdirSync(indexedDbPath);
        if (files.length > 0) {
          return {
            name: "WhatsApp",
            status: "online",
            lastCall: null,
            description: "Session active · Watcher running",
          };
        }
      }
    } catch {
      // Try next candidate
    }
  }

  return { name: "WhatsApp", status: "offline", lastCall: null, description: "Session not found — run wa_local_setup.py" };
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
