# SchoolSkim — Operations Manual

Complete documentation of every component, how to access it, what can go wrong, and how to tear it all down.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Details](#component-details)
   - [Vercel (Web App)](#vercel-web-app)
   - [Stripe (Payments)](#stripe-payments)
   - [AWS SES (Email)](#aws-ses-email)
   - [AWS DynamoDB (Database)](#aws-dynamodb-database)
   - [AWS Lambda (Backend Logic)](#aws-lambda-backend-logic)
   - [AWS S3 (Raw Email Storage)](#aws-s3-raw-email-storage)
   - [AWS EventBridge (Scheduling)](#aws-eventbridge-scheduling)
   - [Cloudflare (DNS)](#cloudflare-dns)
   - [GitHub (Source Code)](#github-source-code)
3. [Data Flow](#data-flow)
4. [Environment Variables](#environment-variables)
5. [What Can Go Wrong](#what-can-go-wrong)
6. [Common Operations](#common-operations)
7. [Teardown Procedure](#teardown-procedure)

---

## Architecture Overview

```
User signs up at schoolskim.com
         │
         ▼
   ┌───────────┐    Stripe Checkout     ┌──────────┐
   │  Vercel   │ ◄──────────────────►   │  Stripe  │
   │ (Next.js) │                        │(Payments)│
   └─────┬─────┘                        └────┬─────┘
         │                                   │
         │ /api/onboarding                   │ Webhooks
         ▼                                   ▼
   ┌───────────┐                        ┌──────────┐
   │ DynamoDB  │ ◄──────────────────    │ Webhook  │
   │  (Users)  │   subscription events  │ Handler  │
   └───────────┘                        └──────────┘

Parent forwards school emails
         │
         ▼
   ┌───────────┐    Receipt Rule    ┌──────────────┐
   │  AWS SES  │ ──────────────►   │    S3 Bucket  │
   │ (Inbound) │                   │  (Raw Email)  │
   └─────┬─────┘                   └───────────────┘
         │
         │ Triggers
         ▼
   ┌──────────────┐    Lookup User    ┌───────────┐
   │   Lambda:    │ ─────────────►    │ DynamoDB  │
   │ ingest_email │                   │  (Users)  │
   └──────┬───────┘                   └───────────┘
          │
          │ Store parsed email
          ▼
   ┌───────────┐
   │ DynamoDB  │
   │ (Emails)  │
   └───────────┘

Every evening (per user's chosen time)
         │
   ┌─────┴──────────┐   Fetch emails   ┌───────────┐
   │    Lambda:      │ ────────────►    │ DynamoDB  │
   │  digest_cron    │                  │ (Emails)  │
   └──────┬──┬──────┘                   └───────────┘
          │  │
          │  │ Summarize via Claude API
          │  ▼
          │  ┌───────────┐
          │  │ Anthropic │
          │  │   (AI)    │
          │  └───────────┘
          │
          │ Send digest email
          ▼
   ┌───────────┐                        ┌───────────┐
   │  AWS SES  │  ──────────────────►   │  Parent's │
   │ (Outbound)│                        │   Inbox   │
   └───────────┘                        └───────────┘
```

---

## Component Details

### Vercel (Web App)

**What it does:** Hosts the Next.js web application at schoolskim.com. Serves the landing page, handles Stripe checkout, runs the onboarding flow, and processes Stripe webhooks.

**Access:** https://vercel.com → Log in with your GitHub account (adamtarrence)

**Project:** `adamtarrence-2707s-projects/web`

**Key settings location:**
- **Settings → General:** Project name, root directory (must be `web`)
- **Settings → Environment Variables:** All secrets (Stripe keys, AWS credentials)
- **Settings → Build and Deployment:** Root directory setting
- **Deployments:** View deploy history, redeploy, view build logs

**How deploys work:** Every push to `main` on GitHub auto-deploys to production. You can also redeploy manually from the Deployments page.

**Files involved:**
- `web/src/app/page.tsx` — Landing page (Header, Hero, HowItWorks, Pricing, FAQ, Support, Footer)
- `web/src/app/success/page.tsx` — Post-checkout onboarding flow
- `web/src/app/cancel/page.tsx` — Checkout cancellation page
- `web/src/app/api/checkout/route.ts` — Creates Stripe checkout session
- `web/src/app/api/session/route.ts` — Retrieves Stripe session (used by success page)
- `web/src/app/api/onboarding/route.ts` — Saves user to DynamoDB, generates forwarding address
- `web/src/app/api/webhooks/stripe/route.ts` — Handles Stripe webhook events
- `web/src/components/OnboardingForm.tsx` — Multi-step onboarding form + setup instructions
- `web/src/lib/aws.ts` — Shared AWS credential configuration

**Current domain:** schoolskim.com (DNS via Cloudflare, A record pointing to Vercel)

---

### Stripe (Payments)

**What it does:** Processes $3/month subscriptions with a 14-day free trial. Sends webhook events when subscriptions are created, cancelled, or payments fail.

**Access:** https://dashboard.stripe.com → Log in with your Stripe account

**Account ID:** `acct_1TG0kGBxA2bAYTuQ` ("SchoolSkim")

**Key settings location:**
- **Product catalog:** The "SchoolSkim Daily Digest" product and its $3/month price
- **Developers → API keys:** Secret key (`sk_live_...`) and publishable key
- **Developers → Webhooks:** Endpoint at `https://schoolskim.com/api/webhooks/stripe`
- **Customers:** View all subscribers
- **Subscriptions:** View active/cancelled subscriptions

**Webhook events handled:**
| Event | What happens |
|-------|-------------|
| `checkout.session.completed` | Logs the new subscriber (user record created via onboarding form) |
| `customer.subscription.deleted` | Sets user status to "inactive" in DynamoDB |
| `invoice.payment_failed` | Sends warning email to user via SES |

**Live price ID:** `price_1TG45mBxA2bAYTuQFvN7vt4U`

**Checkout flow:** Landing page → Stripe hosted checkout → redirect to `/success?session_id={id}` → onboarding form

---

### AWS SES (Email)

**What it does:** Two functions:
1. **Inbound:** Receives all email sent to `*@schoolskim.com` and triggers the ingestion Lambda
2. **Outbound:** Sends digest emails and payment warning emails from `digest@schoolskim.com`

**Access:** https://console.aws.amazon.com → Search "SES" → Make sure region is **US East (N. Virginia) / us-east-1**

**Key settings location:**
- **Identities:** Domain verification status for schoolskim.com
- **Configuration sets:** Receipt rules
- **Email receiving → Rule sets:** `schoolskim-prod` (must be the active rule set)
- **Account dashboard:** Sandbox/production status, sending limits

**Domain verification:** Verified via TXT record `_amazonses.schoolskim.com` in Cloudflare DNS.

**DKIM:** Three CNAME records in Cloudflare for email signing.

**Receipt rule:** `schoolskim-ingest-prod`
- Receives email for `schoolskim.com`
- Action 1: Store raw email in S3 bucket `schoolskim-ses-prod` under `inbound/` prefix
- Action 2: Invoke Lambda `schoolskim-ingest-email-prod`

**Sandbox vs Production:**
- **Production mode** (approved 2026-03-30): Can send to any email address. Sending quota: 50,000 messages/day, max send rate: 14 messages/second. (AWS case #177473125700142.)

---

### AWS DynamoDB (Database)

**What it does:** Stores all application data — users, emails, and digest history.

**Access:** https://console.aws.amazon.com → Search "DynamoDB" → Region: us-east-1

**Tables:**

#### `schoolskim-users-prod`
| Attribute | Type | Description |
|-----------|------|-------------|
| `user_id` | String (PK) | Random 12-char hex ID |
| `email` | String | Parent's email address |
| `forward_address` | String | `u-{user_id}@schoolskim.com` |
| `children` | List | `[{name, grade, school}]` |
| `timezone` | String | e.g. `America/New_York` |
| `digest_time` | String | e.g. `18:00` |
| `stripe_customer_id` | String | Stripe customer ID |
| `stripe_subscription_id` | String | Stripe subscription ID |
| `status` | String | `active` or `inactive` (set on cancellation) |
| `created_at` | String | ISO 8601 timestamp |

**Global Secondary Indexes:**
- `forward_address-index` — Used by ingest Lambda to look up user from incoming email address
- `stripe_customer_id-index` — Used by webhook to find user on subscription cancellation

#### `schoolskim-emails-prod`
| Attribute | Type | Description |
|-----------|------|-------------|
| `user_id` | String (PK) | Which user this email belongs to |
| `received_at` | String (SK) | ISO 8601 timestamp |
| `subject` | String | Email subject line |
| `sender` | String | Sender address |
| `body` | String | Plain text body (truncated to 10KB) |
| `raw_message_id` | String | SES message ID |
| `ttl` | Number | Auto-delete after 30 days |

#### `schoolskim-digests-prod`
| Attribute | Type | Description |
|-----------|------|-------------|
| `user_id` | String (PK) | Which user this digest was for |
| `sent_at` | String (SK) | ISO 8601 timestamp |
| `markdown` | String | Raw markdown digest content |
| `email_count` | Number | How many emails were summarized |

**Billing:** PAY_PER_REQUEST (no provisioned capacity — you pay per read/write, pennies at low scale).

---

### AWS Lambda (Backend Logic)

**What it does:** Two serverless functions that handle email processing and digest generation.

**Access:** https://console.aws.amazon.com → Search "Lambda" → Region: us-east-1

#### `schoolskim-ingest-email-prod`
- **Trigger:** SES receipt rule (when email arrives at `*@schoolskim.com`)
- **Timeout:** 15 seconds
- **Memory:** 256 MB
- **Runtime:** Python 3.13
- **What it does:**
  1. Receives SES event with email metadata
  2. Extracts recipient forwarding address
  3. Looks up user in DynamoDB via `forward_address-index` GSI
  4. Fetches raw email from S3
  5. Parses RFC 2822 email (subject, sender, plain text body)
  6. Stores parsed email in `schoolskim-emails-prod` table
- **Source:** `functions/ingest_email/handler.py`

#### `schoolskim-digest-cron-prod`
- **Trigger:** EventBridge schedule — `cron(0 22-3 * * ? *)` (every hour from 22:00-03:00 UTC)
- **Timeout:** 300 seconds (5 minutes)
- **Memory:** 512 MB
- **Runtime:** Python 3.13
- **What it does:**
  1. Scans Users table for users whose digest time matches the current hour (converted from their timezone to UTC)
  2. For each due user, fetches their emails from the last 28 hours
  3. Sends all emails to Claude API (Haiku model) for summarization
  4. Converts markdown digest to HTML email
  5. Sends via SES from `digest@schoolskim.com`
  6. Stores digest record in Digests table
- **Source:** `functions/digest_cron/handler.py`
- **Environment variables:** `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `FROM_EMAIL`, plus all table names

**Timezone handling:** Uses Python's `zoneinfo` module to dynamically resolve UTC offsets, automatically handling DST transitions. Any valid IANA timezone name (e.g. `America/New_York`) is supported.

---

### AWS S3 (Raw Email Storage)

**What it does:** Stores raw email files as received by SES, so the Lambda can fetch and parse them.

**Access:** https://console.aws.amazon.com → Search "S3" → Bucket: `schoolskim-ses-prod`

**Structure:** `inbound/{ses-message-id}` — each file is a complete RFC 2822 email

**Lifecycle rule:** Objects auto-delete after **7 days**. The parsed email is already stored in DynamoDB, so the raw files are only kept briefly for debugging.

---

### AWS EventBridge (Scheduling)

**What it does:** Triggers the digest cron Lambda on a schedule.

**Access:** https://console.aws.amazon.com → Search "EventBridge" → Rules → Region: us-east-1

**Rule:** `schoolskim-prod-DigestCronFunctionScheduleEvening-*`
- **Schedule:** `cron(0 22-3 * * ? *)` — runs at the top of every hour from 22:00 to 03:00 UTC
- **Why these hours:** Covers 6 PM through 9 PM across all US timezones (Eastern through Hawaii)
- **Target:** Lambda function `schoolskim-digest-cron-prod`

---

### Cloudflare (DNS)

**What it does:** Manages DNS for schoolskim.com. Routes web traffic to Vercel and email to AWS SES.

**Access:** https://dash.cloudflare.com → Select schoolskim.com

**DNS Records:**

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| A | @ | 76.76.21.21 | Points schoolskim.com to Vercel |
| MX | @ | inbound-smtp.us-east-1.amazonaws.com (priority 10) | Routes inbound email to AWS SES |
| TXT | _amazonses.schoolskim.com | `FttaH9fxOMHgJXZid1yvk82jaByIcXG27kk5kItfd68=` | SES domain verification |
| CNAME | `gadg2pcgbj272iiows3kii55zv4ienfl._domainkey` | `gadg2pcgbj272iiows3kii55zv4ienfl.dkim.amazonses.com` | DKIM signing (1 of 3) |
| CNAME | `lvivb2dwfoz7cphvc3ij5sqydbgmfqu4._domainkey` | `lvivb2dwfoz7cphvc3ij5sqydbgmfqu4.dkim.amazonses.com` | DKIM signing (2 of 3) |
| CNAME | `ediiy6pwjhrdvjsqcbuddmh5rmawrfre._domainkey` | `ediiy6pwjhrdvjsqcbuddmh5rmawrfre.dkim.amazonses.com` | DKIM signing (3 of 3) |

**Important:** Do NOT enable Cloudflare proxy (orange cloud) on the MX record — it must be DNS-only (grey cloud).

---

### GitHub (Source Code)

**What it does:** Hosts the source code. Pushes to `main` trigger Vercel auto-deploy.

**Access:** https://github.com/adamtarrence/school-email-scanner

**Repository:** Public

**Branch:** `main` (single branch)

**Key directories:**
| Path | Contents |
|------|---------|
| `web/` | Next.js app (Vercel deploys from here) |
| `functions/ingest_email/` | Email ingestion Lambda |
| `functions/digest_cron/` | Digest cron Lambda |
| `infra/` | SAM template and deploy script |
| `*.py` (root) | Original local Python digest engine (legacy, replaced by Lambdas) |
| `.github/workflows/` | Legacy GitHub Actions digest cron (replaced by Lambda) |

**Legacy components still in repo:** The root-level Python files (`digest.py`, `summarizer.py`, `gmail_client.py`, `config.py`, `url_fetcher.py`) and `.github/workflows/digest.yml` are the original local/GitHub Actions digest system. They still work but are superseded by the Lambda-based system. They can be removed once the Lambda pipeline is confirmed working.

---

## Data Flow

### New Subscriber Flow
```
1. User clicks "Start your free trial" on schoolskim.com
2. POST /api/checkout → creates Stripe checkout session (14-day trial, $3/month)
3. User enters payment info on Stripe hosted checkout
4. Stripe redirects to /success?session_id={id}
5. Success page calls GET /api/session to get customer email from Stripe
6. User fills out onboarding form (children, timezone, delivery time)
7. POST /api/onboarding → generates u-{id}@schoolskim.com, stores user in DynamoDB
8. User shown forwarding setup instructions (Gmail/Outlook)
9. Stripe fires checkout.session.completed webhook → logged (user already created above)
```

### Daily Email Flow
```
1. School sends email to parent's Gmail/Outlook
2. Parent's forwarding rule sends copy to u-{id}@schoolskim.com
3. SES receives email at schoolskim.com domain
4. SES receipt rule:
   a. Stores raw email in S3 (schoolskim-ses-prod/inbound/{message-id})
   b. Invokes Lambda (schoolskim-ingest-email-prod)
5. Lambda parses email, looks up user by forwarding address, stores in DynamoDB
```

### Digest Generation Flow
```
1. EventBridge fires every hour from 22:00-03:00 UTC
2. Lambda scans Users table, finds users whose digest hour matches current UTC hour
3. For each user:
   a. Query Emails table for last 28 hours
   b. Send all emails to Claude API with summarization prompt
   c. Convert markdown response to HTML email
   d. Send via SES from digest@schoolskim.com
   e. Store digest record in Digests table
```

### Cancellation Flow
```
1. User cancels subscription in Stripe (via customer portal or you cancel manually)
2. Stripe fires customer.subscription.deleted webhook
3. Webhook handler looks up user by stripe_customer_id in DynamoDB
4. Sets user status to "inactive" and records deactivated_at timestamp
5. Digest cron will still find this user but should be updated to skip inactive users
```

### Payment Failure Flow
```
1. Stripe fails to charge user's payment method
2. Stripe fires invoice.payment_failed webhook
3. Webhook handler sends warning email via SES to the customer's email
```

---

## Environment Variables

### Vercel (Production)
| Variable | Value | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_BASE_URL` | `https://schoolskim.com` | Base URL for Stripe redirect URLs |
| `STRIPE_SECRET_KEY` | `sk_live_...` | Stripe API authentication |
| `STRIPE_PRICE_ID` | `price_1TG45mBxA2bAYTuQFvN7vt4U` | Live $3/month price |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Validates Stripe webhook signatures |
| `USERS_TABLE` | `schoolskim-users-prod` | DynamoDB table name |
| `SCHOOLSKIM_AWS_REGION` | `us-east-1` | AWS region |
| `SCHOOLSKIM_AWS_ACCESS_KEY_ID` | `AKIA...` | AWS credentials for DynamoDB/SES |
| `SCHOOLSKIM_AWS_SECRET_ACCESS_KEY` | `Q3km...` | AWS credentials for DynamoDB/SES |

**Why `SCHOOLSKIM_AWS_*` instead of `AWS_*`?** Vercel reserves the `AWS_*` namespace and silently blocks deploys that set `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`. The app code (`src/lib/aws.ts`) checks for both prefixes.

### Lambda (set via SAM template)
| Variable | Set By | Purpose |
|----------|--------|---------|
| `USERS_TABLE` | CloudFormation | DynamoDB Users table name |
| `EMAILS_TABLE` | CloudFormation | DynamoDB Emails table name |
| `DIGESTS_TABLE` | CloudFormation | DynamoDB Digests table name |
| `EMAIL_DOMAIN` | Parameter | `schoolskim.com` |
| `STAGE` | Parameter | `prod` |
| `ANTHROPIC_API_KEY` | Parameter | Claude API key (for digest cron only) |
| `ANTHROPIC_MODEL` | Parameter | `claude-haiku-4-5-20251001` |
| `FROM_EMAIL` | Template | `digest@schoolskim.com` |

### Local Development
For local development without AWS, the onboarding route falls back to writing users to `web/.data/users.json` (gitignored). No AWS credentials needed locally.

---

## What Can Go Wrong

### Emails not arriving in DynamoDB
**Symptoms:** User forwarded emails but nothing appears in the Emails table.
**Check:**
1. **MX record:** `dig MX schoolskim.com` should return `10 inbound-smtp.us-east-1.amazonaws.com`
2. **SES receipt rule set:** Must be the **active** rule set. Check in SES console → Email receiving → Rule sets. Run `aws ses describe-active-receipt-rule-set --region us-east-1` to verify.
3. **Lambda errors:** Check CloudWatch Logs for `schoolskim-ingest-email-prod`. Common issue: user not found for forwarding address (user hasn't completed onboarding).
4. **S3 permissions:** The SES bucket policy must allow `ses.amazonaws.com` to put objects.

### Digests not being sent
**Symptoms:** Emails are in DynamoDB but user doesn't receive digest.
**Check:**
1. **SES sending limits:** Check SES console → Account dashboard for current quota usage (50k/day limit).
2. **Lambda errors:** Check CloudWatch Logs for `schoolskim-digest-cron-prod`. Common issues: Anthropic API key expired, Claude API rate limit, SES sending limit.
3. **Timezone mismatch:** The digest cron uses `zoneinfo` for automatic DST handling. If a user has an invalid timezone string, it falls back to `America/New_York`.
4. **EventBridge rule disabled:** Check EventBridge → Rules → verify the schedule rule is enabled.
5. **User status:** Users with `status = "inactive"` (cancelled subscription) are automatically skipped by the digest cron.

### Stripe checkout not working
**Symptoms:** "Start your free trial" button fails or redirects to error.
**Check:**
1. **Vercel env vars:** Ensure `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID` are set and are **live mode** values (not `sk_test_*` or `price_test_*`).
2. **Price ID:** Verify the price exists in Stripe dashboard → Product catalog. If you deleted/archived it, create a new one and update Vercel.
3. **Vercel logs:** Check function logs in Vercel dashboard → Logs for `/api/checkout` errors.

### Webhooks not firing
**Symptoms:** Stripe events (cancellation, payment failure) aren't processed.
**Check:**
1. **Webhook endpoint:** Stripe dashboard → Developers → Webhooks. Verify endpoint URL is `https://schoolskim.com/api/webhooks/stripe`.
2. **Webhook secret:** The `STRIPE_WEBHOOK_SECRET` in Vercel must match the signing secret shown in Stripe's webhook endpoint details.
3. **Event selection:** Verify the webhook is listening for `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`.
4. **Webhook logs:** Stripe dashboard → Developers → Webhooks → click the endpoint → "Attempts" tab shows delivery status and response codes.

### Deploy failures on Vercel
**Symptoms:** Push to GitHub doesn't result in a new deployment, or deployment shows "Error".
**Check:**
1. **Root directory:** Vercel project settings → Build and Deployment → Root Directory must be `web`.
2. **Build logs:** Vercel dashboard → Deployments → click failed deploy → Build Logs.
3. **Env var conflicts:** Never use `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` as env var names — use `SCHOOLSKIM_AWS_*` prefix.

### Claude API errors in digest
**Symptoms:** Digest cron Lambda fails with Anthropic API errors.
**Check:**
1. **API key:** Verify `ANTHROPIC_API_KEY` is valid. Test with: `curl https://api.anthropic.com/v1/messages -H "x-api-key: YOUR_KEY" -H "anthropic-version: 2023-06-01"`
2. **Rate limits:** Haiku has generous limits, but if processing many users simultaneously, you could hit them. Lambda logs will show the error.
3. **Model availability:** The model `claude-haiku-4-5-20251001` must still be available. If deprecated, update `ANTHROPIC_MODEL` in the SAM template and redeploy.

### Emails going to spam
**Symptoms:** Digest emails land in spam/junk folder.
**Check:**
1. **DKIM:** `aws ses get-identity-dkim-attributes --identities schoolskim.com --region us-east-1` should show `DkimVerificationStatus: Success`.
2. **DKIM DNS records:** All 3 CNAME records must be in Cloudflare.
3. **SPF:** SES handles SPF automatically when using `amazonses.com` as MAIL FROM.
4. **SES reputation:** Check SES → Reputation metrics for bounce/complaint rates.

---

## Common Operations

### View a user's data
```bash
# By user ID
aws dynamodb get-item --table-name schoolskim-users-prod \
  --key '{"user_id": {"S": "abc123def456"}}' --region us-east-1

# Find user by email
aws dynamodb scan --table-name schoolskim-users-prod \
  --filter-expression "email = :e" \
  --expression-attribute-values '{":e": {"S": "parent@example.com"}}' \
  --region us-east-1
```

### View a user's stored emails
```bash
aws dynamodb query --table-name schoolskim-emails-prod \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values '{":uid": {"S": "abc123def456"}}' \
  --region us-east-1
```

### View a user's digest history
```bash
aws dynamodb query --table-name schoolskim-digests-prod \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values '{":uid": {"S": "abc123def456"}}' \
  --region us-east-1
```

### Manually trigger a digest (for testing)
```bash
aws lambda invoke --function-name schoolskim-digest-cron-prod \
  --region us-east-1 --payload '{}' /dev/stdout
```

### Check Lambda logs
```bash
# Ingest Lambda
aws logs tail /aws/lambda/schoolskim-ingest-email-prod --region us-east-1 --follow

# Digest cron Lambda
aws logs tail /aws/lambda/schoolskim-digest-cron-prod --region us-east-1 --follow
```

### Update Lambda code
```bash
cd /Users/adamtarrence/Library/Mobile\ Documents/com~apple~CloudDocs/Projects/school-email-scanner
PATH="/opt/homebrew/bin:$PATH" sam build --template-file infra/template.yaml --build-dir .aws-sam/build
sam deploy --template-file .aws-sam/build/template.yaml --stack-name schoolskim-prod \
  --region us-east-1 --capabilities CAPABILITY_IAM --no-confirm-changeset --resolve-s3 \
  --parameter-overrides "Stage=prod" "AnthropicApiKey=YOUR_KEY"
```

### Cancel a user's subscription
Do this in Stripe dashboard → Customers → find customer → Subscriptions → Cancel. The webhook will automatically deactivate them in DynamoDB.

### Refund a user
Stripe dashboard → Payments → find the payment → Refund.

---

## Teardown Procedure

If you need to shut everything down, follow these steps in order. Each step is independent — you can stop at any point and the remaining services will continue to function.

### 1. Stop accepting new subscribers
In Vercel, set `STRIPE_PRICE_ID` to an empty string. The checkout button will fail gracefully. Existing subscribers are unaffected.

### 2. Disable digest sending
```bash
# Disable the EventBridge schedule rule
aws events disable-rule --name "schoolskim-prod-DigestCronFunctionScheduleEvening-*" --region us-east-1

# Or find the exact rule name first:
aws events list-rules --region us-east-1 --query "Rules[?contains(Name, 'schoolskim')]"
```

### 3. Cancel all Stripe subscriptions
In Stripe dashboard → Subscriptions → select all → Cancel. Or use the Stripe API:
```bash
# List all active subscriptions
stripe subscriptions list --status active

# Cancel one
stripe subscriptions cancel sub_XXXXXXX
```

### 4. Turn off Stripe live mode
In Stripe dashboard, toggle back to Test mode. No new charges will be processed. Alternatively, delete the webhook endpoint to stop receiving events.

### 5. Stop receiving inbound email
```bash
# Deactivate the SES receipt rule set
aws ses set-active-receipt-rule-set --region us-east-1
# (no --rule-set-name = deactivate all)
```
Emails to `*@schoolskim.com` will now bounce.

### 6. Delete the AWS CloudFormation stack
This removes all AWS resources (DynamoDB tables, Lambdas, S3 bucket, SES rules, IAM roles):
```bash
# First, empty the S3 bucket (CloudFormation can't delete non-empty buckets)
aws s3 rm s3://schoolskim-ses-prod --recursive --region us-east-1

# Delete the stack
aws cloudformation delete-stack --stack-name schoolskim-prod --region us-east-1

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name schoolskim-prod --region us-east-1
```
**WARNING:** This permanently deletes all user data, stored emails, and digest history. There is no undo.

### 7. Remove DNS records
In Cloudflare dashboard → DNS → delete:
- The MX record (stops email routing)
- The `_amazonses` TXT record
- The three `_domainkey` CNAME records

Keep the A record if you want the website to stay up.

### 8. Delete the Vercel project
Vercel dashboard → Project → Settings → scroll to bottom → "Delete Project". Or keep it running as a static landing page.

### 9. Delete the Stripe account
Stripe dashboard → Settings → Account details → Close account. Only do this if you're sure you won't need payment history.

### 10. Close the AWS account (optional)
Only if you have no other AWS usage. AWS Console → Account → Close Account.

### 11. Remove local AWS credentials
```bash
rm ~/.aws/credentials ~/.aws/config
```

---

## Account Credentials Summary

| Service | Login | Access URL |
|---------|-------|-----------|
| Vercel | GitHub (adamtarrence) | https://vercel.com |
| Stripe | Email account | https://dashboard.stripe.com |
| AWS | IAM user `schoolskim-deploy` | https://console.aws.amazon.com |
| Cloudflare | Email account | https://dash.cloudflare.com |
| GitHub | adamtarrence | https://github.com/adamtarrence/school-email-scanner |
| Anthropic | API key in `.env` and Lambda env vars | https://console.anthropic.com |

**AWS IAM user credentials:**
- Access Key ID: `AKIA432WVTKVFXXDPYWR`
- Region: `us-east-1`
- Stack name: `schoolskim-prod`

---

*Last updated: March 28, 2026*
