import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { getAwsCredentials, AWS_REGION, USERS_TABLE } from "@/lib/aws";

const useDynamo = !!USERS_TABLE;

async function deactivateUser(stripeCustomerId: string) {
  if (!useDynamo) {
    console.log("DynamoDB not configured, skipping deactivation.");
    return;
  }

  const { DynamoDBClient } = await import("@aws-sdk/client-dynamodb");
  const { DynamoDBDocumentClient, QueryCommand, UpdateCommand } = await import(
    "@aws-sdk/lib-dynamodb"
  );

  const credentials = getAwsCredentials();
  const client = DynamoDBDocumentClient.from(
    new DynamoDBClient({ region: AWS_REGION, ...(credentials && { credentials }) })
  );

  // Look up user by stripe_customer_id
  const result = await client.send(
    new QueryCommand({
      TableName: USERS_TABLE,
      IndexName: "stripe_customer_id-index",
      KeyConditionExpression: "stripe_customer_id = :cid",
      ExpressionAttributeValues: { ":cid": stripeCustomerId },
      Limit: 1,
    })
  );

  const user = result.Items?.[0];
  if (!user) {
    console.log(`No user found for customer ${stripeCustomerId}`);
    return;
  }

  await client.send(
    new UpdateCommand({
      TableName: USERS_TABLE,
      Key: { user_id: user.user_id },
      UpdateExpression: "SET #status = :status, deactivated_at = :now",
      ExpressionAttributeNames: { "#status": "status" },
      ExpressionAttributeValues: {
        ":status": "inactive",
        ":now": new Date().toISOString(),
      },
    })
  );

  console.log(`Deactivated user ${user.user_id}`);
}

async function sendWarningEmail(customerEmail: string) {
  if (!AWS_REGION) return;

  const { SESClient, SendEmailCommand } = await import(
    "@aws-sdk/client-ses"
  );

  const credentials = getAwsCredentials();
  const ses = new SESClient({ region: AWS_REGION, ...(credentials && { credentials }) });

  await ses.send(
    new SendEmailCommand({
      Source: "SchoolSkim <digest@schoolskim.com>",
      Destination: { ToAddresses: [customerEmail] },
      Message: {
        Subject: { Data: "SchoolSkim — Payment issue" },
        Body: {
          Text: {
            Data:
              "Hi there,\n\n" +
              "We had trouble processing your latest SchoolSkim payment. " +
              "Please update your payment method to keep your daily digests running.\n\n" +
              "You can update your payment info by replying to this email and we'll help you out.\n\n" +
              "Thanks,\nSchoolSkim",
          },
        },
      },
    })
  );

  console.log(`Payment warning email sent to ${customerEmail}`);
}

export async function POST(request: NextRequest) {
  const secretKey = process.env.STRIPE_SECRET_KEY;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!secretKey || !webhookSecret) {
    return NextResponse.json(
      { error: "Stripe is not configured." },
      { status: 503 }
    );
  }

  const stripe = new Stripe(secretKey);
  const body = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json({ error: "Missing signature." }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch {
    return NextResponse.json({ error: "Invalid signature." }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      const customerId =
        typeof session.customer === "string"
          ? session.customer
          : session.customer?.id || "";
      const subscriptionId =
        typeof session.subscription === "string"
          ? session.subscription
          : session.subscription?.id || "";
      const email = session.customer_details?.email || session.customer_email || "";

      console.log(
        `Checkout completed: ${email}, customer=${customerId}, subscription=${subscriptionId}`
      );

      // User record is created during onboarding form submission (/api/onboarding).
      // The webhook fires before the user fills out the form, so we don't create
      // the user here. The onboarding route receives stripeCustomerId and
      // stripeSubscriptionId from the session and stores them with the user.
      break;
    }
    case "customer.subscription.deleted": {
      const subscription = event.data.object as Stripe.Subscription;
      const customerId =
        typeof subscription.customer === "string"
          ? subscription.customer
          : subscription.customer?.id || "";

      console.log(`Subscription cancelled: ${subscription.id}`);
      await deactivateUser(customerId);
      break;
    }
    case "invoice.payment_failed": {
      const invoice = event.data.object as Stripe.Invoice;
      const customerEmail =
        typeof invoice.customer_email === "string"
          ? invoice.customer_email
          : "";

      console.log(`Payment failed for: ${invoice.customer}`);
      if (customerEmail) {
        await sendWarningEmail(customerEmail);
      }
      break;
    }
  }

  return NextResponse.json({ received: true });
}
