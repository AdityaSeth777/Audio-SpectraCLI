# Audio-SpectraCLI - Web

The SaaS surface of Audio-SpectraCLI: a hosted, client-side audio visualizer
with accounts/billing, plus a server-side Data/Analysis API. Next.js 16 (App
Router) + TypeScript, deployed on Vercel.

See the [root README](../Readme.md) for how this fits alongside the native
Python CLI and the VS Code extension.

## What's here

- **`/visualize`** - the visualizer itself. Mic capture and FFT run entirely
  in the browser (Web Audio `AnalyserNode`); no audio is ever sent to a
  server. Free tier: live bars. Paid tier: waterfall view, tuner mode, PNG
  export.
- **`/dashboard`** - subscription status and upgrade flow (Stripe Checkout).
- **`/api/v1/analyze`** - the Data/Analysis API (see below).
- **`/api/keys`, `/api/presets`** - account-scoped CRUD, used by the
  dashboard/visualizer.
- Auth: [Clerk](https://clerk.com). Billing: [Stripe](https://stripe.com).
  DB: Postgres via [Drizzle](https://orm.drizzle.team), tested against
  [Neon](https://neon.tech).

## Setup

1. Copy `.env.example` to `.env.local` and fill in:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` - from a Clerk
     application (dashboard.clerk.com).
   - `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PAID_PLAN_PRICE_ID`
     - create a Stripe product with a recurring price for the paid tier, and
     a webhook endpoint pointed at `/api/stripe/webhook` listening for
     `checkout.session.completed`, `customer.subscription.updated`, and
     `customer.subscription.deleted`.
   - `DATABASE_URL` - a Postgres connection string (a free Neon project works).
   - `STRIPE_API_USAGE_METER_EVENT_NAME` - optional; only needed if you want
     Analysis API usage reported to a Stripe Billing Meter for metered
     billing. Usage is always recorded in the `api_usage_events` table
     regardless of whether this is set.
2. Push the DB schema: `npm run db:push` (uses `drizzle.config.ts` +
   `DATABASE_URL`).
3. `npm install && npm run dev`, open http://localhost:3000.

## Development

```bash
npm run dev          # dev server
npm run build        # production build
npm run test          # vitest - DSP/FFT/WAV/API-key/rate-limit unit tests
npm run lint          # eslint
npx tsc --noEmit       # typecheck
npm run db:generate    # generate a Drizzle migration after editing lib/db/schema.ts
npm run db:push        # push schema changes straight to DATABASE_URL (dev convenience)
```

## Data/Analysis API

`POST /api/v1/analyze` - send audio, get back its spectrum.

**Auth**: `Authorization: Bearer <api key>`. Create a key by signing in and
`POST /api/keys` (see its route for the shape); the plaintext key is
returned exactly once and never stored - only its SHA-256 hash is, so losing
it means generating a new one.

**Request body** - either:
- `Content-Type: audio/wav` with the raw WAV file bytes (16-bit PCM or
  32-bit float, any channel count - multi-channel is averaged to mono).
  Other codecs (MP3, AAC, ...) aren't supported yet.
- `Content-Type: application/json` with `{ "samples": number[], "sampleRate": number }`
  - pre-decoded PCM samples in `[-1, 1]`.

Only the first ~8192 samples (~0.2s at 44.1kHz) are analyzed per request -
this is a single-frame spectral snapshot, not a full-track analysis.

**Response**:

```json
{
  "sampleRate": 44100,
  "fftSize": 8192,
  "freqBinsHz": [/* up to 128 downsampled bin center frequencies */],
  "spectrumDb": [/* matching magnitudes in dB */],
  "dominantFrequencyHz": 440.1,
  "samplesAnalyzed": 8192
}
```

**Rate limit**: 60 requests/minute per API key. Backed by Upstash Redis
(sliding window, correct across multiple serverless instances) when
`UPSTASH_REDIS_REST_URL`/`UPSTASH_REDIS_REST_TOKEN` are set; falls back to
an in-memory single-process limiter otherwise (fine for local dev, not
correct once actually deployed across multiple instances without Upstash
configured - `isRateLimitDistributed()` in `lib/rateLimit.ts` tells you
which mode is active).

**Paid plan required**: creating a key (`POST /api/keys`) and using one
(`POST /api/v1/analyze`) both require the account's subscription to be
`active`. A downgrade takes effect immediately on existing keys too - they
aren't just revoked at creation time.

## Known gaps

- Presets can only be saved/loaded/deleted from the `/visualize` page itself
  (where the live settings live) - there's no separate presets list on
  `/dashboard` the way API keys have one.
- ffmpeg-static's bundled binary is ~44MB (measured on this machine; varies
  by platform) added to the deploy - worth confirming actual function size
  on Vercel once deployed there, in case it bumps against a plan's function
  size limit.
- Stripe metered billing needs a Billing Meter configured on the Stripe
  dashboard side before `STRIPE_API_USAGE_METER_EVENT_NAME` does anything.
- Upstash env vars are optional but recommended before real traffic - see
  the rate limiting note above.
