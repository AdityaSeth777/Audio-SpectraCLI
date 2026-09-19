import { auth } from "@clerk/nextjs/server";
import { db } from "./db";
import { users } from "./db/schema";
import { eq } from "drizzle-orm";

export type SubscriptionStatus = "free" | "active" | "canceled" | "past_due";

/** Server-side entitlement check — reads the cached status synced by the Stripe webhook. */
export async function getEntitlement(): Promise<{
  userId: string | null;
  isPaid: boolean;
  status: SubscriptionStatus;
}> {
  const { userId } = await auth();
  if (!userId) {
    return { userId: null, isPaid: false, status: "free" };
  }

  const [row] = await db.select().from(users).where(eq(users.id, userId)).limit(1);
  const status = (row?.subscriptionStatus ?? "free") as SubscriptionStatus;

  return { userId, isPaid: status === "active", status };
}
