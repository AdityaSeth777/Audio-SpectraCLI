import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { getStripe, getPaidPlanPriceId } from "@/lib/stripe";

// Same guard as proxy.ts/lib/entitlement.ts: when Clerk isn't configured,
// proxy.ts's fallback middleware lets this route through unauthenticated
// (rather than clerkMiddleware() throwing on every request), so auth()
// here would otherwise throw its own "can't detect clerkMiddleware()"
// error instead of the clean 401 this route is supposed to return for an
// unauthenticated request. Found by the same E2E pass.
const hasClerkKeys = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY,
);

export async function POST(request: Request) {
  if (!hasClerkKeys) {
    return NextResponse.json({ error: "Not signed in" }, { status: 401 });
  }

  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Not signed in" }, { status: 401 });
  }

  const origin = new URL(request.url).origin;

  const session = await getStripe().checkout.sessions.create({
    mode: "subscription",
    line_items: [{ price: getPaidPlanPriceId(), quantity: 1 }],
    success_url: `${origin}/dashboard?checkout=success`,
    cancel_url: `${origin}/dashboard?checkout=canceled`,
    client_reference_id: userId,
  });

  if (!session.url) {
    return NextResponse.json({ error: "Could not create checkout session" }, { status: 500 });
  }

  return NextResponse.redirect(session.url, 303);
}
