/**
 * Per-user tokens for self-service account links (pause / resume / account view).
 *
 * Mirrors the Python `_self_service_token` used by the Lambdas (digest footer +
 * seasonal reminder emails) so links generated server-side verify here. Signed
 * with the same shared secret as the unsubscribe links, but namespaced with an
 * "account:" prefix so an unsubscribe token can't be replayed as an account
 * token (and vice-versa).
 *
 * The Lambda side and this side MUST use the same UNSUBSCRIBE_SECRET value for
 * tokens to verify — same requirement the existing unsubscribe links already have.
 */
import { createHmac, timingSafeEqual } from "crypto";

const SELF_SERVICE_SECRET =
  process.env.UNSUBSCRIBE_SECRET || "schoolskim-unsub-default";

export function selfServiceToken(userId: string): string {
  return createHmac("sha256", SELF_SERVICE_SECRET)
    .update(`account:${userId}`)
    .digest("hex");
}

export function verifySelfServiceToken(userId: string, token: string): boolean {
  if (!token) return false;
  const expected = selfServiceToken(userId);
  // timingSafeEqual throws on length mismatch, so guard first.
  if (expected.length !== token.length) return false;
  return timingSafeEqual(Buffer.from(expected), Buffer.from(token));
}
