"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock, DownloadCloud, FileText, Fingerprint, RefreshCw } from "lucide-react";

type Item = {
  id: string;
  source_id: string;
  title: string;
  url: string;
  external_id: string | null;
  content_hash: string;
  summary: string | null;
  raw_content: string | null;
  status: string;
  normalized_title: string | null;
  normalized_content: string | null;
  normalized_hash: string | null;
  language: string | null;
  is_duplicate: boolean;
  duplicate_of_item_id: string | null;
  normalization_error: string | null;
  normalized_at: string | null;
  published_at: string | null;
  collected_at: string;
  created_at: string;
  updated_at: string;
};

type CollectionRunResult = {
  status: string;
  sources_checked: number;
  fetched: number;
  created: number;
  duplicates: number;
  skipped: number;
  errors: number;
};

type NormalizationRunResult = {
  status: string;
  candidates: number;
  normalized: number;
  duplicates: number;
  failed: number;
  skipped: number;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    }
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? "Request failed");
  }

  return response.json() as Promise<T>;
}

export function IntelligenceCollection() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [normalizing, setNormalizing] = useState(false);
  const [lastRun, setLastRun] = useState<CollectionRunResult | null>(null);
  const [lastNormalization, setLastNormalization] = useState<NormalizationRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const rawItems = useMemo(() => items.filter((item) => item.status === "raw").length, [items]);
  const normalizedItems = useMemo(
    () => items.filter((item) => item.status === "normalized").length,
    [items]
  );

  async function loadItems() {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<Item[]>("/items?limit=25");
      setItems(data);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load items");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let isCurrent = true;

    apiRequest<Item[]>("/items?limit=25")
      .then((data) => {
        if (isCurrent) {
          setItems(data);
          setError(null);
        }
      })
      .catch((loadError: unknown) => {
        if (isCurrent) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load items");
        }
      })
      .finally(() => {
        if (isCurrent) {
          setLoading(false);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  async function runCollection() {
    setCollecting(true);
    setError(null);

    try {
      const result = await apiRequest<CollectionRunResult>("/collection/run", {
        method: "POST"
      });
      setLastRun(result);
      await loadItems();
    } catch (collectionError) {
      setError(
        collectionError instanceof Error ? collectionError.message : "Unable to run collection"
      );
    } finally {
      setCollecting(false);
    }
  }

  async function runNormalization() {
    setNormalizing(true);
    setError(null);

    try {
      const result = await apiRequest<NormalizationRunResult>("/normalization/run", {
        method: "POST"
      });
      setLastNormalization(result);
      await loadItems();
    } catch (normalizationError) {
      setError(
        normalizationError instanceof Error
          ? normalizationError.message
          : "Unable to run normalization"
      );
    } finally {
      setNormalizing(false);
    }
  }

  return (
    <section className="border border-white/10 bg-white/[0.035]">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 p-5">
        <div>
          <h2 className="text-xl font-semibold text-white">Intelligence Collection</h2>
          <p className="mt-1 text-sm text-slate-400">
            {items.length} recent items / {rawItems} raw / {normalizedItems} normalized
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void loadItems()}
            className="inline-flex h-10 items-center gap-2 border border-white/10 px-3 text-sm text-slate-200 transition hover:border-ice/50 hover:text-ice"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => void runCollection()}
            disabled={collecting}
            className="inline-flex h-10 items-center gap-2 bg-signal px-3 text-sm font-semibold text-obsidian transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <DownloadCloud className="h-4 w-4" aria-hidden="true" />
            {collecting ? "Collecting" : "Collect RSS"}
          </button>
          <button
            type="button"
            onClick={() => void runNormalization()}
            disabled={normalizing}
            className="inline-flex h-10 items-center gap-2 border border-signal/40 bg-signal/10 px-3 text-sm font-semibold text-signal transition hover:border-signal hover:bg-signal/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Fingerprint className="h-4 w-4" aria-hidden="true" />
            {normalizing ? "Normalizing" : "Normalize"}
          </button>
        </div>
      </div>

      {lastRun ? (
        <div className="grid gap-3 border-b border-white/10 p-5 text-sm text-slate-300 sm:grid-cols-6">
          <span>Status {lastRun.status}</span>
          <span>Sources {lastRun.sources_checked}</span>
          <span>Fetched {lastRun.fetched}</span>
          <span>Created {lastRun.created}</span>
          <span>Duplicates {lastRun.duplicates}</span>
          <span>Errors {lastRun.errors}</span>
        </div>
      ) : null}

      {lastNormalization ? (
        <div className="grid gap-3 border-b border-white/10 p-5 text-sm text-slate-300 sm:grid-cols-5">
          <span>Status {lastNormalization.status}</span>
          <span>Candidates {lastNormalization.candidates}</span>
          <span>Normalized {lastNormalization.normalized}</span>
          <span>Duplicates {lastNormalization.duplicates}</span>
          <span>Failed {lastNormalization.failed}</span>
        </div>
      ) : null}

      {error ? <div className="border-b border-white/10 p-5 text-sm text-red-300">{error}</div> : null}

      <div className="divide-y divide-white/10">
        {loading ? (
          <div className="p-5 text-sm text-slate-400">Loading items</div>
        ) : items.length === 0 ? (
          <div className="p-5 text-sm text-slate-400">No collected intelligence yet</div>
        ) : (
          items.map((item) => (
            <article key={item.id} className="grid gap-3 p-5">
              <div className="flex flex-wrap items-center gap-3">
                <FileText className="h-4 w-4 text-signal" aria-hidden="true" />
                <h3 className="min-w-0 flex-1 truncate text-base font-semibold text-white">
                  {item.title}
                </h3>
                <span className="border border-white/10 px-2 py-1 text-xs uppercase text-slate-300">
                  {item.status}
                </span>
                {item.language ? (
                  <span className="border border-ice/20 px-2 py-1 text-xs uppercase text-ice">
                    {item.language}
                  </span>
                ) : null}
              </div>
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="truncate text-sm text-ice transition hover:text-signal"
              >
                {item.url}
              </a>
              {item.normalized_content || item.summary ? (
                <p className="line-clamp-2 text-sm leading-6 text-slate-400">
                  {item.normalized_content ?? item.summary}
                </p>
              ) : null}
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                  Collected {new Date(item.collected_at).toLocaleString()}
                </span>
                <span>Hash {(item.normalized_hash ?? item.content_hash).slice(0, 12)}</span>
                {item.is_duplicate ? <span>Duplicate</span> : null}
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
