import { NextRequest, NextResponse } from "next/server";
import { verifySelfServiceToken } from "@/lib/tokens";
import { getUserById } from "@/lib/users";

/** Show just enough of the email to be recognizable, without exposing it fully. */
function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!domain) return email;
  const shown = local.slice(0, 2);
  return `${shown}${local.length > 2 ? "…" : ""}@${domain}`;
}

// Minimal status for the self-service account page. Token-gated; intentionally
// returns no PII beyond a masked email (no children names, no Stripe IDs).
export async function GET(request: NextRequest) {
  const uid = request.nextUrl.searchParams.get("uid") || "";
  const token = request.nextUrl.searchParams.get("token") || "";

  if (!uid || !token || !verifySelfServiceToken(uid, token)) {
    return NextResponse.json({ error: "Invalid link." }, { status: 403 });
  }

  const user = await getUserById(uid);
  if (!user) {
    return NextResponse.json({ error: "Account not found." }, { status: 404 });
  }

  return NextResponse.json({
    email: maskEmail(user.email),
    paused: user.paused,
    status: user.status ?? "active",
    digestTime: user.digestTime ?? "",
    timezone: user.timezone ?? "",
    childCount: user.childCount,
  });
}
