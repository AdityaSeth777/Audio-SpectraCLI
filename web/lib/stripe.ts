import Stripe from "stripe";

let cachedStripe: Stripe | null = null;

/**
 * Lazily constructs the Stripe client so route collection at build time
 * doesn't fail when STRIPE_SECRET_KEY isn't set yet (e.g. in CI or before
 * env vars are configured on the hosting platform).
 */
export function getStripe(): Stripe {
  if (!cachedStripe) {
    cachedStripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: "2026-08-26.dahlia",
    });
  }
  return cachedStripe;
}

/** The single paid plan's Stripe Price id (set after creating the product in the Stripe dashboard). */
export function getPaidPlanPriceId(): string {
  return process.env.STRIPE_PAID_PLAN_PRICE_ID!;
}
