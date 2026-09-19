import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Named `proxy.ts` per Next.js 16 (the `middleware.ts` convention was renamed
// to `proxy.ts` - see docs/superpowers/specs - Clerk's helper works either way
// since Next only cares about the exported function shape, not the file name.

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/api/presets(.*)",
  "/api/keys(.*)",
  "/api/stripe/checkout(.*)",
]);

// Merely CALLING clerkMiddleware(...)'s returned handler throws
// "Missing publishableKey" for every matched request - including "/",
// "/visualize", and "/api/v1/analyze" (which authenticates its own way,
// via a bearer API key in lib/apiAuth.ts, entirely unrelated to Clerk) -
// even though none of those call auth.protect(). Found by an actual E2E
// run: every route 500'd with no Clerk env vars set, not just the ones
// that are supposed to require sign-in. Falling back to a pass-through
// when Clerk isn't configured keeps the client-only surface (the
// visualizer, local presets, session stats, share links, and the
// Analysis API) working without any account/billing setup, matching
// what the rest of this project explicitly aims for. Routes that
// genuinely need auth (/dashboard, /api/presets, /api/keys,
// /api/stripe/checkout) still fail meaningfully downstream without
// Clerk configured (no session, and no DATABASE_URL either) - they're
// just not protected AT this layer in that unconfigured state, same as
// they wouldn't be protected by a DB that doesn't exist yet either.
const hasClerkKeys = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY,
);

export default hasClerkKeys
  ? clerkMiddleware(async (auth, req) => {
      if (isProtectedRoute(req)) {
        await auth.protect();
      }
    })
  : () => NextResponse.next();

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)"],
};
