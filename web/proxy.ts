import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Named `proxy.ts` per Next.js 16 (the `middleware.ts` convention was renamed
// to `proxy.ts` — see docs/superpowers/specs — Clerk's helper works either way
// since Next only cares about the exported function shape, not the file name.

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/api/presets(.*)",
  "/api/keys(.*)",
  "/api/stripe/checkout(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)"],
};
