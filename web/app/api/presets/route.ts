import { NextResponse } from "next/server";
import { and, eq } from "drizzle-orm";
import { db } from "@/lib/db";
import { presets } from "@/lib/db/schema";
import { getEntitlement } from "@/lib/entitlement";

export async function GET() {
  const { userId, isPaid } = await getEntitlement();
  if (!userId || !isPaid) {
    return NextResponse.json({ error: "Presets require a paid plan" }, { status: 403 });
  }

  const rows = await db.select().from(presets).where(eq(presets.ownerId, userId));
  return NextResponse.json({ presets: rows });
}

export async function POST(request: Request) {
  const { userId, isPaid } = await getEntitlement();
  if (!userId || !isPaid) {
    return NextResponse.json({ error: "Presets require a paid plan" }, { status: 403 });
  }

  const body = await request.json();
  if (typeof body?.name !== "string" || !body?.settings) {
    return NextResponse.json({ error: "name and settings are required" }, { status: 400 });
  }

  const [row] = await db
    .insert(presets)
    .values({ ownerId: userId, name: body.name, settings: body.settings })
    .returning();

  return NextResponse.json({ preset: row }, { status: 201 });
}

export async function DELETE(request: Request) {
  const { userId, isPaid } = await getEntitlement();
  if (!userId || !isPaid) {
    return NextResponse.json({ error: "Presets require a paid plan" }, { status: 403 });
  }

  const id = new URL(request.url).searchParams.get("id");
  if (!id) return NextResponse.json({ error: "Missing ?id= query param" }, { status: 400 });

  await db.delete(presets).where(and(eq(presets.id, id), eq(presets.ownerId, userId)));

  return NextResponse.json({ deleted: true });
}
