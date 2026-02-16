import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { approveItem } from "@/lib/vault";

export async function POST(request: NextRequest) {
  const session = await auth();

  // Check authentication
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Check admin role
  const userRole = (session.user as any).role;
  if (userRole !== "admin") {
    return NextResponse.json({ error: "Forbidden - admin only" }, { status: 403 });
  }

  try {
    const { filePath } = await request.json();

    if (!filePath) {
      return NextResponse.json({ error: "Missing filePath" }, { status: 400 });
    }

    const success = approveItem(filePath);

    if (success) {
      return NextResponse.json({
        success: true,
        message: "Item approved successfully",
      });
    } else {
      return NextResponse.json({ error: "Failed to approve item" }, { status: 500 });
    }
  } catch (error) {
    console.error("Error in approve API:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
