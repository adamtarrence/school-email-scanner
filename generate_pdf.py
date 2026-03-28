#!/usr/bin/env python3
"""Generate a PDF version of the beta launch plan."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        "DocTitle", parent=styles["Title"],
        fontSize=24, spaceAfter=6, textColor=HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=HexColor("#666666"), spaceAfter=20,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=18, spaceBefore=24, spaceAfter=10,
        textColor=HexColor("#1a73e8"), borderPadding=(0, 0, 4, 0),
    ))
    styles.add(ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=14, spaceBefore=16, spaceAfter=8,
        textColor=HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=12, spaceBefore=12, spaceAfter=6,
        textColor=HexColor("#555555"),
    ))
    styles.add(ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=15, spaceAfter=8,
        textColor=HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        "BulletItem", parent=styles["Normal"],
        fontSize=10, leading=15, spaceAfter=4,
        leftIndent=20, bulletIndent=8,
        textColor=HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        "SubBulletItem", parent=styles["Normal"],
        fontSize=10, leading=14, spaceAfter=3,
        leftIndent=40, bulletIndent=28,
        textColor=HexColor("#555555"),
    ))
    styles.add(ParagraphStyle(
        "CodeBlock", parent=styles["Normal"],
        fontSize=9, leading=12, spaceAfter=4,
        leftIndent=20, fontName="Courier",
        textColor=HexColor("#444444"),
    ))
    styles.add(ParagraphStyle(
        "TableCell", parent=styles["Normal"],
        fontSize=9, leading=12,
    ))
    styles.add(ParagraphStyle(
        "TableHeader", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
        textColor=HexColor("#ffffff"),
    ))

    story = []

    def h1(text):
        story.append(Paragraph(text, styles["H1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1a73e8")))

    def h2(text):
        story.append(Paragraph(text, styles["H2"]))

    def h3(text):
        story.append(Paragraph(text, styles["H3"]))

    def body(text):
        story.append(Paragraph(text, styles["Body"]))

    def bullet(text):
        story.append(Paragraph(f"\u2022  {text}", styles["BulletItem"]))

    def subbullet(text):
        story.append(Paragraph(f"\u2013  {text}", styles["SubBulletItem"]))

    def code(text):
        story.append(Paragraph(text, styles["CodeBlock"]))

    def spacer(h=6):
        story.append(Spacer(1, h))

    def make_table(headers, rows, col_widths=None):
        data = [headers] + rows
        t = Table(data, colWidths=col_widths, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a73e8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEADING", (0, 0), (-1, -1), 13),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8f9fa")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        spacer(8)

    # ── Title page ──
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("SchoolSkim", styles["DocTitle"]))
    story.append(Paragraph("Beta Launch Plan", styles["Subtitle"]))
    spacer(12)
    body("A $3/month service that turns the firehose of school emails into a 2-minute "
         "daily digest. Parents forward their school emails to a personalized address; "
         "every evening they get a clean briefing with action items, upcoming events, "
         "and quick hits \u2014 grouped by child, with links back to the original emails.")
    story.append(PageBreak())

    # ── Phase 1 ──
    h1("Phase 1: Foundation (Week 1-2)")

    h2("Domain &amp; Brand")
    body("Top domain picks (check availability on Namecheap/Porkbun):")
    bullet("<b>SchoolSkim.com</b> \u2014 immediately communicates the value prop")
    bullet("<b>DailyBell.app</b> \u2014 school bell metaphor + daily cadence")
    bullet("<b>NoteSift.com</b> \u2014 \"sift\" perfectly describes the filtering action")
    bullet("<b>BellNote.com</b> \u2014 clean, professional")
    bullet("<b>RecapKid.com</b> \u2014 obvious and friendly")
    spacer()
    body("Budget: ~$10-15/year for domain.")

    h2("Email Receiving Setup (Amazon SES Inbound)")
    body("This is the core of the forwarding model \u2014 no OAuth, no CASA assessment.")
    spacer()

    bullet("<b>1. Register your domain</b> with Route 53 (or any DNS provider)")
    spacer(4)

    bullet("<b>2. Set up Amazon SES for inbound email:</b>")
    subbullet("Open the SES console \u2192 Email receiving \u2192 Create rule set")
    subbullet("Add an MX record to your domain's DNS:")
    code("MX 10 inbound-smtp.us-east-1.amazonaws.com")
    subbullet("Create a receipt rule that triggers a Lambda function (or saves to S3)")
    subbullet("This lets you receive email at any address @yourdomain.com")
    spacer(4)

    bullet("<b>3. Generate per-user forwarding addresses:</b>")
    subbullet("Each user gets a unique address: u-{user_id}@schoolskim.com")
    subbullet("When SES receives an email to that address, it triggers processing")
    subbullet("The user sets up forwarding rules in Gmail/Outlook to auto-forward school emails")
    spacer(4)

    bullet("<b>4. SES receipt rule \u2192 Lambda function:</b>")
    subbullet("Lambda receives the raw email (headers, body, attachments)")
    subbullet("Parse with Python's email stdlib module")
    subbullet("Store parsed email in DynamoDB keyed by user_id + timestamp")
    subbullet("Cost: Lambda free tier covers 1M requests/month")
    spacer(4)

    bullet("<b>5. Daily digest cron:</b>")
    subbullet("EventBridge triggers a Lambda at 6 PM per user's timezone")
    subbullet("Lambda pulls that user's emails from the last 24 hours")
    subbullet("Sends batch to Claude Haiku for summarization")
    subbullet("Sends digest email via SES outbound")
    spacer()

    body("<b>SES costs at scale:</b> Inbound $0.10/1,000 emails (first 1,000 free). "
         "Outbound $0.10/1,000 + $0.12/GB. At 1,000 users: ~$22/month.")

    h2("Hosting Architecture")
    body("Serverless stack (cheapest, scales automatically):")
    make_table(
        ["Component", "Service", "Cost"],
        [
            ["Email receiving", "SES Inbound + Lambda", "~$22/mo at 1K users"],
            ["Email storage", "DynamoDB", "~$5/mo at 1K users"],
            ["Digest generation", "Lambda + Claude API", "~$20/mo (Haiku)"],
            ["Digest sending", "SES Outbound", "Included above"],
            ["Landing page", "Vercel / Cloudflare Pages", "Free"],
            ["Auth", "Clerk or Auth.js", "Free tier"],
            ["Payments", "Stripe", "2.9% + $0.30/txn"],
            ["DNS", "Route 53", "$0.50/mo"],
        ],
        col_widths=[1.8 * inch, 2.2 * inch, 1.8 * inch],
    )
    bullet("<b>1,000 users:</b> ~$50/month infra")
    bullet("<b>100 users:</b> ~$10/month infra")
    bullet("<b>10 users:</b> ~$2/month infra")

    h2("Database Schema (DynamoDB)")
    body("<b>Users:</b> user_id (PK) | email | forward_address | children[] | timezone | stripe_id")
    body("<b>Emails:</b> user_id (PK) | received_at (SK) | subject | sender | body | raw_message_id")
    body("<b>Digests:</b> user_id (PK) | sent_at (SK) | markdown | email_count")

    story.append(PageBreak())

    # ── Phase 2 ──
    h1("Phase 2: Landing Page &amp; Payments (Week 2-3)")

    h2("Landing Page")
    body("Build a single-page site. Keep it dead simple.")
    bullet("<b>Hero:</b> \"Your school emails, skimmed.\" + screenshot of a sample digest")
    bullet("<b>How it works:</b> Forward \u2192 We summarize \u2192 You get a digest at 6 PM")
    bullet("<b>Pricing:</b> $3/month, cancel anytime, 14-day free trial")
    bullet("<b>Sign up button</b> \u2192 Stripe Checkout")
    spacer()
    body("Tech: Next.js on Vercel (free tier) or static HTML on Cloudflare Pages.")

    h2("Stripe Setup")
    bullet("Create a Stripe account at stripe.com")
    bullet("Create a Product: \"SchoolSkim Monthly\" \u2014 $3.00/month recurring")
    bullet("Set up a Checkout Session with mode: 'subscription'")
    bullet("Add webhook endpoint: checkout.session.completed \u2192 provision user")
    bullet("Enable Customer Portal for self-service cancel/update")
    bullet("Set up a 14-day free trial on the subscription")

    h2("Onboarding Flow")
    body("After payment:")
    bullet("User enters email + children's names/grades/schools")
    bullet("System generates unique forwarding address (e.g., u-a7x3@schoolskim.com)")
    bullet("Show step-by-step instructions with screenshots for forwarding setup:")
    subbullet("<b>Gmail:</b> Settings \u2192 Forwarding \u2192 Add forwarding address \u2192 Filters")
    subbullet("<b>Outlook:</b> Rules \u2192 Forward emails from [school domains]")
    subbullet("<b>Apple Mail:</b> Rules \u2192 If From contains [school domain] \u2192 Forward")
    bullet("Send a test email to verify forwarding works")
    bullet("User gets their first digest that evening (or a sample immediately)")

    story.append(PageBreak())

    # ── Phase 3 ──
    h1("Phase 3: Core Backend (Week 3-4)")

    h2("Summarization Service")
    body("Port the existing summarizer to work multi-tenant. Each user's children "
         "context is injected into the prompt dynamically.")
    spacer()
    body("<b>Model choice:</b>")
    bullet("Start with <b>Claude Haiku</b> ($0.02/user/month) \u2014 test quality")
    bullet("If quality complaints: upgrade to <b>Sonnet</b> ($0.21/user/month) \u2014 still profitable")
    bullet("Batch API (50% off) is a natural fit \u2014 24-hour SLA is fine for 6 PM delivery")

    h2("Email Parsing")
    body("Use Python's built-in email module to parse raw inbound messages. "
         "Extract subject, sender, date, message-id, and body (prefer plain text, fall back to HTML).")

    h2("Digest Delivery")
    bullet("Send via SES using the same HTML template from the current project")
    bullet("Include unsubscribe link (required by CAN-SPAM)")
    bullet("Include \"Manage subscription\" link to Stripe Customer Portal")

    story.append(PageBreak())

    # ── Phase 4 ──
    h1("Phase 4: Beta Launch (Week 4-5)")

    h2("Pre-launch Checklist")
    bullet("<b>Privacy policy</b> \u2014 What you collect, how you use it, how long you store it, third parties")
    bullet("<b>Terms of service</b> \u2014 Liability limits, refund policy, service availability")
    bullet("<b>CAN-SPAM compliance:</b> Physical address in every email, unsubscribe link, accurate From header")
    bullet("<b>Beta test</b> with 5-10 real parents (friends, family, school parents you know)")

    h2("Marketing \u2014 First 100 Users")
    h3("Free / low-cost channels")
    bullet("<b>Your own school community</b> \u2014 Parent Facebook groups, PTO lists, class WhatsApp")
    bullet("<b>Reddit</b> \u2014 r/parenting, r/Mommit, r/daddit. Post about the problem, not the product.")
    bullet("<b>Local parent Facebook groups</b> \u2014 Every district has one. Offer free month for testers.")
    bullet("<b>Product Hunt</b> \u2014 Tuesday/Wednesday launch. Ask friends to upvote early.")
    bullet("<b>Hacker News Show HN</b> \u2014 The \"parent who built a thing\" angle plays well.")
    bullet("<b>PTO newsletters</b> \u2014 Email PTO presidents, offer free month for members.")
    bullet("<b>Local parenting blogs/influencers</b> \u2014 Free accounts for honest reviews.")

    h3("Paid channels (after free validation)")
    bullet("<b>Facebook/Instagram ads</b> \u2014 Target parents by geography near schools. $5-10/day test.")
    bullet("<b>Google Ads</b> \u2014 \"too many school emails\" queries. Low volume, high intent.")

    story.append(PageBreak())

    # ── Defensibility ──
    h1("Defensibility &amp; Preventing Copycats")

    h2("What WON'T Protect You")
    bullet("<b>The tech.</b> A developer can clone the core product in a weekend.")
    bullet("<b>Price.</b> Someone can always undercut $3/month.")
    bullet("<b>AI model choice.</b> Everyone has access to the same APIs.")

    h2("What WILL Set You Apart")

    bullet("<b>1. School-specific prompt tuning and knowledge base.</b> "
           "Build a database of per-district context: known noise senders, school calendars, "
           "district jargon. A copycat starts from zero for every district. Build it via "
           "one-tap feedback after each digest.")
    spacer(4)

    bullet("<b>2. Network effects within schools.</b> "
           "If 5 parents at one school use it, you learn which emails matter there. "
           "New parents get a better product on day one. Track click-through rates per school.")
    spacer(4)

    bullet("<b>3. Calendar sync.</b> "
           "Extract dates and push to Google/Apple Calendar. Creates switching costs \u2014 "
           "once school events are in a parent's calendar, they don't want to re-set-up.")
    spacer(4)

    bullet("<b>4. Family sharing / co-parent support.</b> "
           "Both parents get the same digest. Underserved need in separated households. "
           "Doubles word-of-mouth. Charge $4-5/month for family plan.")
    spacer(4)

    bullet("<b>5. District partnerships (B2B).</b> "
           "Once you have 50+ parents in a district, pitch the district directly. "
           "$1-2/student/year. Annual contracts with high switching costs.")
    spacer(4)

    bullet("<b>6. Brand and trust.</b> "
           "Parents are handing you their children's school emails. Be transparent about privacy. "
           "First-mover trust advantage is real in this market.")

    h2("Moat Timeline")
    make_table(
        ["Timeframe", "Defensibility"],
        [
            ["Month 1-6", "None. Compete on execution speed."],
            ["Month 6-12", "Weak. Per-school tuning data that new entrants lack."],
            ["Year 1-2", "Moderate. Network effects + calendar switching costs."],
            ["Year 2+", "Strong if B2B. District contracts are sticky."],
        ],
        col_widths=[1.5 * inch, 4.3 * inch],
    )

    h2("Intellectual Property")
    bullet("<b>Trademark</b> the name (~$250-350 via USPTO). Protects brand, not tech.")
    bullet("<b>Don't bother with patents.</b> Tech isn't novel enough. Moat is data + network effects.")

    story.append(PageBreak())

    # ── Budget ──
    h1("Budget Summary")

    h2("Startup Costs (One-Time)")
    make_table(
        ["Item", "Cost"],
        [
            ["Domain name", "$10-15"],
            ["Stripe account", "Free"],
            ["AWS account", "Free"],
            ["Privacy policy (Termly)", "$10/month or free generator"],
            ["PO Box (CAN-SPAM)", "~$20/month"],
            ["Trademark (optional)", "$250-350"],
            ["Total", "$50-100 to launch"],
        ],
        col_widths=[3 * inch, 2.8 * inch],
    )

    h2("Monthly Costs at Scale")
    make_table(
        ["Users", "Revenue", "Infra", "AI (Haiku)", "Stripe Fees", "Net Margin"],
        [
            ["10", "$30", "$2", "$0.20", "$12", "$16 (53%)"],
            ["100", "$300", "$10", "$2", "$117", "$171 (57%)"],
            ["1,000", "$3,000", "$50", "$20", "$1,170", "$1,760 (59%)"],
            ["10,000", "$30,000", "$200", "$200", "$11,700", "$17,900 (60%)"],
        ],
        col_widths=[0.7 * inch, 0.9 * inch, 0.7 * inch, 0.9 * inch, 1.1 * inch, 1.3 * inch],
    )
    body("Note: Stripe fees dominate at every scale. At $3/month, the $0.30 fixed fee "
         "per transaction is 10% of revenue. Consider annual plans ($30/year) to reduce overhead.")

    story.append(PageBreak())

    # ── Milestones ──
    h1("Milestones")
    make_table(
        ["Timeline", "Deliverable"],
        [
            ["Week 1-2", "Domain, AWS setup, port summarizer to Lambda"],
            ["Week 2-3", "Landing page, Stripe integration, onboarding flow"],
            ["Week 3-4", "Email receiving pipeline, multi-tenant digest generation"],
            ["Week 4-5", "Privacy policy, ToS, test with 5-10 friends"],
            ["Week 5-6", "Public beta launch, post to school parent groups"],
            ["Month 2-3", "Product Hunt / HN launch, iterate on feedback"],
            ["Month 3-6", "Calendar sync, family sharing, per-school tuning"],
            ["Month 6+", "Approach districts for B2B pilot"],
        ],
        col_widths=[1.3 * inch, 4.5 * inch],
    )

    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    build_pdf("SchoolSkim_Beta_Plan.pdf")
