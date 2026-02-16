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

  // Check authentication and admin role
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userRole = (session.user as any).role;
  if (userRole !== "admin") {
    return NextResponse.json({ error: "Forbidden - admin only" }, { status: 403 });
  }

  try {
    const { email, password, name, role } = await request.json();

    // Validate input
    if (!email || !password || !name || !role) {
      return NextResponse.json(
        { error: "Missing required fields: email, password, name, role" },
        { status: 400 }
      );
    }

    if (role !== "admin" && role !== "viewer") {
      return NextResponse.json(
        { error: "Invalid role. Must be 'admin' or 'viewer'" },
        { status: 400 }
      );
    }

    // Read existing users
    const usersPath = path.join(process.cwd(), "..", "vault", "Users", "users.json");
    const data = fs.readFileSync(usersPath, "utf-8");
    const usersData: UsersData = JSON.parse(data);

    // Check if user already exists
    if (usersData.users.some((u) => u.email === email)) {
      return NextResponse.json({ error: "User already exists" }, { status: 409 });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 12);

    // Create new user
    const newUser: User = {
      id: String(usersData.users.length + 1),
      email,
      password: hashedPassword,
      role,
      name,
      created_at: new Date().toISOString(),
    };

    // Add to users array
    usersData.users.push(newUser);

    // Write back to file
    fs.writeFileSync(usersPath, JSON.stringify(usersData, null, 2));

    return NextResponse.json({
      success: true,
      message: "User created successfully",
      user: {
        id: newUser.id,
        email: newUser.email,
        name: newUser.name,
        role: newUser.role,
      },
    });
  } catch (error) {
    console.error("Error creating user:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
