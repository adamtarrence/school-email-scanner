import { NextRequest, NextResponse } from "next/server";
import { randomBytes } from "crypto";
import { readFile, writeFile, mkdir } from "fs/promises";
import { join } from "path";

interface UserRecord {
  userId: string;
  email: string;
  forwardAddress: string;
  children: { name: string; grade: string; school: string }[];
  timezone: string;
  digestTime: string;
  stripeCustomerId: string;
  stripeSubscriptionId: string;
  createdAt: string;
}

// DynamoDB config — when these env vars are set, we write to DynamoDB
const AWS_REGION = process.env.AWS_REGION;
const USERS_TABLE = process.env.USERS_TABLE;
const useDynamo = !!(AWS_REGION && USERS_TABLE);

// Local file fallback for dev
const DATA_DIR = join(process.cwd(), ".data");
const USERS_FILE = join(DATA_DIR, "users.json");

// ── DynamoDB helpers ──

async function dynamoPutUser(user: UserRecord): Promise<void> {
  // Dynamic import so the app doesn't fail if @aws-sdk isn't installed
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, PutCommand } = await import(
    "@aws-sdk/lib-dynamodb"
  );

  const client = DynamoDBDocumentClient.from(
    new DynamoDBClient({ region: AWS_REGION })
  );

  await client.send(
    new PutCommand({
      TableName: USERS_TABLE,
      Item: {
        user_id: user.userId,
        email: user.email,
        forward_address: user.forwardAddress,
        children: user.children,
        timezone: user.timezone,
        digest_time: user.digestTime,
        stripe_customer_id: user.stripeCustomerId,
        stripe_subscription_id: user.stripeSubscriptionId,
        created_at: user.createdAt,
      },
      ConditionExpression: "attribute_not_exists(user_id)",
    })
  );
}

async function dynamoFindByEmail(email: string): Promise<string | null> {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, ScanCommand } = await import(
    "@aws-sdk/lib-dynamodb"
  );

  const client = DynamoDBDocumentClient.from(
    new DynamoDBClient({ region: AWS_REGION })
  );

  const result = await client.send(
    new ScanCommand({
      TableName: USERS_TABLE,
      FilterExpression: "email = :email",
      ExpressionAttributeValues: { ":email": email },
      Limit: 1,
    })
  );

  const items = result.Items || [];
  return items.length > 0 ? (items[0].forward_address as string) : null;
}

// ── Local file helpers ──

async function readUsers(): Promise<UserRecord[]> {
  try {
    const data = await readFile(USERS_FILE, "utf-8");
    return JSON.parse(data);
  } catch {
    return [];
  }
}

async function writeUsers(users: UserRecord[]): Promise<void> {
  await mkdir(DATA_DIR, { recursive: true });
  await writeFile(USERS_FILE, JSON.stringify(users, null, 2));
}

// ── Route handler ──

export async function POST(request: NextRequest) {
  const body = await request.json();
  const {
    email,
    stripeCustomerId,
    stripeSubscriptionId,
    children,
    timezone,
    digestTime,
  } = body;

  if (!email || !children?.length) {
    return NextResponse.json(
      { error: "Email and at least one child are required." },
      { status: 400 }
    );
  }

  for (const child of children) {
    if (!child.name) {
      return NextResponse.json(
        { error: "Each child must have a name." },
        { status: 400 }
      );
    }
  }

  const userId = randomBytes(6).toString("hex");
  const forwardAddress = `u-${userId}@schoolskim.com`;

  const user: UserRecord = {
    userId,
    email,
    forwardAddress,
    children,
    timezone: timezone || "America/New_York",
    digestTime: digestTime || "18:00",
    stripeCustomerId: stripeCustomerId || "",
    stripeSubscriptionId: stripeSubscriptionId || "",
    createdAt: new Date().toISOString(),
  };

  if (useDynamo) {
    // Check if user already onboarded
    const existingAddress = await dynamoFindByEmail(email);
    if (existingAddress) {
      return NextResponse.json({ forwardAddress: existingAddress });
    }
    await dynamoPutUser(user);
  } else {
    // Local file fallback
    const users = await readUsers();
    const existing = users.find((u) => u.email === email);
    if (existing) {
      return NextResponse.json({ forwardAddress: existing.forwardAddress });
    }
    users.push(user);
    await writeUsers(users);
  }

  return NextResponse.json({ forwardAddress });
}
