import { NextResponse } from "next/server";
import { auth } from "@/auth";
import fs from "fs";
import path from "path";

interface MCPServerHealth {
  name: string;
  status: "online" | "offline" | "unknown";
  lastCall: string | null;
  error?: string;
}

export async function GET() {
  const session = await auth();

  // Check authentication (both admin and viewer can access)
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const vaultPath = path.join(process.cwd(), "..", "vault");
    const mcpHealthPath = path.join(vaultPath, "Logs", "MCP_Health");

    const mcpServers: MCPServerHealth[] = [];

    // Define expected MCP servers
    const expectedServers = [
      "Email",
      "WhatsApp",
      "LinkedIn",
      "Facebook",
      "Instagram",
      "Twitter",
      "Odoo",
    ];

    for (const serverName of expectedServers) {
      const healthFile = path.join(mcpHealthPath, `${serverName.toLowerCase()}.md`);

      if (fs.existsSync(healthFile)) {
        try {
          const content = fs.readFileSync(healthFile, "utf-8");
          const lines = content.split("\n");
          const statusLine = lines.find((l) => l.includes("status:"));
          const lastCallLine = lines.find((l) => l.includes("last_call:"));

          mcpServers.push({
            name: serverName,
            status: statusLine?.includes("online") ? "online" : "offline",
            lastCall: lastCallLine?.split(":")[1]?.trim() || null,
          });
        } catch (error) {
          mcpServers.push({
            name: serverName,
            status: "unknown",
            lastCall: null,
            error: "Failed to read health file",
          });
        }
      } else {
        mcpServers.push({
          name: serverName,
          status: "unknown",
          lastCall: null,
        });
      }
    }

    return NextResponse.json({
      servers: mcpServers,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Error in health API:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
