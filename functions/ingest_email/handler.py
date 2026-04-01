"""
Lambda handler: SES inbound email ingestion.

Triggered by SES receipt rule after raw email is stored in S3.
Parses the email, looks up the user by forwarding address, and stores
the parsed email in the Emails DynamoDB table.
"""

import email
import email.policy
import json
import os
import re
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

USERS_TABLE = os.environ["USERS_TABLE"]
EMAILS_TABLE = os.environ["EMAILS_TABLE"]


def lambda_handler(event, context):
    """Process an SES inbound email event."""
    for record in event["Records"]:
        ses_event = record["ses"]
        mail = ses_event["mail"]
        receipt = ses_event["receipt"]

        # Get the recipient (our u-xxx@schoolskim.com address)
        recipients = receipt.get("recipients", [])
        if not recipients:
            print("No recipients found, skipping.")
            continue

        forward_address = recipients[0].lower()
        print(f"Received email for: {forward_address}")

        # Look up the user by forwarding address
        user = _lookup_user(forward_address)
        if not user:
            print(f"No user found for {forward_address}, skipping.")
            continue

        # Fetch raw email from S3 if available, otherwise use SES event data
        subject, sender, body_text, received_at = _parse_from_ses_event(
            mail, ses_event
        )

        # Try to get full body from S3
        s3_info = _get_s3_info(ses_event)
        if s3_info:
            raw_body = _fetch_from_s3(s3_info["bucket"], s3_info["key"])
            if raw_body:
                parsed = _parse_raw_email(raw_body)
                if parsed["body"]:
                    body_text = parsed["body"]
                if parsed["subject"]:
                    subject = parsed["subject"]
                if parsed["sender"]:
                    sender = parsed["sender"]

        # Store in DynamoDB
        _store_email(
            user_id=user["user_id"],
            received_at=received_at,
            subject=subject,
            sender=sender,
            body=body_text,
            raw_message_id=mail.get("messageId", ""),
        )

        print(
            f"Stored email for user {user['user_id']}: "
            f"{subject[:60]}"
        )

    return {"statusCode": 200}


def _lookup_user(forward_address: str) -> dict | None:
    """Find user by their forwarding address using GSI."""
    table = dynamodb.Table(USERS_TABLE)
    resp = table.query(
        IndexName="forward_address-index",
        KeyConditionExpression="forward_address = :addr",
        ExpressionAttributeValues={":addr": forward_address},
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


def _parse_from_ses_event(
    mail: dict, ses_event: dict
) -> tuple[str, str, str, str]:
    """Extract basic email info from the SES event payload."""
    subject = ""
    for header in mail.get("commonHeaders", {}).get("headers", []):
        pass
    subject = mail.get("commonHeaders", {}).get("subject", "(no subject)")
    sender = mail.get("commonHeaders", {}).get("from", [""])[0]
    received_at = mail.get("timestamp", datetime.now(timezone.utc).isoformat())

    # SES doesn't include the body in the event — we get it from S3
    body_text = ""
    return subject, sender, body_text, received_at


def _get_s3_info(ses_event: dict) -> dict | None:
    """Extract S3 bucket/key from the SES action if present."""
    action = ses_event.get("receipt", {}).get("action", {})
    if action.get("type") == "S3":
        return {
            "bucket": action["bucketName"],
            "key": action["objectKey"],
        }
    # If Lambda action, the S3 action ran first — reconstruct from mail ID
    mail_id = ses_event.get("mail", {}).get("messageId", "")
    bucket = os.environ.get("SES_BUCKET") or f"schoolskim-ses-{os.environ.get('STAGE', 'prod')}"
    if mail_id:
        return {"bucket": bucket, "key": f"inbound/{mail_id}"}
    return None


def _fetch_from_s3(bucket: str, key: str) -> str | None:
    """Fetch raw email from S3."""
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Failed to fetch from S3 ({bucket}/{key}): {e}")
        return None


def _parse_raw_email(raw: str) -> dict:
    """Parse a raw RFC 2822 email into subject, sender, and plain text body."""
    msg = email.message_from_string(raw, policy=email.policy.default)

    subject = msg.get("Subject", "(no subject)")
    sender = msg.get("From", "")

    # Extract plain text body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="replace")
                    break
        # Fallback to HTML if no plain text
        if not body:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_text = payload.decode("utf-8", errors="replace")
                        body = _strip_html(html_text)
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            text = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                body = _strip_html(text)
            else:
                body = text

    # Truncate long bodies
    if len(body) > 10000:
        body = body[:10000] + "\n[truncated]"

    return {"subject": subject, "sender": sender, "body": body}


def _strip_html(html_text: str) -> str:
    """Basic HTML to plain text conversion."""
    # Remove style/script blocks
    text = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", html_text, flags=re.S)
    # Replace block elements with newlines
    text = re.sub(r"<(br|p|div|h[1-6]|li|tr)[^>]*>", "\n", text, flags=re.I)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _store_email(
    user_id: str,
    received_at: str,
    subject: str,
    sender: str,
    body: str,
    raw_message_id: str,
) -> None:
    """Write parsed email to the Emails DynamoDB table."""
    table = dynamodb.Table(EMAILS_TABLE)

    # TTL: auto-delete after 30 days
    ttl = int(datetime.now(timezone.utc).timestamp()) + (30 * 86400)

    table.put_item(
        Item={
            "user_id": user_id,
            "received_at": received_at,
            "subject": subject,
            "sender": sender,
            "body": body,
            "raw_message_id": raw_message_id,
            "ttl": ttl,
        }
    )
