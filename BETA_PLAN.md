# SchoolSkim Beta Launch Plan

## Product

A $3/month service that turns the firehose of school emails into a 2-minute
daily digest. Parents forward their school emails to a personalized address;
every evening they get a clean briefing with action items, upcoming events,
and quick hits — grouped by child, with links back to the original emails.

---

## Phase 1: Foundation (Week 1-2)

### Domain & Brand

**Top domain picks** (check availability on Namecheap/Porkbun):
1. SchoolSkim.com — immediately communicates the value prop
2. DailyBell.app — school bell metaphor + daily cadence
3. NoteSift.com — "sift" perfectly describes the filtering action
4. BellNote.com — clean, professional
5. RecapKid.com — obvious and friendly

Budget: ~$10-15/year for domain.

### Email Receiving Setup (Amazon SES Inbound)

This is the core of the forwarding model — no OAuth, no CASA assessment.

**Step by step:**

1. **Register your domain** with Route 53 (or any DNS provider)

2. **Set up Amazon SES for inbound email:**
   - Open the SES console → Email receiving → Create rule set
   - Add an MX record to your domain's DNS:
     ```
     MX 10 inbound-smtp.us-east-1.amazonaws.com
     ```
   - Create a receipt rule that triggers a Lambda function (or saves to S3)
   - This lets you receive email at any address @yourdomain.com

3. **Generate per-user forwarding addresses:**
   - Each user gets a unique address: `u-{user_id}@schoolskim.com`
   - When SES receives an email to that address, it triggers processing
   - The user sets up forwarding rules in Gmail/Outlook to auto-forward
     school emails to their SchoolSkim address

4. **SES receipt rule → Lambda function:**
   - Lambda receives the raw email (headers, body, attachments)
   - Parse with Python's `email` stdlib module
   - Store parsed email in DynamoDB (or Postgres) keyed by user_id + timestamp
   - Cost: Lambda free tier covers 1M requests/month

5. **Daily digest cron:**
   - EventBridge (CloudWatch Events) triggers a Lambda at 6 PM per user's timezone
   - Lambda pulls that user's emails from the last 24 hours
   - Sends batch to Claude Haiku for summarization
   - Sends digest email via SES outbound

**SES costs at scale:**
- Inbound: $0.10 per 1,000 emails (first 1,000 free/month)
- Outbound: $0.10 per 1,000 emails + $0.12/GB data
- 1,000 users × 200 inbound + 20 outbound/month = ~$22/month

### Hosting Architecture

**Serverless stack (cheapest, scales automatically):**

| Component | Service | Cost |
|-----------|---------|------|
| Email receiving | SES Inbound + Lambda | ~$22/month at 1K users |
| Email storage | DynamoDB | ~$5/month at 1K users |
| Digest generation | Lambda + Claude API | ~$20/month (Haiku) |
| Digest sending | SES Outbound | Included above |
| Landing page / dashboard | Vercel or Cloudflare Pages | Free |
| Auth + user management | Clerk or Auth.js | Free tier |
| Payments | Stripe | 2.9% + $0.30/txn |
| DNS | Route 53 | $0.50/month per zone |

**Total infrastructure at 1,000 users: ~$50/month**
**Total infrastructure at 100 users: ~$10/month**
**Total infrastructure at 10 users: ~$2/month**

### Database Schema (DynamoDB)

```
Users table:
  user_id (PK) | email | forward_address | children[] | timezone | stripe_id | created_at

Emails table:
  user_id (PK) | received_at (SK) | subject | sender | body | raw_message_id

Digests table:
  user_id (PK) | sent_at (SK) | markdown | email_count
```

---

## Phase 2: Landing Page & Payments (Week 2-3)

### Landing Page

Build a single-page site. Keep it dead simple.

**Sections:**
1. Hero: "Your school emails, skimmed." + screenshot of a sample digest
2. How it works: Forward → We summarize → You get a digest at 6 PM
3. Pricing: $3/month, cancel anytime, 14-day free trial
4. Sign up button → Stripe Checkout

**Tech:** Next.js on Vercel (free tier) or even a static HTML page on
Cloudflare Pages. Don't overengineer this.

### Stripe Setup

1. Create a Stripe account at stripe.com
2. Create a Product: "SchoolSkim Monthly" — $3.00/month recurring
3. Set up a Checkout Session with `mode: 'subscription'`
4. Add a webhook endpoint to handle:
   - `checkout.session.completed` → provision user, generate forwarding address
   - `customer.subscription.deleted` → deactivate user
   - `invoice.payment_failed` → send warning email
5. Enable the Customer Portal so users can cancel/update payment themselves
6. Set up a 14-day free trial on the subscription

### Onboarding Flow

After payment:
1. User enters their email + children's names/grades/schools
2. System generates their unique forwarding address (e.g., u-a7x3@schoolskim.com)
3. Show step-by-step instructions (with screenshots) for setting up forwarding:
   - **Gmail**: Settings → Forwarding → Add forwarding address → Filters
   - **Outlook**: Rules → Forward emails from [school domains] to [address]
   - **Apple Mail**: Rules → If From contains [school domain] → Forward to [address]
4. Send a test email to verify forwarding works
5. User gets their first digest that evening (or a sample digest immediately)

---

## Phase 3: Core Backend (Week 3-4)

### Summarization Service

Port the existing summarizer to work multi-tenant:

```python
# Per-user summarization with their children context
def summarize_for_user(user_id: str, emails: list[dict]) -> str:
    user = get_user(user_id)
    children = user["children"]  # [{"name": "Spencer", "grade": "6th", "school": "Mason Intermediate"}]
    # Build prompt with this user's children
    # Call Claude Haiku (batch API for cost savings)
    # Return markdown digest
```

**Model choice:**
- Start with Claude Haiku ($0.02/user/month) — test quality
- If quality complaints: upgrade to Sonnet ($0.21/user/month) — still profitable
- The batch digest model is a perfect fit for Anthropic's Batch API (50% off,
  24-hour SLA is fine since you're sending at 6 PM anyway)

### Email Parsing

```python
import email
from email import policy

def parse_inbound(raw_bytes: bytes) -> dict:
    msg = email.message_from_bytes(raw_bytes, policy=policy.default)
    return {
        "subject": msg["subject"],
        "sender": msg["from"],
        "date": msg["date"],
        "message_id": msg["message-id"],
        "body": msg.get_body(preferencelist=("plain", "html")).get_content(),
    }
```

### Digest Delivery

- Send via SES using the same HTML template approach from the current project
- Include unsubscribe link (required by CAN-SPAM)
- Include "Manage subscription" link to Stripe Customer Portal

---

## Phase 4: Beta Launch (Week 4-5)

### Pre-launch (before opening signups)

1. **Privacy policy** — Required. Cover:
   - What data you collect (email content, children's names)
   - How you use it (AI summarization only, not sold)
   - How long you store it (delete after digest sent, or 7-day rolling window)
   - Third parties (Anthropic for summarization, Stripe for payments, AWS for hosting)
   - Use a generator like Termly ($10/month) or write one with Claude

2. **Terms of service** — Cover liability limits, refund policy, service availability

3. **CAN-SPAM compliance:**
   - Physical mailing address in every digest email (PO Box is fine: ~$20/month)
   - Working unsubscribe link
   - Accurate "From" header

4. **Test with 5-10 real parents** (friends, family, school parents you know)
   - Get feedback on digest quality, forwarding setup difficulty, missing features
   - Fix issues before opening to public

### Marketing — First 100 Users

**Free/low-cost channels (start here):**

1. **Your own school community** — Post in your school's parent Facebook group,
   PTO email list, or class WhatsApp group. "I built this thing that
   summarizes all the school emails into one daily digest. Looking for beta
   testers." Parents who share your pain are your best early adopters.

2. **r/parenting, r/Mommit, r/daddit** on Reddit — Post about the problem
   (not the product). "Anyone else drowning in school emails?" Let people
   discover the product in comments. Don't spam.

3. **Local parent Facebook groups** — Every school district has one. Join groups
   for nearby districts (not just your own). Offer free month for beta testers.

4. **Product Hunt launch** — Free. Time it for a Tuesday or Wednesday morning.
   Title: "SchoolSkim — Your school emails, summarized in 2 minutes." Ask
   friends to upvote early.

5. **Hacker News "Show HN"** — Free. The "parent who built a thing" angle plays
   well here. Focus on the technical story.

6. **School PTO newsletters** — Email PTO presidents at local schools. Offer a
   free month for their members. PTOs are always looking for useful resources
   to share.

7. **Local parenting blogs/influencers** — Offer free accounts in exchange for
   an honest review.

**Paid channels (after validating with free channels):**

8. **Facebook/Instagram ads** targeting parents in specific school districts.
   $5-10/day test budget. Target by "parent" interest + geographic radius
   around schools.

9. **Google Ads** on "too many school emails" / "school email overload" type
   queries. Low volume but high intent.

---

## Defensibility & Preventing Copycats

### What WON'T protect you

- **The tech.** A competent developer can clone the core product in a weekend.
  Prompt + email forwarding + SES is not a moat.
- **Price.** Someone can always undercut $3/month. Race-to-bottom pricing is
  not a strategy.
- **AI model choice.** Everyone has access to the same APIs.

### What WILL set you apart

1. **School-specific prompt tuning and knowledge base.**
   Build a database of school-specific context that improves over time:
   - Known sender patterns per district (which senders are always noise)
   - School calendar integration (know when spring break is, when report cards
     come out, testing weeks)
   - District-specific jargon and acronyms
   - This compounds — a copycat starts from zero for every district.

   **How to build it:** After each digest, ask users a one-tap feedback
   question: "Did we miss anything important?" or "Was anything in today's
   digest not useful?" Use this to fine-tune per-district filtering rules.
   Over months, you build a dataset no competitor can replicate without the
   same user base.

2. **Network effects within schools.**
   If 5 parents at Mason Intermediate use SchoolSkim, you know which emails
   from that school are important (because parents engage with them) and which
   are noise (because they don't). New parents at that school get a better
   product on day one. This is a real moat — the product gets better per-school
   as more parents at that school use it.

   **How to build it:** Track which digest items users click on. Aggregate
   anonymously per school. Weight future summarization toward items that
   parents at that school actually care about.

3. **Calendar sync.**
   Extract dates from emails and push them to Google Calendar / Apple Calendar.
   "Field trip permission slip due March 15" → calendar event with reminder.
   This is sticky — once your school events are in a parent's calendar, they
   don't want to switch. Sense AI does this; Magic Mail Machine doesn't.

4. **Family sharing / co-parent support.**
   Let both parents (including divorced/separated households) get the same
   digest. This is a surprisingly underserved need — school emails go to one
   parent's inbox and the other is always out of the loop. Charge $4-5/month
   for a family plan (2 recipients). This also doubles your word-of-mouth —
   the co-parent tells other parents about it.

5. **District partnerships (B2B angle).**
   Once you have 50+ parents in a single district, approach the district:
   "50 of your parents are paying for a service to summarize your emails.
   Want to offer it free to all parents as a district perk?" District pays
   $1-2/student/year (typical school SaaS pricing). This flips the business
   from B2C ($3/month per parent) to B2B ($1-2/student/year paid by district).
   Much stickier — districts sign annual contracts, and switching costs are
   high. A copycat can't just undercut you if you have district contracts.

6. **Brand and trust.**
   Parents are handing you their children's school emails. Trust matters
   enormously. Be transparent about privacy (open-source the summarization
   logic, publish what data you store, offer data deletion). First-mover
   trust advantage is real in a market where parents are protective of their
   kids' information.

### Intellectual property options

- **Trademark** the name. ~$250-350 via USPTO if you file yourself. Protects
  the brand, not the tech.
- **Don't bother with patents.** The tech isn't novel enough, and patent
  litigation is expensive. Your moat is data + network effects, not IP.

### Realistic moat timeline

| Timeframe | Defensibility level |
|-----------|-------------------|
| Month 1-6 | **None.** Anyone can clone it. You compete on execution speed. |
| Month 6-12 | **Weak.** You have user feedback data and per-school tuning that a new entrant doesn't. |
| Year 1-2 | **Moderate.** Network effects kick in if you have density in specific districts. Calendar sync creates switching costs. |
| Year 2+ | **Strong if B2B.** District contracts are sticky. Per-school intelligence is hard to replicate. Brand trust is established. |

The honest truth: for the first 6 months, your only defense is moving faster
than anyone else. The moat builds over time through data, not through code.

---

## Budget Summary

### Startup costs (one-time)

| Item | Cost |
|------|------|
| Domain name | $10-15 |
| Stripe account | Free |
| AWS account | Free |
| Privacy policy (Termly) | $10/month or free generator |
| PO Box (CAN-SPAM) | ~$20/month |
| Trademark (optional) | $250-350 |
| **Total** | **~$50-100 to launch** |

### Monthly costs at scale

| Users | Revenue | Infra | AI (Haiku) | Stripe fees | Net margin |
|-------|---------|-------|------------|-------------|------------|
| 10 | $30 | $2 | $0.20 | $12 | $16 (53%) |
| 100 | $300 | $10 | $2 | $117 | $171 (57%) |
| 1,000 | $3,000 | $50 | $20 | $1,170 | $1,760 (59%) |
| 10,000 | $30,000 | $200 | $200 | $11,700 | $17,900 (60%) |

Note: Stripe fees dominate at every scale. At $3/month, the $0.30 fixed fee
per transaction is 10% of revenue. Consider offering annual plans ($30/year)
to reduce per-transaction overhead.

---

## Milestones

1. **Week 1-2**: Domain, AWS setup, port existing summarizer to Lambda
2. **Week 2-3**: Landing page, Stripe integration, onboarding flow
3. **Week 3-4**: Email receiving pipeline, multi-tenant digest generation
4. **Week 4-5**: Privacy policy, ToS, test with 5-10 friends
5. **Week 5-6**: Public beta launch, post to school parent groups
6. **Month 2-3**: Product Hunt / HN launch, iterate on feedback
7. **Month 3-6**: Calendar sync, family sharing, per-school tuning
8. **Month 6+**: Approach districts for B2B pilot
