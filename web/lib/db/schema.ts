import { pgTable, text, timestamp, jsonb, uuid } from "drizzle-orm/pg-core";

/** One row per Clerk user, caching Stripe subscription status for entitlement checks. */
export const users = pgTable("users", {
  id: text("id").primaryKey(), // Clerk user id
  stripeCustomerId: text("stripe_customer_id").unique(),
  subscriptionStatus: text("subscription_status").notNull().default("free"), // "free" | "active" | "canceled" | "past_due"
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});

/** Saved slider/theme presets — a paid-tier feature. */
export const presets = pgTable("presets", {
  id: uuid("id").primaryKey().defaultRandom(),
  ownerId: text("owner_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  settings: jsonb("settings").notNull(), // { duration, sampleRate, fftSize, color, frequencyRange, viewMode }
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

/**
 * API keys for the server-side Data/Analysis API product (sub-project #4).
 * Only a SHA-256 hash of the key is stored — the plaintext key is shown to
 * the user exactly once, at creation time, like GitHub personal access tokens.
 */
export const apiKeys = pgTable("api_keys", {
  id: uuid("id").primaryKey().defaultRandom(),
  ownerId: text("owner_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  keyHash: text("key_hash").notNull().unique(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  lastUsedAt: timestamp("last_used_at"),
  revokedAt: timestamp("revoked_at"),
});

/** One row per billed API call — the source of truth for usage-based billing. */
export const apiUsageEvents = pgTable("api_usage_events", {
  id: uuid("id").primaryKey().defaultRandom(),
  apiKeyId: uuid("api_key_id")
    .notNull()
    .references(() => apiKeys.id, { onDelete: "cascade" }),
  endpoint: text("endpoint").notNull(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});
