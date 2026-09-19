import { NextResponse } from "next/server";
import { authenticateApiRequest } from "@/lib/apiAuth";
import { applyHannWindow, nextPowerOfTwo, rfftMagnitude } from "@/lib/fft";
import { parseWav, UnsupportedWavError } from "@/lib/wav";
import { binToFrequency, downsampleMaxPool, findDominantBin, magnitudeToDb } from "@/lib/dsp";
import { db } from "@/lib/db";
import { apiUsageEvents, users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { getStripe } from "@/lib/stripe";

export const runtime = "nodejs"; // Buffer + WAV byte parsing need the Node runtime, not Edge.

const MAX_SAMPLES = 8192; // caps FFT cost per request; analyzes the first ~0.2s at 44.1kHz
const DEFAULT_BARS = 128;
const ENDPOINT_NAME = "v1/analyze";

export async function POST(request: Request) {
  const authResult = await authenticateApiRequest(request);
  if (!authResult.ok) {
    return NextResponse.json({ error: authResult.error }, { status: authResult.status });
  }

  let decoded: { sampleRate: number; samples: Float32Array };
  const contentType = request.headers.get("content-type") ?? "";

  try {
    if (contentType.includes("audio/wav") || contentType.includes("audio/x-wav")) {
      const buffer = Buffer.from(await request.arrayBuffer());
      decoded = parseWav(buffer);
    } else if (contentType.includes("application/json")) {
      const body = await request.json();
      if (!Array.isArray(body?.samples) || typeof body?.sampleRate !== "number") {
        return NextResponse.json(
          { error: "JSON body must be { samples: number[], sampleRate: number }." },
          { status: 400 },
        );
      }
      decoded = { sampleRate: body.sampleRate, samples: Float32Array.from(body.samples) };
    } else {
      return NextResponse.json(
        { error: "Unsupported Content-Type. Use audio/wav or application/json." },
        { status: 415 },
      );
    }
  } catch (err) {
    const message = err instanceof UnsupportedWavError ? err.message : "Could not parse request body.";
    return NextResponse.json({ error: message }, { status: 400 });
  }

  if (decoded.samples.length === 0) {
    return NextResponse.json({ error: "No audio samples provided." }, { status: 400 });
  }

  const analysisSlice = decoded.samples.subarray(0, Math.min(decoded.samples.length, MAX_SAMPLES));
  const windowed = applyHannWindow(analysisSlice);
  const fftSize = nextPowerOfTwo(windowed.length);
  const padded = new Float32Array(fftSize);
  padded.set(windowed);

  const magnitudes = rfftMagnitude(padded);
  const spectrumDb = magnitudes.map((m) => magnitudeToDb(m));
  const freqBins = Array.from({ length: magnitudes.length }, (_, i) => binToFrequency(i, decoded.sampleRate, fftSize));

  const bars = Math.min(DEFAULT_BARS, magnitudes.length);
  const dominant = findDominantBin(Float32Array.from(magnitudes), decoded.sampleRate, fftSize);

  await recordUsage(authResult.apiKeyId, authResult.ownerId);

  return NextResponse.json({
    sampleRate: decoded.sampleRate,
    fftSize,
    freqBinsHz: downsampleMaxPool(freqBins, bars),
    spectrumDb: downsampleMaxPool(spectrumDb, bars),
    dominantFrequencyHz: dominant.frequencyHz,
    samplesAnalyzed: analysisSlice.length,
  });
}

async function recordUsage(apiKeyId: string, ownerId: string) {
  await db.insert(apiUsageEvents).values({ apiKeyId, endpoint: ENDPOINT_NAME });

  // Best-effort usage report to Stripe metered billing - never fails the API
  // response if Stripe/config is missing, since this product can run and be
  // billed manually (via apiUsageEvents) before metered billing is wired up.
  const meterEventName = process.env.STRIPE_API_USAGE_METER_EVENT_NAME;
  if (!meterEventName) return;

  try {
    const [user] = await db.select().from(users).where(eq(users.id, ownerId)).limit(1);
    if (!user?.stripeCustomerId) return;

    await getStripe().billing.meterEvents.create({
      event_name: meterEventName,
      payload: { stripe_customer_id: user.stripeCustomerId, value: "1" },
    });
  } catch {
    // Swallow - usage is still recorded in apiUsageEvents for manual reconciliation.
  }
}
