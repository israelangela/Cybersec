"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Clock,
  DownloadCloud,
  ExternalLink,
  Eye,
  Fingerprint,
  GitBranch,
  Languages,
  Layers,
  Network,
  Sparkles,
  RefreshCw,
  Radar,
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
  ai_summary: string | null;
  ai_severity: string | null;
  ai_confidence: number | null;
  ai_tags: string[] | null;
  ai_cves: string[] | null;
  ai_iocs: string[] | null;
  ai_mitre_attack: string[] | null;
  ai_recommended_actions: string[] | null;
  enriched_at: string | null;
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
  enriched: number;
  enrichment_error: number;
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

type ItemEnrichmentResult = {
  item_id: string;
  status: string;
  error: string | null;
};

type EnrichmentRunResult = {
  status: string;
  candidates: number;
  enriched: number;
  failed: number;
  skipped: number;
};

type CyberEntity = {
  id: string;
  item_id: string;
  enrichment_id: string;
  entity_type: string;
  value: string;
  normalized_value: string;
  severity: string | null;
  confidence: number | null;
  risk_score: number;
  evidence: Record<string, unknown>;
  first_seen_at: string | null;
  last_seen_at: string | null;
};

type CyberEntityAggregate = {
  entity_type: string;
  value: string;
  normalized_value: string;
  occurrences: number;
  max_risk_score: number;
  avg_confidence: number | null;
  severity: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
};

type IntelligenceStats = {
  total_entities: number;
  unique_entities: number;
  high_risk_entities: number;
  by_type: Array<{ entity_type: string; count: number }>;
  top_risks: Array<{
    entity_type: string;
    value: string;
    normalized_value: string;
    risk_score: number;
    severity: string | null;
    item_id: string;
    last_seen_at: string | null;
  }>;
};

type IntelligenceSyncResult = {
  status: string;
  enrichments_checked: number;
  entities_created: number;
  entities_deleted: number;
  skipped: number;
};

type Story = {
  id: string;
  title: string;
  summary: string | null;
  status: string;
  severity: string | null;
  risk_score: number;
  item_count: number;
  entity_count: number;
  keywords: string[];
  entity_fingerprint: string;
  first_seen_at: string | null;
  last_seen_at: string | null;
};

type StoryStats = {
  total_stories: number;
  high_risk_stories: number;
  linked_items: number;
  top_stories: Story[];
};

type StorySyncResult = {
  status: string;
  candidates: number;
  stories_created: number;
  story_items_created: number;
  stories_deleted: number;
  skipped: number;
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
  const [intelligenceStats, setIntelligenceStats] = useState<IntelligenceStats | null>(null);
  const [cyberEntities, setCyberEntities] = useState<CyberEntityAggregate[]>([]);
  const [selectedCyberEntities, setSelectedCyberEntities] = useState<CyberEntity[]>([]);
  const [storyStats, setStoryStats] = useState<StoryStats | null>(null);
  const [stories, setStories] = useState<Story[]>([]);
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
  const [enriching, setEnriching] = useState(false);
  const [batchEnriching, setBatchEnriching] = useState(false);
  const [syncingIntelligence, setSyncingIntelligence] = useState(false);
  const [syncingStories, setSyncingStories] = useState(false);
  const [lastRun, setLastRun] = useState<CollectionRunResult | null>(null);
  const [lastNormalization, setLastNormalization] = useState<NormalizationRunResult | null>(null);
  const [lastEnrichment, setLastEnrichment] = useState<EnrichmentRunResult | null>(null);
  const [lastIntelligenceSync, setLastIntelligenceSync] =
    useState<IntelligenceSyncResult | null>(null);
  const [lastStorySync, setLastStorySync] = useState<StorySyncResult | null>(null);
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

  async function loadIntelligenceStats() {
    const data = await apiRequest<IntelligenceStats>("/intelligence/stats");
    setIntelligenceStats(data);
  }

  async function loadCyberEntities() {
    const data = await apiRequest<CyberEntityAggregate[]>(
      "/intelligence/entities?limit=12&min_score=1"
    );
    setCyberEntities(data);
  }

  async function loadStoryStats() {
    const data = await apiRequest<StoryStats>("/stories/stats");
    setStoryStats(data);
  }

  async function loadStories() {
    const data = await apiRequest<Story[]>("/stories?limit=8");
    setStories(data);
  }

  async function loadSelectedCyberEntities(itemId: string | null) {
    if (!itemId) {
      setSelectedCyberEntities([]);
      return;
    }

    const data = await apiRequest<CyberEntity[]>(`/intelligence/items/${itemId}/entities`);
    setSelectedCyberEntities(data);
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
    await Promise.all([
      loadSources(),
      loadStats(),
      loadIntelligenceStats(),
      loadCyberEntities(),
      loadStoryStats(),
      loadStories(),
      loadItems()
    ]);
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

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadSelectedCyberEntities(selectedItem?.id ?? null);
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedItem?.id]);

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

  async function enrichSelectedItem() {
    if (!selectedItem) {
      return;
    }

    setEnriching(true);
    setError(null);

    try {
      const result = await apiRequest<ItemEnrichmentResult>(
        `/enrichment/items/${selectedItem.id}/run`,
        { method: "POST" }
      );

      if (result.status === "error" || result.status === "skipped") {
        setError(result.error ?? "Unable to enrich item");
      }

      await refreshAll();
    } catch (enrichmentError) {
      setError(enrichmentError instanceof Error ? enrichmentError.message : "Unable to enrich item");
    } finally {
      setEnriching(false);
    }
  }

  async function enrichBatch() {
    setBatchEnriching(true);
    setError(null);

    try {
      const result = await apiRequest<EnrichmentRunResult>("/enrichment/run?limit=10", {
        method: "POST"
      });
      setLastEnrichment(result);
      await refreshAll();
    } catch (enrichmentError) {
      setError(
        enrichmentError instanceof Error ? enrichmentError.message : "Unable to enrich items"
      );
    } finally {
      setBatchEnriching(false);
    }
  }

  async function syncIntelligence() {
    setSyncingIntelligence(true);
    setError(null);

    try {
      const result = await apiRequest<IntelligenceSyncResult>("/intelligence/sync?limit=500", {
        method: "POST"
      });
      setLastIntelligenceSync(result);
      await Promise.all([
        loadStats(),
        loadIntelligenceStats(),
        loadCyberEntities(),
        loadSelectedCyberEntities(selectedItem?.id ?? null)
      ]);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Unable to sync intelligence");
    } finally {
      setSyncingIntelligence(false);
    }
  }

  async function syncStories() {
    setSyncingStories(true);
    setError(null);

    try {
      const result = await apiRequest<StorySyncResult>("/stories/sync?limit=500", {
        method: "POST"
      });
      setLastStorySync(result);
      await Promise.all([loadStoryStats(), loadStories()]);
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Unable to sync stories");
    } finally {
      setSyncingStories(false);
    }
  }

  return (
    <section className="grid gap-6">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-7">
        {[
          { label: "Items", value: stats?.total ?? 0 },
          { label: "Normalized", value: stats?.normalized ?? 0 },
          { label: "Raw", value: stats?.raw ?? 0 },
          { label: "Duplicates", value: stats?.duplicate ?? 0 },
          { label: "Errors", value: stats?.normalization_error ?? 0 },
          { label: "AI Enriched", value: stats?.enriched ?? 0 },
          { label: "AI Errors", value: stats?.enrichment_error ?? 0 }
        ].map((metric) => (
          <div key={metric.label} className="border border-white/10 bg-white/[0.04] p-4">
            <p className="text-sm text-slate-400">{metric.label}</p>
            <p className="mt-2 text-2xl font-semibold text-white">{metric.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 border border-white/10 bg-white/[0.035] p-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
          {[
            {
              label: "Cyber Entities",
              value: intelligenceStats?.total_entities ?? 0,
              icon: Network
            },
            {
              label: "Unique Entities",
              value: intelligenceStats?.unique_entities ?? 0,
              icon: Radar
            },
            {
              label: "High Risk",
              value: intelligenceStats?.high_risk_entities ?? 0,
              icon: Activity
            }
          ].map((metric) => {
            const MetricIcon = metric.icon;

            return (
              <div key={metric.label} className="border border-white/10 bg-obsidian/60 p-4">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <MetricIcon className="h-4 w-4 text-fuchsia-200" aria-hidden="true" />
                  {metric.label}
                </div>
                <p className="mt-2 text-2xl font-semibold text-white">{metric.value}</p>
              </div>
            );
          })}
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <section className="min-w-0">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-white">Top Risk Entities</h2>
              <span className="text-xs uppercase text-slate-500">Score</span>
            </div>
            <div className="mt-4 grid gap-2">
              {(intelligenceStats?.top_risks ?? []).slice(0, 6).map((entity) => (
                <button
                  key={`${entity.item_id}-${entity.normalized_value}`}
                  type="button"
                  onClick={() => setSelectedItemId(entity.item_id)}
                  className="grid grid-cols-[1fr_48px] gap-3 border border-white/10 p-3 text-left transition hover:border-fuchsia-200/40"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold text-slate-200">
                      {entity.normalized_value}
                    </span>
                    <span className="text-xs uppercase text-slate-500">
                      {entity.entity_type} {entity.severity ?? "unknown"}
                    </span>
                  </span>
                  <span className="text-right text-sm font-semibold text-fuchsia-200">
                    {entity.risk_score}
                  </span>
                </button>
              ))}
              {intelligenceStats?.top_risks.length === 0 ? (
                <p className="border border-white/10 p-3 text-sm text-slate-400">
                  No synchronized intelligence entities
                </p>
              ) : null}
            </div>
          </section>

          <section className="min-w-0">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-white">Entity Radar</h2>
              <span className="text-xs uppercase text-slate-500">Occurrences</span>
            </div>
            <div className="mt-4 grid gap-2">
              {cyberEntities.slice(0, 6).map((entity) => (
                <div
                  key={`${entity.entity_type}-${entity.normalized_value}`}
                  className="grid grid-cols-[1fr_56px] gap-3 border border-white/10 p-3"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold text-slate-200">
                      {entity.normalized_value}
                    </span>
                    <span className="text-xs uppercase text-slate-500">
                      {entity.entity_type} risk {entity.max_risk_score}
                    </span>
                  </span>
                  <span className="text-right text-sm text-slate-300">
                    {entity.occurrences}
                  </span>
                </div>
              ))}
              {cyberEntities.length === 0 ? (
                <p className="border border-white/10 p-3 text-sm text-slate-400">
                  Run Sync Intel after enriching items
                </p>
              ) : null}
            </div>
          </section>
        </div>
      </div>

      <div className="grid gap-4 border border-white/10 bg-white/[0.035] p-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
          {[
            {
              label: "Stories",
              value: storyStats?.total_stories ?? 0,
              icon: GitBranch
            },
            {
              label: "High Risk Stories",
              value: storyStats?.high_risk_stories ?? 0,
              icon: ShieldAlert
            },
            {
              label: "Linked Items",
              value: storyStats?.linked_items ?? 0,
              icon: Layers
            }
          ].map((metric) => {
            const MetricIcon = metric.icon;

            return (
              <div key={metric.label} className="border border-white/10 bg-obsidian/60 p-4">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <MetricIcon className="h-4 w-4 text-amber-100" aria-hidden="true" />
                  {metric.label}
                </div>
                <p className="mt-2 text-2xl font-semibold text-white">{metric.value}</p>
              </div>
            );
          })}
        </div>

        <section className="min-w-0">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">Story Clusters</h2>
            <span className="text-xs uppercase text-slate-500">Embeddings + pgvector</span>
          </div>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {(stories.length ? stories : storyStats?.top_stories ?? []).slice(0, 8).map((story) => (
              <div key={story.id} className="border border-white/10 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-white">{story.title}</h3>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                      {story.summary ?? "No story summary"}
                    </p>
                  </div>
                  <span className="shrink-0 text-sm font-semibold text-amber-100">
                    {story.risk_score}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {story.keywords.slice(0, 5).map((keyword) => (
                    <span key={keyword} className="border border-white/10 px-2 py-1 text-xs text-slate-300">
                      {keyword}
                    </span>
                  ))}
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                  <span>{story.item_count} items</span>
                  <span>{story.entity_count} entities</span>
                  <span>{story.severity ?? "unknown"}</span>
                  <span>{formatDate(story.last_seen_at)}</span>
                </div>
              </div>
            ))}
            {(stories.length === 0 && (storyStats?.top_stories.length ?? 0) === 0) ? (
              <p className="border border-white/10 p-4 text-sm text-slate-400">
                Run Sync Stories after syncing cyber intelligence
              </p>
            ) : null}
          </div>
        </section>
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
                <button
                  type="button"
                  onClick={() => void enrichBatch()}
                  disabled={batchEnriching}
                  className="inline-flex h-10 items-center gap-2 border border-ice/30 bg-ice/10 px-3 text-sm font-semibold text-ice transition hover:border-ice hover:bg-ice/15 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  {batchEnriching ? "Enriching" : "Enrich 10"}
                </button>
                <button
                  type="button"
                  onClick={() => void syncIntelligence()}
                  disabled={syncingIntelligence}
                  className="inline-flex h-10 items-center gap-2 border border-fuchsia-300/30 bg-fuchsia-300/10 px-3 text-sm font-semibold text-fuchsia-200 transition hover:border-fuchsia-200 hover:bg-fuchsia-300/15 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Radar className="h-4 w-4" aria-hidden="true" />
                  {syncingIntelligence ? "Syncing" : "Sync Intel"}
                </button>
                <button
                  type="button"
                  onClick={() => void syncStories()}
                  disabled={syncingStories}
                  className="inline-flex h-10 items-center gap-2 border border-amber-200/30 bg-amber-200/10 px-3 text-sm font-semibold text-amber-100 transition hover:border-amber-100 hover:bg-amber-200/15 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <GitBranch className="h-4 w-4" aria-hidden="true" />
                  {syncingStories ? "Clustering" : "Sync Stories"}
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

          {lastEnrichment ? (
            <div className="grid gap-3 border-b border-white/10 p-4 text-sm text-slate-300 sm:grid-cols-5">
              <span>Status {lastEnrichment.status}</span>
              <span>Candidates {lastEnrichment.candidates}</span>
              <span>Enriched {lastEnrichment.enriched}</span>
              <span>Failed {lastEnrichment.failed}</span>
              <span>Skipped {lastEnrichment.skipped}</span>
            </div>
          ) : null}

          {lastIntelligenceSync ? (
            <div className="grid gap-3 border-b border-white/10 p-4 text-sm text-slate-300 sm:grid-cols-5">
              <span>Status {lastIntelligenceSync.status}</span>
              <span>Checked {lastIntelligenceSync.enrichments_checked}</span>
              <span>Created {lastIntelligenceSync.entities_created}</span>
              <span>Deleted {lastIntelligenceSync.entities_deleted}</span>
              <span>Skipped {lastIntelligenceSync.skipped}</span>
            </div>
          ) : null}

          {lastStorySync ? (
            <div className="grid gap-3 border-b border-white/10 p-4 text-sm text-slate-300 sm:grid-cols-5">
              <span>Status {lastStorySync.status}</span>
              <span>Candidates {lastStorySync.candidates}</span>
              <span>Stories {lastStorySync.stories_created}</span>
              <span>Linked Items {lastStorySync.story_items_created}</span>
              <span>Deleted {lastStorySync.stories_deleted}</span>
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
                    {item.ai_severity ? (
                      <span className="border border-signal/30 px-2 py-1 text-xs uppercase text-signal">
                        {item.ai_severity}
                      </span>
                    ) : null}
                  </div>

                  <p className="line-clamp-2 text-sm leading-6 text-slate-400">
                    {item.ai_summary ?? item.normalized_content ?? item.summary ?? "No content"}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                    <span>{item.source_name ?? "Unknown source"}</span>
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                      {formatDate(item.published_at ?? item.collected_at)}
                    </span>
                    <span>{compactHash(item.normalized_hash ?? item.content_hash)}</span>
                    {item.ai_confidence !== null ? <span>AI {item.ai_confidence}%</span> : null}
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

              <button
                type="button"
                onClick={() => void enrichSelectedItem()}
                disabled={enriching || selectedItem.status !== "normalized" || selectedItem.is_duplicate}
                className="inline-flex h-10 items-center justify-center gap-2 border border-ice/30 bg-ice/10 px-3 text-sm font-semibold text-ice transition hover:border-ice hover:bg-ice/15 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Sparkles className="h-4 w-4" aria-hidden="true" />
                {enriching ? "Enriching" : selectedItem.ai_summary ? "Refresh AI Enrichment" : "Enrich Item"}
              </button>

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
                <span className="border border-white/10 p-3">
                  AI Enriched
                  <strong className="mt-1 block font-semibold text-white">
                    {formatDate(selectedItem.enriched_at)}
                  </strong>
                </span>
              </div>

              {selectedItem.ai_summary ? (
                <div className="grid gap-3 border border-ice/20 bg-ice/5 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Sparkles className="h-4 w-4 text-ice" aria-hidden="true" />
                    <span className="text-sm font-semibold text-white">AI Enrichment</span>
                    {selectedItem.ai_severity ? (
                      <span className="border border-signal/30 px-2 py-1 text-xs uppercase text-signal">
                        {selectedItem.ai_severity}
                      </span>
                    ) : null}
                    {selectedItem.ai_confidence !== null ? (
                      <span className="text-xs text-slate-400">
                        Confidence {selectedItem.ai_confidence}%
                      </span>
                    ) : null}
                  </div>
                  <p className="text-sm leading-6 text-slate-300">{selectedItem.ai_summary}</p>
                  {selectedItem.ai_tags?.length ? (
                    <div className="flex flex-wrap gap-2">
                      {selectedItem.ai_tags.map((tag) => (
                        <span key={tag} className="border border-white/10 px-2 py-1 text-xs text-slate-300">
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  {selectedItem.ai_cves?.length ? (
                    <p className="text-xs text-slate-400">
                      CVEs {selectedItem.ai_cves.join(", ")}
                    </p>
                  ) : null}
                  {selectedItem.ai_iocs?.length ? (
                    <p className="text-xs text-slate-400">
                      IOCs {selectedItem.ai_iocs.join(", ")}
                    </p>
                  ) : null}
                  {selectedItem.ai_mitre_attack?.length ? (
                    <p className="text-xs text-slate-400">
                      MITRE {selectedItem.ai_mitre_attack.join(", ")}
                    </p>
                  ) : null}
                  {selectedItem.ai_recommended_actions?.length ? (
                    <ul className="grid gap-2 text-sm text-slate-300">
                      {selectedItem.ai_recommended_actions.map((action) => (
                        <li key={action}>- {action}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ) : null}

              {selectedCyberEntities.length ? (
                <div className="grid gap-3 border border-fuchsia-300/20 bg-fuchsia-300/5 p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <Radar className="h-4 w-4 text-fuchsia-200" aria-hidden="true" />
                    Cyber Entities
                  </div>
                  <div className="grid gap-2">
                    {selectedCyberEntities.slice(0, 12).map((entity) => (
                      <div
                        key={entity.id}
                        className="grid grid-cols-[1fr_44px] gap-3 border border-white/10 p-2"
                      >
                        <span className="min-w-0">
                          <span className="block truncate text-sm text-slate-200">
                            {entity.normalized_value}
                          </span>
                          <span className="text-xs uppercase text-slate-500">
                            {entity.entity_type} {entity.severity ?? "unknown"}
                          </span>
                        </span>
                        <span className="text-right text-sm font-semibold text-fuchsia-200">
                          {entity.risk_score}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

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
