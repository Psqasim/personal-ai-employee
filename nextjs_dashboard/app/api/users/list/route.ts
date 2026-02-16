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

export async function GET(req: NextRequest) {
  try {
    const session = await auth();

    if (!session || !session.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userRole = (session.user as any).role;

    // Only admin can list users
    if (userRole !== "admin") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const usersPath = path.join(process.cwd(), "..", "vault", "Users", "users.json");
    const data = fs.readFileSync(usersPath, "utf-8");
    const usersData: UsersData = JSON.parse(data);

    // Remove password from response
    const safeUsers = usersData.users.map((u) => ({
      id: u.id,
      email: u.email,
      name: u.name,
      role: u.role,
      created_at: u.created_at,
    }));

    return NextResponse.json({ users: safeUsers });
  } catch (error) {
    console.error("Error listing users:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
