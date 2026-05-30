import { NextRequest, NextResponse } from "next/server";
import { verifySelfServiceToken } from "@/lib/tokens";
import { resumeAccount } from "@/lib/account-actions";

function readParams(request: NextRequest) {
  return {
    uid: request.nextUrl.searchParams.get("uid") || "",
    token: request.nextUrl.searchParams.get("token") || "",
  };
}

// Link click from the fall reminder email / the account page → resume, then land on /account.
export async function GET(request: NextRequest) {
  const { uid, token } = readParams(request);
  if (!uid || !token || !verifySelfServiceToken(uid, token)) {
    return NextResponse.json({ error: "Invalid link." }, { status: 403 });
  }

  try {
    const result = await resumeAccount(uid);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 404 });
    }
  } catch (e) {
    console.error(`Resume failed for ${uid}:`, e);
    return NextResponse.json({ error: "Something went wrong." }, { status: 500 });
  }

  const dest = new URL("/account", request.url);
  dest.searchParams.set("uid", uid);
  dest.searchParams.set("token", token);
  return NextResponse.redirect(dest);
}

// One-click / programmatic resume.
export async function POST(request: NextRequest) {
  const { uid, token } = readParams(request);
  if (!uid || !token || !verifySelfServiceToken(uid, token)) {
    return NextResponse.json({ error: "Invalid." }, { status: 403 });
  }

  try {
    const result = await resumeAccount(uid);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 404 });
    }
    return NextResponse.json({ resumed: true });
  } catch (e) {
    console.error(`Resume failed for ${uid}:`, e);
    return NextResponse.json({ error: "Failed." }, { status: 500 });
  }
}
