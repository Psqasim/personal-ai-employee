import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { getPendingApprovals, getVaultStatus } from "@/lib/vault";

export const dynamic = "force-dynamic";

export async function GET() {
  const session = await auth();

  // Check authentication (both admin and viewer can access)
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const pendingApprovals = getPendingApprovals();
    const vaultStatus = getVaultStatus();

    return NextResponse.json({
      approvals: pendingApprovals,
      counts: vaultStatus,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Error in status API:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
