"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Clock,
  DownloadCloud,
  ExternalLink,
  Eye,
  Fingerprint,
  Languages,
  RefreshCw,
  Search,
  ShieldAlert
} from "lucide-react";

type Item = {
  id: string;
  source_id: string;
  source_name: string | null;
  title: string;
  url: string;
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
};

type Source = {
  id: string;
  name: string;
  is_enabled: boolean;
  source_type: string;
};

type ItemStats = {
  total: number;
  raw: number;
  normalized: number;
  duplicate: number;
  normalization_error: number;
  languages: Array<{ language: string; count: number }>;
  sources: Array<{
    source_id: string;
    source_name: string;
    count: number;
    last_collected_at: string | null;
  }>;
};

type CollectionRunResult = {
  status: string;
  sources_checked: number;
  fetched: number;
  created: number;
  duplicates: number;
  errors: number;
};

type NormalizationRunResult = {
  status: string;
  candidates: number;
  normalized: number;
  duplicates: number;
  failed: number;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const statusOptions = ["all", "normalized", "raw", "duplicate", "normalization_error"];

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

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Unknown";
}

function compactHash(value: string | null) {
  return value ? value.slice(0, 12) : "pending";
}

export function IntelligenceWorkbench() {
  const [items, setItems] = useState<Item[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [stats, setStats] = useState<ItemStats | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [sourceId, setSourceId] = useState("all");
  const [language, setLanguage] = useState("all");
  const [duplicatesOnly, setDuplicatesOnly] = useState(false);
  const [limit, setLimit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [normalizing, setNormalizing] = useState(false);
  const [lastRun, setLastRun] = useState<CollectionRunResult | null>(null);
  const [lastNormalization, setLastNormalization] = useState<NormalizationRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedItem = useMemo(
    () => items.find((item) => item.id === selectedItemId) ?? items[0] ?? null,
    [items, selectedItemId]
  );
  const languages = useMemo(() => stats?.languages.map((entry) => entry.language) ?? [], [stats]);

  async function loadSources() {
    const data = await apiRequest<Source[]>("/sources");
    setSources(data.filter((source) => source.source_type === "rss"));
  }

  async function loadStats() {
    const data = await apiRequest<ItemStats>("/items/stats");
    setStats(data);
  }

  async function loadItems() {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ limit: String(limit) });

      if (sourceId !== "all") {
        params.set("source_id", sourceId);
      }

      if (status !== "all") {
        params.set("status", status);
      }

      if (language !== "all") {
        params.set("language", language);
      }

      if (duplicatesOnly) {
        params.set("is_duplicate", "true");
      }

      if (search.trim().length >= 2) {
        params.set("search", search.trim());
      }

      const data = await apiRequest<Item[]>(`/items?${params.toString()}`);
      setItems(data);

      if (!data.some((item) => item.id === selectedItemId)) {
        setSelectedItemId(data[0]?.id ?? null);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load intelligence");
    } finally {
      setLoading(false);
    }
  }

  async function refreshAll() {
    await Promise.all([loadSources(), loadStats(), loadItems()]);
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshAll();
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadItems();
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, sourceId, language, duplicatesOnly, limit]);

  async function runCollection() {
    setCollecting(true);
    setError(null);

    try {
      const result = await apiRequest<CollectionRunResult>("/collection/run", { method: "POST" });
      setLastRun(result);
      await refreshAll();
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
      const result = await apiRequest<NormalizationRunResult>("/normalization/run?limit=500", {
        method: "POST"
      });
      setLastNormalization(result);
      await refreshAll();
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
    <section className="grid gap-6">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {[
          { label: "Items", value: stats?.total ?? 0 },
          { label: "Normalized", value: stats?.normalized ?? 0 },
          { label: "Raw", value: stats?.raw ?? 0 },
          { label: "Duplicates", value: stats?.duplicate ?? 0 },
          { label: "Errors", value: stats?.normalization_error ?? 0 }
        ].map((metric) => (
          <div key={metric.label} className="border border-white/10 bg-white/[0.04] p-4">
            <p className="text-sm text-slate-400">{metric.label}</p>
            <p className="mt-2 text-2xl font-semibold text-white">{metric.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="border border-white/10 bg-white/[0.035]">
          <div className="grid gap-4 border-b border-white/10 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-white">Intelligence</h2>
                <p className="mt-1 text-sm text-slate-400">
                  {items.length} visible / {stats?.total ?? 0} indexed
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void refreshAll()}
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

            <div className="grid gap-3 lg:grid-cols-[minmax(180px,1fr)_160px_180px_140px_140px]">
              <label className="relative">
                <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-500" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      void loadItems();
                    }
                  }}
                  className="h-10 w-full border border-white/10 bg-obsidian py-2 pl-9 pr-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-signal/60"
                  placeholder="Search intelligence"
                />
              </label>

              <select
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
              >
                {statusOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>

              <select
                value={sourceId}
                onChange={(event) => setSourceId(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
              >
                <option value="all">all sources</option>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>

              <select
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
              >
                <option value="all">all languages</option>
                {languages.map((entry) => (
                  <option key={entry} value={entry}>
                    {entry}
                  </option>
                ))}
              </select>

              <select
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
              >
                {[25, 50, 100, 200].map((value) => (
                  <option key={value} value={value}>
                    {value} rows
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
              <label className="inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={duplicatesOnly}
                  onChange={(event) => setDuplicatesOnly(event.target.checked)}
                  className="h-4 w-4 accent-emerald-400"
                />
                Duplicates only
              </label>
              <button
                type="button"
                onClick={() => void loadItems()}
                className="inline-flex h-9 items-center gap-2 border border-white/10 px-3 text-sm text-slate-200 transition hover:border-signal/50 hover:text-signal"
              >
                <Search className="h-4 w-4" aria-hidden="true" />
                Apply
              </button>
            </div>
          </div>

          {lastRun ? (
            <div className="grid gap-3 border-b border-white/10 p-4 text-sm text-slate-300 sm:grid-cols-6">
              <span>Status {lastRun.status}</span>
              <span>Sources {lastRun.sources_checked}</span>
              <span>Fetched {lastRun.fetched}</span>
              <span>Created {lastRun.created}</span>
              <span>Duplicates {lastRun.duplicates}</span>
              <span>Errors {lastRun.errors}</span>
            </div>
          ) : null}

          {lastNormalization ? (
            <div className="grid gap-3 border-b border-white/10 p-4 text-sm text-slate-300 sm:grid-cols-5">
              <span>Status {lastNormalization.status}</span>
              <span>Candidates {lastNormalization.candidates}</span>
              <span>Normalized {lastNormalization.normalized}</span>
              <span>Duplicates {lastNormalization.duplicates}</span>
              <span>Failed {lastNormalization.failed}</span>
            </div>
          ) : null}

          {error ? <div className="border-b border-white/10 p-4 text-sm text-red-300">{error}</div> : null}

          <div className="divide-y divide-white/10">
            {loading ? (
              <div className="p-5 text-sm text-slate-400">Loading intelligence</div>
            ) : items.length === 0 ? (
              <div className="p-5 text-sm text-slate-400">No intelligence matches the filters</div>
            ) : (
              items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedItemId(item.id)}
                  className={
                    selectedItem?.id === item.id
                      ? "grid w-full gap-3 bg-signal/10 p-4 text-left"
                      : "grid w-full gap-3 p-4 text-left transition hover:bg-white/[0.04]"
                  }
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="min-w-0 flex-1 truncate text-sm font-semibold text-white">
                      {item.normalized_title ?? item.title}
                    </h3>
                    <span className="border border-white/10 px-2 py-1 text-xs uppercase text-slate-300">
                      {item.status}
                    </span>
                    {item.language ? (
                      <span className="inline-flex items-center gap-1 border border-ice/20 px-2 py-1 text-xs uppercase text-ice">
                        <Languages className="h-3 w-3" aria-hidden="true" />
                        {item.language}
                      </span>
                    ) : null}
                  </div>

                  <p className="line-clamp-2 text-sm leading-6 text-slate-400">
                    {item.normalized_content ?? item.summary ?? "No content"}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                    <span>{item.source_name ?? "Unknown source"}</span>
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                      {formatDate(item.published_at ?? item.collected_at)}
                    </span>
                    <span>{compactHash(item.normalized_hash ?? item.content_hash)}</span>
                    {item.is_duplicate ? <span>Duplicate</span> : null}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        <aside className="border border-white/10 bg-white/[0.045]">
          {selectedItem ? (
            <div className="grid gap-5 p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-signal">Selected Item</p>
                  <h2 className="mt-3 text-xl font-semibold leading-7 text-white">
                    {selectedItem.normalized_title ?? selectedItem.title}
                  </h2>
                </div>
                <a
                  href={selectedItem.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-10 w-10 shrink-0 items-center justify-center border border-white/10 text-slate-300 transition hover:border-ice/50 hover:text-ice"
                  aria-label="Open original"
                >
                  <ExternalLink className="h-4 w-4" aria-hidden="true" />
                </a>
              </div>

              <div className="grid gap-3 text-sm text-slate-300">
                <div className="grid grid-cols-2 gap-3">
                  <span className="border border-white/10 p-3">
                    Status
                    <strong className="mt-1 block font-semibold text-white">
                      {selectedItem.status}
                    </strong>
                  </span>
                  <span className="border border-white/10 p-3">
                    Language
                    <strong className="mt-1 block font-semibold text-white">
                      {selectedItem.language ?? "unknown"}
                    </strong>
                  </span>
                </div>
                <span className="border border-white/10 p-3">
                  Source
                  <strong className="mt-1 block font-semibold text-white">
                    {selectedItem.source_name ?? selectedItem.source_id}
                  </strong>
                </span>
                <span className="border border-white/10 p-3">
                  Published
                  <strong className="mt-1 block font-semibold text-white">
                    {formatDate(selectedItem.published_at)}
                  </strong>
                </span>
                <span className="border border-white/10 p-3">
                  Normalized
                  <strong className="mt-1 block font-semibold text-white">
                    {formatDate(selectedItem.normalized_at)}
                  </strong>
                </span>
              </div>

              {selectedItem.normalization_error ? (
                <div className="flex gap-3 border border-red-400/30 bg-red-950/20 p-3 text-sm text-red-200">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>{selectedItem.normalization_error}</span>
                </div>
              ) : null}

              <div className="grid gap-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                  <Eye className="h-4 w-4 text-signal" aria-hidden="true" />
                  Content
                </div>
                <p className="max-h-[420px] overflow-auto border border-white/10 bg-obsidian p-4 text-sm leading-6 text-slate-300">
                  {selectedItem.normalized_content ??
                    selectedItem.summary ??
                    selectedItem.raw_content ??
                    "No content"}
                </p>
              </div>

              <div className="grid gap-2 text-xs text-slate-500">
                <span>URL {selectedItem.url}</span>
                <span>Content hash {selectedItem.content_hash}</span>
                <span>Normalized hash {selectedItem.normalized_hash ?? "pending"}</span>
                {selectedItem.duplicate_of_item_id ? (
                  <span>Duplicate of {selectedItem.duplicate_of_item_id}</span>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="p-5 text-sm text-slate-400">No item selected</div>
          )}
        </aside>
      </div>

      {stats ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="border border-white/10 bg-white/[0.035] p-5">
            <h2 className="text-lg font-semibold text-white">Languages</h2>
            <div className="mt-4 grid gap-3">
              {stats.languages.slice(0, 8).map((entry) => (
                <div key={entry.language} className="grid grid-cols-[100px_1fr_64px] items-center gap-3">
                  <span className="text-sm uppercase text-slate-300">{entry.language}</span>
                  <span className="h-2 bg-white/10">
                    <span
                      className="block h-2 bg-signal"
                      style={{ width: `${Math.max(4, (entry.count / stats.total) * 100)}%` }}
                    />
                  </span>
                  <span className="text-right text-sm text-slate-400">{entry.count}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="border border-white/10 bg-white/[0.035] p-5">
            <h2 className="text-lg font-semibold text-white">Top Sources</h2>
            <div className="mt-4 grid gap-3">
              {stats.sources.slice(0, 8).map((entry) => (
                <div key={entry.source_id} className="grid grid-cols-[1fr_72px] gap-3 text-sm">
                  <span className="truncate text-slate-300">{entry.source_name}</span>
                  <span className="text-right text-slate-400">{entry.count}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}
