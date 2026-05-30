/**
 * Orchestrates a pause/resume across DynamoDB (the `paused` flag the Lambdas
 * read) and Stripe billing.
 *
 * Ordering is deliberately asymmetric for safety:
 *  - Pause:  pause billing FIRST. We must never stop a user's service while
 *            still charging them, so a hard Stripe failure aborts before we set
 *            the flag. (Soft outcomes — Stripe not configured, or no
 *            subscription found — don't throw and don't block the pause.)
 *  - Resume: restore service FIRST so digests come back even if billing can't
 *            be restarted; a Stripe failure is reported but not fatal.
 */
import { getUserById, setPaused } from "@/lib/users";
import { pauseSubscription, resumeSubscription } from "@/lib/stripe-pause";

export type ActionResult =
  | { ok: true; billing: "paused" | "resumed" | "skipped" }
  | { ok: false; error: "not-found" | "billing-failed" };

export async function pauseAccount(userId: string): Promise<ActionResult> {
  const user = await getUserById(userId);
  if (!user) return { ok: false, error: "not-found" };

  const ref = {
    subscriptionId: user.stripeSubscriptionId,
    customerId: user.stripeCustomerId,
  };

  try {
    await pauseSubscription(ref);
  } catch (e) {
    console.error(`Stripe pause failed for ${userId}:`, e);
    return { ok: false, error: "billing-failed" };
  }

  await setPaused(userId, true);
  return { ok: true, billing: "paused" };
}

export async function resumeAccount(userId: string): Promise<ActionResult> {
  const user = await getUserById(userId);
  if (!user) return { ok: false, error: "not-found" };

  await setPaused(userId, false);

  const ref = {
    subscriptionId: user.stripeSubscriptionId,
    customerId: user.stripeCustomerId,
  };
  try {
    await resumeSubscription(ref);
  } catch (e) {
    console.error(`Stripe resume failed for ${userId} (service resumed anyway):`, e);
    return { ok: true, billing: "skipped" };
  }

  return { ok: true, billing: "resumed" };
}
