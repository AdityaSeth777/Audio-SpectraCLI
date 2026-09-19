import Link from "next/link";
import { Show, UserButton } from "@clerk/nextjs";

// <Show>/<UserButton> need clerkMiddleware to have actually run on this
// request to resolve auth state during SSR, and throw otherwise - same
// underlying cause as proxy.ts/lib/entitlement.ts's own guards, just hit
// from a page component instead of middleware or a server action. Found
// by the same E2E pass: "/" 500'd with no Clerk env vars set, even though
// the page itself needs no auth to be useful (it's just a landing page
// linking to /visualize).
const hasClerkKeys = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="absolute top-4 right-4">
        {hasClerkKeys ? (
          <>
            <Show when="signed-in">
              <UserButton />
            </Show>
            <Show when="signed-out">
              <Link href="/sign-in" className="text-sm underline">
                Sign in
              </Link>
            </Show>
          </>
        ) : (
          <Link href="/sign-in" className="text-sm underline">
            Sign in
          </Link>
        )}
      </div>

      <h1 className="text-4xl font-bold">Audio-SpectraCLI</h1>
      <p className="max-w-md text-white/70">
        Real-time audio spectrum visualization, right in your browser. No install, no server round-trip -
        your microphone audio never leaves your device.
      </p>
      <Link href="/visualize" className="rounded bg-blue-600 px-6 py-3 text-white hover:bg-blue-700">
        Open Visualizer
      </Link>
    </div>
  );
}
