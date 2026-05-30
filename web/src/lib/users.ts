/**
 * Shared user read/update helpers used by the self-service account routes.
 *
 * Works against DynamoDB when USERS_TABLE is configured, and falls back to the
 * local `.data/users.json` file (same file the onboarding route writes) so the
 * account flow is testable locally without AWS.
 */
import { readFile, writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { getAwsCredentials, AWS_REGION, USERS_TABLE } from "@/lib/aws";

export interface AppUser {
  userId: string;
  email: string;
  status?: string; // "active" | "inactive" (cancelled) | undefined
  paused: boolean;
  digestTime?: string;
  timezone?: string;
  childCount: number;
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
}

const useDynamo = !!USERS_TABLE;

// Local file fallback for dev (mirrors web/src/app/api/onboarding/route.ts)
const DATA_DIR = join(process.cwd(), ".data");
const USERS_FILE = join(DATA_DIR, "users.json");

async function docClient() {
  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient } = await import("@aws-sdk/lib-dynamodb");
  const credentials = getAwsCredentials();
  return DynamoDBDocumentClient.from(
    new DynamoDBClient({
      region: AWS_REGION,
      ...(credentials && { credentials }),
    })
  );
}

export async function getUserById(userId: string): Promise<AppUser | null> {
  if (useDynamo) {
    const { GetCommand } = await import("@aws-sdk/lib-dynamodb");
    const client = await docClient();
    const res = await client.send(
      new GetCommand({ TableName: USERS_TABLE, Key: { user_id: userId } })
    );
    const it = res.Item;
    if (!it) return null;
    // DynamoDB document items come back as NativeAttributeValue (a broad union),
    // so cast scalar fields to string like onboarding/route.ts does.
    return {
      userId: it.user_id as string,
      email: (it.email as string) ?? "",
      status: it.status as string | undefined,
      paused: !!it.paused,
      digestTime: it.digest_time as string | undefined,
      timezone: it.timezone as string | undefined,
      childCount: Array.isArray(it.children) ? it.children.length : 0,
      stripeCustomerId: it.stripe_customer_id as string | undefined,
      stripeSubscriptionId: it.stripe_subscription_id as string | undefined,
    };
  }

  const users = await readLocalUsers();
  const u = users.find((x) => x.userId === userId);
  if (!u) return null;
  return {
    userId: u.userId,
    email: u.email ?? "",
    status: u.status,
    paused: !!u.paused,
    digestTime: u.digestTime,
    timezone: u.timezone,
    childCount: Array.isArray(u.children) ? u.children.length : 0,
    stripeCustomerId: u.stripeCustomerId,
    stripeSubscriptionId: u.stripeSubscriptionId,
  };
}

export async function setPaused(
  userId: string,
  paused: boolean
): Promise<void> {
  const nowIso = new Date().toISOString();

  if (useDynamo) {
    const { UpdateCommand } = await import("@aws-sdk/lib-dynamodb");
    const client = await docClient();
    const tsField = paused ? "paused_at" : "resumed_at";
    // Alias `paused` defensively in case it's a DynamoDB reserved word (same
    // reason the cancellation path aliases `#status`). The `*_at` names follow
    // the existing `deactivated_at` precedent and are safe inline.
    await client.send(
      new UpdateCommand({
        TableName: USERS_TABLE,
        Key: { user_id: userId },
        UpdateExpression: `SET #paused = :p, ${tsField} = :now`,
        ExpressionAttributeNames: { "#paused": "paused" },
        ExpressionAttributeValues: { ":p": paused, ":now": nowIso },
      })
    );
    return;
  }

  const users = await readLocalUsers();
  const u = users.find((x) => x.userId === userId);
  if (!u) return;
  u.paused = paused;
  if (paused) u.pausedAt = nowIso;
  else u.resumedAt = nowIso;
  await writeLocalUsers(users);
}

interface LocalUser {
  userId: string;
  email?: string;
  status?: string;
  paused?: boolean;
  pausedAt?: string;
  resumedAt?: string;
  digestTime?: string;
  timezone?: string;
  children?: unknown[];
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
}

async function readLocalUsers(): Promise<LocalUser[]> {
  try {
    const data = await readFile(USERS_FILE, "utf-8");
    return JSON.parse(data);
  } catch {
    return [];
  }
}

async function writeLocalUsers(users: LocalUser[]): Promise<void> {
  await mkdir(DATA_DIR, { recursive: true });
  await writeFile(USERS_FILE, JSON.stringify(users, null, 2));
}
