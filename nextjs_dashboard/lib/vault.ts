import fs from "fs";
import path from "path";
import matter from "gray-matter";

/**
 * Safely parse a markdown file with YAML frontmatter.
 * Falls back to extracting body text when YAML is malformed
 * (e.g. retry files with raw browser logs in error: field).
 */
function safeMatter(rawContent: string): { data: Record<string, any>; content: string } {
  try {
    return matter(rawContent);
  } catch {
    // Fallback: strip frontmatter block, treat body as content
    const fmMatch = rawContent.match(/^---[\r\n]([\s\S]*?)[\r\n]---[\r\n]?([\s\S]*)$/);
    if (fmMatch) {
      const body = fmMatch[2] || "";
      // Try to salvage simple key: value lines from frontmatter
      const data: Record<string, any> = {};
      for (const line of fmMatch[1].split("\n")) {
        const m = line.match(/^(\w+):\s*["']?([^"'\n]+)["']?\s*$/);
        if (m) data[m[1]] = m[2].trim();
      }
      return { data, content: body };
    }
    return { data: {}, content: rawContent };
  }
}

export interface ApprovalItem {
  id: string;
  category: "Email" | "LinkedIn" | "Odoo" | "WhatsApp" | "Facebook" | "Instagram" | "Twitter";
  title: string;
  preview: string;
  timestamp: string;
  filePath: string;
  metadata?: Record<string, any>;
  content?: string;
}

const VAULT_PATH = path.join(process.cwd(), "..", "vault");

/**
 * Read all pending approval items from vault/Pending_Approval/
 */
export function getPendingApprovals(): ApprovalItem[] {
  const pendingPath = path.join(VAULT_PATH, "Pending_Approval");
  const items: ApprovalItem[] = [];

  try {
    const categories = fs.readdirSync(pendingPath);

    for (const category of categories) {
      const categoryPath = path.join(pendingPath, category);
      const stat = fs.statSync(categoryPath);

      if (!stat.isDirectory()) continue;

      const files = fs.readdirSync(categoryPath).filter((f) => f.endsWith(".md"));

      for (const file of files) {
        try {
          const filePath = path.join(categoryPath, file);
          const stat = fs.statSync(filePath);
          const content = fs.readFileSync(filePath, "utf-8");
          const { data, content: bodyContent } = safeMatter(content);

          items.push({
            id: path.basename(file, ".md"),
            category: category as any,
            title: data.title || data.subject || file.replace(".md", ""),
            preview: bodyContent.substring(0, 200) + (bodyContent.length > 200 ? "..." : ""),
            timestamp: data.timestamp || data.created_at || stat.mtime.toISOString(),
            filePath: path.relative(VAULT_PATH, filePath),
            metadata: data,
            content: bodyContent,
          });
        } catch (error) {
          console.error(`Error parsing file ${file}:`, error instanceof Error ? error.message : error);
          // Skip files with invalid YAML frontmatter
          continue;
        }
      }
    }

    return items.sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  } catch (error) {
    console.error("Error reading pending approvals:", error);
    return [];
  }
}

/**
 * Move file from Pending_Approval to Approved
 */
export function approveItem(filePath: string): boolean {
  try {
    const sourcePath = path.join(VAULT_PATH, filePath);
    const targetPath = sourcePath.replace("Pending_Approval", "Approved");

    // Ensure target directory exists
    const targetDir = path.dirname(targetPath);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    // Move file
    fs.renameSync(sourcePath, targetPath);
    return true;
  } catch (error) {
    console.error("Error approving item:", error);
    return false;
  }
}

/**
 * Move file from Pending_Approval to Rejected
 */
export function rejectItem(filePath: string, reason?: string): boolean {
  try {
    const sourcePath = path.join(VAULT_PATH, filePath);
    const targetPath = sourcePath.replace("Pending_Approval", "Rejected");

    // Ensure target directory exists
    const targetDir = path.dirname(targetPath);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    // If reason provided, append to frontmatter
    if (reason) {
      try {
        const content = fs.readFileSync(sourcePath, "utf-8");
        const { data, content: bodyContent } = safeMatter(content);
        data.rejection_reason = reason;
        data.rejected_at = new Date().toISOString();
        const newContent = matter.stringify(bodyContent, data);
        fs.writeFileSync(sourcePath, newContent);
      } catch (error) {
        console.error("Error updating frontmatter with rejection reason:", error);
        // Continue with rejection even if frontmatter update fails
      }
    }

    // Move file
    fs.renameSync(sourcePath, targetPath);
    return true;
  } catch (error) {
    console.error("Error rejecting item:", error);
    return false;
  }
}

/**
 * Get vault status summary
 */
export function getVaultStatus() {
  try {
    const getPendingPath = path.join(VAULT_PATH, "Pending_Approval");
    const inProgressPath = path.join(VAULT_PATH, "In_Progress");
    const approvedPath = path.join(VAULT_PATH, "Approved");

    const countFilesInDir = (dir: string): number => {
      if (!fs.existsSync(dir)) return 0;

      let count = 0;
      const items = fs.readdirSync(dir);

      for (const item of items) {
        const itemPath = path.join(dir, item);
        const stat = fs.statSync(itemPath);

        if (stat.isDirectory()) {
          count += countFilesInDir(itemPath);
        } else if (item.endsWith(".md")) {
          count++;
        }
      }

      return count;
    };

    return {
      pending: countFilesInDir(getPendingPath),
      inProgress: countFilesInDir(inProgressPath),
      approved: countFilesInDir(approvedPath),
    };
  } catch (error) {
    console.error("Error getting vault status:", error);
    return {
      pending: 0,
      inProgress: 0,
      approved: 0,
    };
  }
}

/**
 * Get recent activity from vault logs
 */
export function getRecentActivity(limit: number = 10) {
  try {
    const logsPath = path.join(VAULT_PATH, "Logs");
    const activities: Array<{
      timestamp: string;
      agent: string;
      action: string;
      details: string;
    }> = [];

    // Read Cloud and Local agent logs
    const agents = ["Cloud", "Local"];

    for (const agent of agents) {
      const agentPath = path.join(logsPath, agent);
      if (!fs.existsSync(agentPath)) continue;

      // For demo, just return mock data
      // In production, parse actual log files
    }

    return activities.slice(0, limit);
  } catch (error) {
    console.error("Error getting recent activity:", error);
    return [];
  }
}

export interface VaultSection {
  name: string;
  path: string;
  icon: string;
  count: number;
  items: ApprovalItem[];
}

/**
 * Get all vault sections for admin dashboard
 */
export function getAllVaultSections(): VaultSection[] {
  const sections: VaultSection[] = [
    {
      name: "Needs Action",
      path: "Needs_Action",
      icon: "📥",
      count: 0,
      items: [],
    },
    {
      name: "In Progress",
      path: "In_Progress",
      icon: "⏳",
      count: 0,
      items: [],
    },
    {
      name: "Approved",
      path: "Approved",
      icon: "✅",
      count: 0,
      items: [],
    },
    {
      name: "Rejected",
      path: "Rejected",
      icon: "❌",
      count: 0,
      items: [],
    },
    {
      name: "Done",
      path: "Done",
      icon: "🎯",
      count: 0,
      items: [],
    },
    {
      name: "Briefings",
      path: "Briefings",
      icon: "📊",
      count: 0,
      items: [],
    },
    {
      name: "Logs",
      path: "Logs",
      icon: "📝",
      count: 0,
      items: [],
    },
    {
      name: "Inbox",
      path: "Inbox",
      icon: "📂",
      count: 0,
      items: [],
    },
  ];

  for (const section of sections) {
    const sectionPath = path.join(VAULT_PATH, section.path);

    if (!fs.existsSync(sectionPath)) {
      continue;
    }

    try {
      section.items = readItemsFromDirectory(sectionPath, section.path);
      section.count = section.items.length;
    } catch (error) {
      console.error(`Error reading section ${section.name}:`, error);
    }
  }

  return sections;
}

/**
 * Helper: Read items from a directory recursively
 */
function readItemsFromDirectory(dirPath: string, relativePath: string): ApprovalItem[] {
  const items: ApprovalItem[] = [];

  try {
    const entries = fs.readdirSync(dirPath);

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        // Recursively read subdirectories
        items.push(...readItemsFromDirectory(fullPath, path.join(relativePath, entry)));
      } else if (entry.endsWith(".md")) {
        try {
          const content = fs.readFileSync(fullPath, "utf-8");
          const { data, content: bodyContent } = safeMatter(content);

          // Determine category from path
          const pathParts = relativePath.split(path.sep);
          const category = pathParts[pathParts.length - 1] || "General";

          items.push({
            id: path.basename(entry, ".md"),
            category: category as any,
            title: data.title || data.subject || entry.replace(".md", ""),
            preview: bodyContent.substring(0, 200) + (bodyContent.length > 200 ? "..." : ""),
            timestamp: data.timestamp || data.created_at || stat.mtime.toISOString(),
            filePath: path.relative(VAULT_PATH, fullPath),
            metadata: data,
            content: bodyContent,
          });
        } catch (error) {
          console.error(`Error parsing file ${entry}:`, error instanceof Error ? error.message : error);
          // Skip files with invalid YAML
          continue;
        }
      }
    }
  } catch (error) {
    console.error(`Error reading directory ${dirPath}:`, error);
  }

  // Sort by timestamp descending (newest first)
  return items.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}
