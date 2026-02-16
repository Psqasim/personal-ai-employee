import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";
import { getAllVaultSections } from "@/lib/vault";

export async function GET(req: NextRequest) {
  try {
    const session = await auth();

    if (!session || !session.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const userRole = (session.user as any).role;

    // Only admin can access vault browser
    if (userRole !== "admin") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const sections = getAllVaultSections();

    return NextResponse.json({ sections });
  } catch (error) {
    console.error("Error fetching vault sections:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
