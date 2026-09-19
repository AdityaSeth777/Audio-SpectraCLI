import { NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import type Stripe from "stripe";

export async function POST(request: Request) {
  const body = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json({ error: "Missing signature" }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      const userId = session.client_reference_id;
      const customerId = session.customer as string;
      if (userId) {
        await upsertSubscriptionStatus(userId, customerId, "active");
      }
      break;
    }
    case "customer.subscription.updated":
    case "customer.subscription.deleted": {
      const subscription = event.data.object as Stripe.Subscription;
      const customerId = subscription.customer as string;
      const status = mapStripeStatus(subscription.status);
      await updateStatusByCustomerId(customerId, status);
      break;
    }
    default:
      break;
  }

  return NextResponse.json({ received: true });
}

function mapStripeStatus(stripeStatus: Stripe.Subscription.Status): "active" | "canceled" | "past_due" {
  if (stripeStatus === "active" || stripeStatus === "trialing") return "active";
  if (stripeStatus === "past_due" || stripeStatus === "unpaid") return "past_due";
  return "canceled";
}

async function upsertSubscriptionStatus(
  userId: string,
  stripeCustomerId: string,
  status: "active" | "canceled" | "past_due",
) {
  await db
    .insert(users)
    .values({ id: userId, stripeCustomerId, subscriptionStatus: status })
    .onConflictDoUpdate({
      target: users.id,
      set: { stripeCustomerId, subscriptionStatus: status, updatedAt: new Date() },
    });
}

async function updateStatusByCustomerId(stripeCustomerId: string, status: "active" | "canceled" | "past_due") {
  await db
    .update(users)
    .set({ subscriptionStatus: status, updatedAt: new Date() })
    .where(eq(users.stripeCustomerId, stripeCustomerId));
}
