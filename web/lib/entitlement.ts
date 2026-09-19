import { auth } from "@clerk/nextjs/server";
import { db } from "./db";
import { users } from "./db/schema";
import { eq } from "drizzle-orm";

export type SubscriptionStatus = "free" | "active" | "canceled" | "past_due";

// Mirrors proxy.ts's own check: when Clerk isn't configured, proxy.ts skips
// clerkMiddleware() entirely (a bare clerkMiddleware() call throws on every
// request otherwise), but auth() independently throws its own "can't detect
// clerkMiddleware()" error when that middleware didn't run - so calling
// auth() has to be skipped here too, for the same reason, or every page that
// calls getEntitlement() (the landing page, /visualize) 500s with no Clerk
// keys set, even though neither of them actually needs a signed-in user.
const hasClerkKeys = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY,
);

/** Server-side entitlement check - reads the cached status synced by the Stripe webhook. */
export async function getEntitlement(): Promise<{
  userId: string | null;
  isPaid: boolean;
  status: SubscriptionStatus;
}> {
  if (!hasClerkKeys) {
    return { userId: null, isPaid: false, status: "free" };
  }

  const { userId } = await auth();
  if (!userId) {
    return { userId: null, isPaid: false, status: "free" };
  }

  const [row] = await db.select().from(users).where(eq(users.id, userId)).limit(1);
  const status = (row?.subscriptionStatus ?? "free") as SubscriptionStatus;

  return { userId, isPaid: status === "active", status };
}
