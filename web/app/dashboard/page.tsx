import { getEntitlement } from "@/lib/entitlement";
import { ApiKeysManager } from "@/components/ApiKeysManager";

export default async function DashboardPage() {
  const { isPaid, status } = await getEntitlement();

  return (
    <div className="flex flex-1 flex-col gap-8 p-8">
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p>
          Subscription status: <strong>{status}</strong>
        </p>

        {!isPaid && (
          <form action="/api/stripe/checkout" method="POST">
            <button type="submit" className="rounded bg-blue-600 px-6 py-3 text-white hover:bg-blue-700">
              Upgrade to Paid Plan
            </button>
          </form>
        )}
      </div>

      <hr className="border-white/10" />

      <ApiKeysManager isPaid={isPaid} />
    </div>
  );
}
