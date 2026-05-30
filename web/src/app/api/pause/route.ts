import { NextRequest, NextResponse } from "next/server";
import { verifySelfServiceToken } from "@/lib/tokens";
import { pauseAccount } from "@/lib/account-actions";

function readParams(request: NextRequest) {
  return {
    uid: request.nextUrl.searchParams.get("uid") || "",
    token: request.nextUrl.searchParams.get("token") || "",
  };
}

// Link click from a reminder email / the account page → pause, then land on /account.
export async function GET(request: NextRequest) {
  const { uid, token } = readParams(request);
  if (!uid || !token || !verifySelfServiceToken(uid, token)) {
    return NextResponse.json({ error: "Invalid link." }, { status: 403 });
  }

  try {
    const result = await pauseAccount(uid);
    if (!result.ok) {
      const status = result.error === "not-found" ? 404 : 502;
      return NextResponse.json({ error: result.error }, { status });
    }
  } catch (e) {
    console.error(`Pause failed for ${uid}:`, e);
    return NextResponse.json({ error: "Something went wrong." }, { status: 500 });
  }

  const dest = new URL("/account", request.url);
  dest.searchParams.set("uid", uid);
  dest.searchParams.set("token", token);
  return NextResponse.redirect(dest);
}

// One-click / programmatic pause.
export async function POST(request: NextRequest) {
  const { uid, token } = readParams(request);
  if (!uid || !token || !verifySelfServiceToken(uid, token)) {
    return NextResponse.json({ error: "Invalid." }, { status: 403 });
  }

  try {
    const result = await pauseAccount(uid);
    if (!result.ok) {
      const status = result.error === "not-found" ? 404 : 502;
      return NextResponse.json({ error: result.error }, { status });
    }
    return NextResponse.json({ paused: true });
  } catch (e) {
    console.error(`Pause failed for ${uid}:`, e);
    return NextResponse.json({ error: "Failed." }, { status: 500 });
  }
}
