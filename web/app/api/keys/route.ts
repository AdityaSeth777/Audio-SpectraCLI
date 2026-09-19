import { NextResponse } from "next/server";
import { and, eq, isNull } from "drizzle-orm";
import { db } from "@/lib/db";
import { apiKeys } from "@/lib/db/schema";
import { generateApiKey, hashApiKey } from "@/lib/apiKeys";
import { getEntitlement } from "@/lib/entitlement";

/** Lists the signed-in user's active API keys (never returns key hashes or plaintext). */
export async function GET() {
  const { userId } = await getEntitlement();
  if (!userId) return NextResponse.json({ error: "Not signed in" }, { status: 401 });

  const rows = await db
    .select({
      id: apiKeys.id,
      name: apiKeys.name,
      createdAt: apiKeys.createdAt,
      lastUsedAt: apiKeys.lastUsedAt,
    })
    .from(apiKeys)
    .where(and(eq(apiKeys.ownerId, userId), isNull(apiKeys.revokedAt)));

  return NextResponse.json({ keys: rows });
}

/** Creates a new API key. The plaintext key is returned exactly once — it is never stored. */
export async function POST(request: Request) {
  const { userId } = await getEntitlement();
  if (!userId) return NextResponse.json({ error: "Not signed in" }, { status: 401 });

  const body = await request.json().catch(() => ({}));
  const name = typeof body?.name === "string" && body.name.trim() ? body.name.trim() : "Unnamed key";

  const plaintextKey = generateApiKey();
  const [row] = await db
    .insert(apiKeys)
    .values({ ownerId: userId, name, keyHash: hashApiKey(plaintextKey) })
    .returning({ id: apiKeys.id, name: apiKeys.name, createdAt: apiKeys.createdAt });

  return NextResponse.json({ key: plaintextKey, ...row }, { status: 201 });
}

/** Revokes an API key by id (`?id=`), owned by the signed-in user. */
export async function DELETE(request: Request) {
  const { userId } = await getEntitlement();
  if (!userId) return NextResponse.json({ error: "Not signed in" }, { status: 401 });

  const id = new URL(request.url).searchParams.get("id");
  if (!id) return NextResponse.json({ error: "Missing ?id= query param" }, { status: 400 });

  await db
    .update(apiKeys)
    .set({ revokedAt: new Date() })
    .where(and(eq(apiKeys.id, id), eq(apiKeys.ownerId, userId)));

  return NextResponse.json({ revoked: true });
}
