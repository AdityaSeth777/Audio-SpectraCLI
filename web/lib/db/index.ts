import { drizzle, type NeonHttpDatabase } from "drizzle-orm/neon-http";
import { neon } from "@neondatabase/serverless";
import * as schema from "./schema";

let cachedDb: NeonHttpDatabase<typeof schema> | null = null;

/**
 * Lazily constructs the DB client so route collection at build time doesn't
 * fail when DATABASE_URL isn't set yet (mirrors lib/stripe.ts's approach).
 */
function getDb(): NeonHttpDatabase<typeof schema> {
  if (!cachedDb) {
    cachedDb = drizzle(neon(process.env.DATABASE_URL!), { schema });
  }
  return cachedDb;
}

export const db = new Proxy({} as NeonHttpDatabase<typeof schema>, {
  get(_target, prop, receiver) {
    return Reflect.get(getDb(), prop, receiver);
  },
});
