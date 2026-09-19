import { getEntitlement } from "@/lib/entitlement";

export default async function DashboardPage() {
  const { isPaid, status } = await getEntitlement();

  return (
    <div className="flex flex-1 flex-col gap-6 p-8">
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
  );
}
