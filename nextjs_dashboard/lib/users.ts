// NO module-level imports of Node.js APIs to avoid Edge Runtime issues

export interface User {
  id: string;
  email: string;
  password: string;
  role: "admin" | "viewer";
  name: string;
  created_at: string;
}

interface UsersData {
  users: User[];
}

/**
 * Get all users from vault/Users/users.json
 * This runs in Node.js runtime only (API routes, not Edge middleware)
 * Uses dynamic imports to avoid Edge Runtime errors
 */
export async function getUsers(): Promise<User[]> {
  try {
    // Dynamic imports inside function to avoid Edge Runtime
    const fs = await import("fs");
    const path = await import("path");
    const usersPath = path.join(process.cwd(), "..", "vault", "Users", "users.json");
    const data = fs.readFileSync(usersPath, "utf-8");
    const usersData: UsersData = JSON.parse(data);
    return usersData.users;
  } catch (error) {
    console.error("Error reading users.json:", error);
    return [];
  }
}
