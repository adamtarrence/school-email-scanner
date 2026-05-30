/**
 * Pause / resume a subscriber's billing using Stripe's pause_collection.
 *
 * Pausing with behavior "void" voids any invoices that would be created during
 * the pause, so the customer isn't charged while still keeping the subscription
 * and saved payment method intact (no re-onboarding). Resuming clears
 * pause_collection and normal billing continues.
 *
 * Both calls no-op gracefully when Stripe isn't configured (mirrors the webhook
 * route), so the local/dev account flow works without Stripe.
 */
import Stripe from "stripe";

export interface PauseResult {
  ok: boolean;
  reason?: "stripe-not-configured" | "no-subscription";
}

interface SubRef {
  subscriptionId?: string;
  customerId?: string;
}

function getStripe(): Stripe | null {
  const key = process.env.STRIPE_SECRET_KEY?.trim();
  if (!key) return null;
  return new Stripe(key);
}

/**
 * Resolve a usable subscription id. Prefers the stored id; otherwise looks up
 * the customer's subscriptions (covers legacy users missing the stored id).
 */
async function resolveSubscriptionId(
  stripe: Stripe,
  { subscriptionId, customerId }: SubRef
): Promise<string | null> {
  if (subscriptionId) return subscriptionId;
  if (!customerId) return null;

  const subs = await stripe.subscriptions.list({
    customer: customerId,
    status: "all",
    limit: 10,
  });
  const sub = subs.data.find((s) => s.status !== "canceled") ?? subs.data[0];
  return sub?.id ?? null;
}

export async function pauseSubscription(ref: SubRef): Promise<PauseResult> {
  const stripe = getStripe();
  if (!stripe) return { ok: false, reason: "stripe-not-configured" };

  const subId = await resolveSubscriptionId(stripe, ref);
  if (!subId) return { ok: false, reason: "no-subscription" };

  await stripe.subscriptions.update(subId, {
    pause_collection: { behavior: "void" },
  });
  return { ok: true };
}

export async function resumeSubscription(ref: SubRef): Promise<PauseResult> {
  const stripe = getStripe();
  if (!stripe) return { ok: false, reason: "stripe-not-configured" };

  const subId = await resolveSubscriptionId(stripe, ref);
  if (!subId) return { ok: false, reason: "no-subscription" };

  // Empty string clears pause_collection (Stripe Emptyable param).
  await stripe.subscriptions.update(subId, { pause_collection: "" });
  return { ok: true };
}
