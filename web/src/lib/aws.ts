/**
 * Shared AWS client configuration.
 *
 * On Vercel, credentials are stored as SCHOOLSKIM_AWS_* to avoid
 * conflicting with Vercel's reserved AWS_* env var namespace.
 * Locally or on Lambda, standard AWS_* vars work too.
 */

export function getAwsCredentials() {
  const accessKeyId =
    process.env.SCHOOLSKIM_AWS_ACCESS_KEY_ID ||
    process.env.AWS_ACCESS_KEY_ID;
  const secretAccessKey =
    process.env.SCHOOLSKIM_AWS_SECRET_ACCESS_KEY ||
    process.env.AWS_SECRET_ACCESS_KEY;

  if (accessKeyId && secretAccessKey) {
    return { accessKeyId, secretAccessKey };
  }

  // Let the SDK use its default credential chain (IAM role, etc.)
  return undefined;
}

export const AWS_REGION = process.env.AWS_REGION || "us-east-1";
export const USERS_TABLE = process.env.USERS_TABLE;
