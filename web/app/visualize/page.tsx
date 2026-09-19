import Link from "next/link";
import { getEntitlement } from "@/lib/entitlement";
import { Visualizer } from "@/components/Visualizer";

export default async function VisualizePage() {
  const { userId, isPaid } = await getEntitlement();

  return (
    <div className="flex flex-1 flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Visualizer</h1>
        <div className="flex items-center gap-4 text-sm">
          {!userId && (
            <Link href="/sign-in" className="underline">
              Sign in to unlock more
            </Link>
          )}
          {userId && !isPaid && (
            <Link href="/dashboard" className="underline">
              Upgrade
            </Link>
          )}
        </div>
      </div>

      <Visualizer isPaid={isPaid} />
    </div>
  );
}
