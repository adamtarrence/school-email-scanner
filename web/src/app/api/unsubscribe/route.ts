import { NextRequest, NextResponse } from "next/server";
import { createHmac } from "crypto";
import { getAwsCredentials, AWS_REGION, USERS_TABLE } from "@/lib/aws";

const UNSUBSCRIBE_SECRET =
  process.env.UNSUBSCRIBE_SECRET || "schoolskim-unsub-default";

export function generateUnsubscribeToken(userId: string): string {
  return createHmac("sha256", UNSUBSCRIBE_SECRET)
    .update(userId)
    .digest("hex")
    .slice(0, 16);
}

function verifyToken(userId: string, token: string): boolean {
  return generateUnsubscribeToken(userId) === token;
}

async function deactivateUser(userId: string): Promise<boolean> {
  if (!USERS_TABLE) return false;

  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, UpdateCommand } = await import(
    "@aws-sdk/lib-dynamodb"
  );

  const credentials = getAwsCredentials();
  const client = DynamoDBDocumentClient.from(
    new DynamoDBClient({
      region: AWS_REGION,
      ...(credentials && { credentials }),
    })
  );

  await client.send(
    new UpdateCommand({
      TableName: USERS_TABLE,
      Key: { user_id: userId },
      UpdateExpression: "SET #status = :status, deactivated_at = :now",
      ExpressionAttributeNames: { "#status": "status" },
      ExpressionAttributeValues: {
        ":status": "inactive",
        ":now": new Date().toISOString(),
      },
    })
  );

  return true;
}

export async function GET(request: NextRequest) {
  const uid = request.nextUrl.searchParams.get("uid");
  const token = request.nextUrl.searchParams.get("token");

  if (!uid || !token) {
    return NextResponse.json(
      { error: "Missing parameters." },
      { status: 400 }
    );
  }

  if (!verifyToken(uid, token)) {
    return NextResponse.json(
      { error: "Invalid unsubscribe link." },
      { status: 403 }
    );
  }

  try {
    await deactivateUser(uid);
  } catch (e) {
    console.error(`Unsubscribe failed for ${uid}:`, e);
    return NextResponse.json(
      { error: "Something went wrong." },
      { status: 500 }
    );
  }

  // Redirect to confirmation page
  return NextResponse.redirect(new URL("/unsubscribe", request.url));
}

// RFC 8058: one-click unsubscribe via POST
export async function POST(request: NextRequest) {
  const uid = request.nextUrl.searchParams.get("uid");
  const token = request.nextUrl.searchParams.get("token");

  if (!uid || !token || !verifyToken(uid, token)) {
    return NextResponse.json({ error: "Invalid." }, { status: 403 });
  }

  try {
    await deactivateUser(uid);
  } catch (e) {
    console.error(`One-click unsubscribe failed for ${uid}:`, e);
    return NextResponse.json({ error: "Failed." }, { status: 500 });
  }

  return NextResponse.json({ unsubscribed: true });
}
