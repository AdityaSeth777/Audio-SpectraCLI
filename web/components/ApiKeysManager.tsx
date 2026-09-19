"use client";

import { useEffect, useState } from "react";

type ApiKeySummary = {
  id: string;
  name: string;
  createdAt: string;
  lastUsedAt: string | null;
};

export function ApiKeysManager({ isPaid }: { isPaid: boolean }) {
  const [keys, setKeys] = useState<ApiKeySummary[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [justCreatedKey, setJustCreatedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // `loading` starts `true` (initial useState value below) and is only ever
  // set back to `false` here - never re-set to `true` - since a function
  // that calls setState as its first synchronous statement is exactly what
  // react-hooks/set-state-in-effect flags when called from an effect.
  const loadKeys = async () => {
    try {
      const res = await fetch("/api/keys");
      if (!res.ok) throw new Error((await res.json()).error ?? "Failed to load keys");
      const data = await res.json();
      setKeys(data.keys);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // react-hooks/set-state-in-effect flags any effect body that calls a
    // function which may eventually call setState, even across an await.
    // This is the standard fetch-on-mount pattern (no data-fetching library
    // is warranted for one dashboard list) - intentional, not an oversight.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadKeys();
  }, []);

  const refresh = loadKeys;

  const createKey = async () => {
    setError(null);
    setJustCreatedKey(null);
    const res = await fetch("/api/keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newKeyName || undefined }),
    });
    if (!res.ok) {
      setError((await res.json()).error ?? "Failed to create key");
      return;
    }
    const data = await res.json();
    setJustCreatedKey(data.key);
    setNewKeyName("");
    refresh();
  };

  const revokeKey = async (id: string) => {
    await fetch(`/api/keys?id=${id}`, { method: "DELETE" });
    refresh();
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Data/Analysis API Keys</h2>

      {justCreatedKey && (
        <div className="rounded border border-yellow-500/40 bg-yellow-500/10 p-3 text-sm">
          <p className="mb-1 font-medium">
            Copy this key now - it won&apos;t be shown again:
          </p>
          <code className="break-all">{justCreatedKey}</code>
        </div>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}

      {!isPaid && (
        <p className="text-sm text-white/60">
          The Data/Analysis API requires the paid plan - upgrade above to create a key. Existing keys stop
          working immediately if your plan lapses.
        </p>
      )}

      <div className="flex gap-2">
        <input
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
          placeholder="Key name (optional)"
          disabled={!isPaid}
          className="flex-1 rounded border border-white/20 bg-transparent px-3 py-2 text-sm disabled:opacity-50"
        />
        <button
          onClick={createKey}
          disabled={!isPaid}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Create key
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-white/60">Loading...</p>
      ) : keys.length === 0 ? (
        <p className="text-sm text-white/60">No API keys yet.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {keys.map((key) => (
            <li
              key={key.id}
              className="flex items-center justify-between rounded border border-white/10 px-3 py-2 text-sm"
            >
              <div>
                <p className="font-medium">{key.name}</p>
                <p className="text-white/50">
                  Created {new Date(key.createdAt).toLocaleDateString()}
                  {key.lastUsedAt ? ` · last used ${new Date(key.lastUsedAt).toLocaleDateString()}` : " · never used"}
                </p>
              </div>
              <button onClick={() => revokeKey(key.id)} className="text-red-400 hover:underline">
                Revoke
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
