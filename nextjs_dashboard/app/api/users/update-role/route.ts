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

    // Only admin can update roles
    if (userRole !== "admin") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const body = await req.json();
    const { userId, newRole } = body;

    if (!userId || !newRole) {
      return NextResponse.json(
        { error: "User ID and new role required" },
        { status: 400 }
      );
    }

    if (newRole !== "admin" && newRole !== "viewer") {
      return NextResponse.json(
        { error: "Invalid role. Must be 'admin' or 'viewer'" },
        { status: 400 }
      );
    }

    const usersPath = path.join(process.cwd(), "..", "vault", "Users", "users.json");
    const data = fs.readFileSync(usersPath, "utf-8");
    const usersData: UsersData = JSON.parse(data);

    // Find user
    const user = usersData.users.find((u) => u.id === userId);

    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    // Update role
    user.role = newRole;

    // Write updated users
    fs.writeFileSync(usersPath, JSON.stringify(usersData, null, 2));

    return NextResponse.json({ message: "User role updated successfully" });
  } catch (error) {
    console.error("Error updating user role:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
