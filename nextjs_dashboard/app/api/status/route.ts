import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { getPendingApprovals, getVaultStatus, getRecentDoneItems } from "@/lib/vault";

export const dynamic = "force-dynamic";

export async function GET() {
  const session = await auth();

  // Check authentication (both admin and viewer can access)
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const userRole = (session.user as any)?.role;
    const isAdmin = userRole === "admin";

    const vaultStatus = getVaultStatus();
    // Viewers only get counts — no sensitive approval/done details
    const pendingApprovals = isAdmin ? getPendingApprovals() : [];
    const recentDone = isAdmin ? getRecentDoneItems(10) : [];

    return NextResponse.json({
      approvals: pendingApprovals,
      counts: vaultStatus,
      recentDone,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Error in status API:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
