import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import bcrypt from "bcryptjs";
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

export async function POST(request: NextRequest) {
  const session = await auth();

  // Check authentication
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const currentUserId = (session.user as any).id;
  const currentUserRole = (session.user as any).role;

  try {
    const { userId, password, role } = await request.json();

    // Admin can update anyone, users can update only themselves (password only)
    if (currentUserRole !== "admin" && userId !== currentUserId) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // Non-admins can't change roles
    if (currentUserRole !== "admin" && role !== undefined) {
      return NextResponse.json(
        { error: "Forbidden - only admins can change roles" },
        { status: 403 }
      );
    }

    // Read existing users
    const usersPath = path.join(process.cwd(), "..", "vault", "Users", "users.json");
    const data = fs.readFileSync(usersPath, "utf-8");
    const usersData: UsersData = JSON.parse(data);

    // Find user
    const userIndex = usersData.users.findIndex((u) => u.id === userId);
    if (userIndex === -1) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    // Update password if provided
    if (password) {
      const hashedPassword = await bcrypt.hash(password, 12);
      usersData.users[userIndex].password = hashedPassword;
    }

    // Update role if provided (admin only)
    if (role && currentUserRole === "admin") {
      if (role !== "admin" && role !== "viewer") {
        return NextResponse.json(
          { error: "Invalid role. Must be 'admin' or 'viewer'" },
          { status: 400 }
        );
      }
      usersData.users[userIndex].role = role;
    }

    // Write back to file
    fs.writeFileSync(usersPath, JSON.stringify(usersData, null, 2));

    return NextResponse.json({
      success: true,
      message: "User updated successfully",
    });
  } catch (error) {
    console.error("Error updating user:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
