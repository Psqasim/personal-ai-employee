import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import fs from "fs";
import path from "path";

interface User {
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

export async function POST(req: NextRequest) {
  try {
    const session = await auth();

    if (!session || !session.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userRole = (session.user as any).role;
    const currentUserId = (session.user as any).id;

    // Only admin can delete users
    if (userRole !== "admin") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const body = await req.json();
    const { userId } = body;

    if (!userId) {
      return NextResponse.json({ error: "User ID required" }, { status: 400 });
    }

    // Prevent deleting yourself
    if (userId === currentUserId) {
      return NextResponse.json(
        { error: "Cannot delete your own account" },
        { status: 400 }
      );
    }

    const usersPath = path.join(process.cwd(), "..", "vault", "Users", "users.json");
    const data = fs.readFileSync(usersPath, "utf-8");
    const usersData: UsersData = JSON.parse(data);

    // Find user
    const userIndex = usersData.users.findIndex((u) => u.id === userId);

    if (userIndex === -1) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    // Remove user
    usersData.users.splice(userIndex, 1);

    // Write updated users
    fs.writeFileSync(usersPath, JSON.stringify(usersData, null, 2));

    return NextResponse.json({ message: "User deleted successfully" });
  } catch (error) {
    console.error("Error deleting user:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
