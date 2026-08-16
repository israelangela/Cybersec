"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Database,
  ExternalLink,
  Eye,
  Fingerprint,
  GitBranch,
  Link2,
  Newspaper,
  RadioTower,
  RefreshCw,
  Search,
  ShieldCheck,
  Waypoints
} from "lucide-react";

import { SourceManagement } from "@/components/source-management";
import { WarRoom } from "@/components/war-room";

type ConsoleView = "war-room" | "stories" | "entities" | "news" | "sources";

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
  created_at: string;
  updated_at: string;
};

type StoryDetail = Story & {
  items: Array<{
    item_id: string;
    relevance_score: number;
    created_at: string;
    item: Item | null;
  }>;
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

type EntityContext = {
  entity: CyberEntityAggregate;
  items: Item[];
  stories: Story[];
  external_references: Array<{ label: string; url: string }>;
};

type ItemContext = {
  item: Item;
  entities: CyberEntity[];
  stories: Story[];
};

type Selection = {
  storyId: string | null;
  itemId: string | null;
  entity: { entity_type: string; value: string } | null;
};

const navigation = [
  { id: "war-room" as const, label: "War Room", icon: Waypoints },
  { id: "stories" as const, label: "Stories", icon: GitBranch },
  { id: "entities" as const, label: "Entities", icon: Fingerprint },
  { id: "news" as const, label: "News Feed", icon: Newspaper },
  { id: "sources" as const, label: "Sources", icon: RadioTower }
];
const entityTypes = ["all", "cve", "ioc", "mitre_attack", "threat_actor", "tag"];
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

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Unknown";
}

function entityExternalUrl(entityType: string, value: string) {
  if (entityType === "cve" && value.toUpperCase().startsWith("CVE-")) {
    return `https://nvd.nist.gov/vuln/detail/${value.toUpperCase()}`;
  }

  if (entityType === "mitre_attack" && /^T\d{4}(?:\.\d{3})?$/i.test(value)) {
    return `https://attack.mitre.org/techniques/${value.toUpperCase().replace(".", "/")}/`;
  }

  return null;
}

function riskTone(score: number) {
  if (score >= 85) {
    return "text-red-200";
  }

  if (score >= 70) {
    return "text-amber-100";
  }

  if (score >= 45) {
    return "text-ice";
  }

  return "text-slate-300";
}

function itemEntities(item: Item) {
  return [
    ...(item.ai_cves ?? []).map((value) => ({ entityType: "cve", value })),
    ...(item.ai_iocs ?? []).map((value) => ({ entityType: "ioc", value })),
    ...(item.ai_mitre_attack ?? []).map((value) => ({
      entityType: "mitre_attack",
      value: /^T\d{4}(?:\.\d{3})?/i.exec(value)?.[0] ?? value
    })),
    ...(item.ai_tags ?? []).map((value) => ({ entityType: "tag", value }))
  ];
}

function EntityPill({
  entityType,
  value,
  onOpen
}: {
  entityType: string;
  value: string;
  onOpen: (entityType: string, value: string) => void;
}) {
  const externalUrl = entityExternalUrl(entityType, value);

  return (
    <span className="inline-flex items-center gap-1 border border-white/10 bg-white/[0.03] text-xs text-slate-300">
      <button
        type="button"
        onClick={() => onOpen(entityType, value)}
        className="px-2 py-1 transition hover:text-ice"
      >
        {value}
      </button>
      {externalUrl ? (
        <a
          href={externalUrl}
          target="_blank"
          rel="noreferrer"
          className="border-l border-white/10 px-2 py-1 text-slate-500 transition hover:text-ice"
          aria-label={`Open external reference for ${value}`}
        >
          <ExternalLink className="h-3 w-3" aria-hidden="true" />
        </a>
      ) : null}
    </span>
  );
}

type CybersecConsoleProps = {
  status: string;
};

export function CybersecConsole({ status }: CybersecConsoleProps) {
  const [activeView, setActiveView] = useState<ConsoleView>("war-room");
  const [selection, setSelection] = useState<Selection>({
    storyId: null,
    itemId: null,
    entity: null
  });

  const activeNav = useMemo(
    () => navigation.find((item) => item.id === activeView) ?? navigation[0],
    [activeView]
  );

  function openStory(storyId: string) {
    setSelection((current) => ({ ...current, storyId }));
    setActiveView("stories");
  }

  function openItem(itemId: string) {
    setSelection((current) => ({ ...current, itemId }));
    setActiveView("news");
  }

  function openEntity(entityType: string, value: string) {
    setSelection((current) => ({ ...current, entity: { entity_type: entityType, value } }));
    setActiveView("entities");
  }

  return (
    <main className="min-h-screen overflow-hidden">
      <div className="fixed inset-0 -z-10 bg-obsidian">
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(0deg,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:56px_56px]" />
        <div className="absolute inset-0 bg-[linear-gradient(135deg,#07080d_0%,#10131b_48%,#07110e_100%)]" />
        <div className="absolute left-0 top-0 h-full w-1/2 bg-[linear-gradient(115deg,rgba(34,197,94,0.08),transparent_55%)]" />
      </div>

      <section className="mx-auto grid min-h-screen w-full max-w-[1680px] lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-white/10 bg-black/30 p-5 backdrop-blur-xl lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center border border-signal/40 bg-signal/10 text-signal shadow-glow">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase text-slate-200">CyberSec</p>
              <p className="mt-1 text-xs uppercase text-slate-500">CTI Console</p>
            </div>
          </div>

          <div className="mt-6 grid gap-2 border border-white/10 bg-white/[0.035] p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs uppercase text-slate-500">System</span>
              <span className="inline-flex items-center gap-2 text-sm font-semibold text-signal">
                <span className="h-2 w-2 bg-signal" aria-hidden="true" />
                {status}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs text-slate-400">
              {[
                { label: "API", icon: Activity },
                { label: "DB", icon: Database },
                { label: "UI", icon: Eye }
              ].map((item) => (
                <div key={item.label} className="border border-white/10 bg-obsidian/70 p-2">
                  <item.icon className="mb-2 h-4 w-4 text-signal" aria-hidden="true" />
                  {item.label}
                </div>
              ))}
            </div>
          </div>

          <nav className="mt-6 grid gap-2">
            {navigation.map((item) => {
              const NavIcon = item.icon;
              const isActive = activeView === item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveView(item.id)}
                  className={
                    isActive
                      ? "grid grid-cols-[40px_1fr] items-center gap-3 border border-signal/40 bg-signal/10 p-3 text-left text-white"
                      : "grid grid-cols-[40px_1fr] items-center gap-3 border border-white/10 bg-white/[0.025] p-3 text-left text-slate-300 transition hover:border-signal/40 hover:bg-signal/5 hover:text-white"
                  }
                >
                  <span className="flex h-10 w-10 items-center justify-center border border-white/10 bg-obsidian/80">
                    <NavIcon className="h-4 w-4 text-signal" aria-hidden="true" />
                  </span>
                  <span className="min-w-0 text-sm font-semibold">{item.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="mt-6 hidden border border-white/10 bg-white/[0.025] p-4 lg:block">
            <Link2 className="h-5 w-5 text-ice" aria-hidden="true" />
            <p className="mt-3 text-sm font-semibold text-white">Signal Chain</p>
            <div className="mt-3 grid gap-2 text-xs uppercase text-slate-500">
              <span>Source</span>
              <span>News</span>
              <span>Entity</span>
              <span>Story</span>
              <span>Risk</span>
            </div>
          </div>
        </aside>

        <section className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
          <header className="mb-5 grid gap-4 border border-white/10 bg-black/20 p-5 backdrop-blur-xl lg:grid-cols-[1fr_auto]">
            <div>
              <p className="text-sm font-semibold uppercase text-signal">CyberSec</p>
              <h1 className="mt-2 text-3xl font-semibold leading-tight text-white sm:text-4xl">
                {activeNav.label}
              </h1>
            </div>

            <div className="flex flex-wrap items-end gap-2">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveView(item.id)}
                  className={
                    activeView === item.id
                      ? "h-10 border border-signal/40 bg-signal px-3 text-sm font-semibold text-obsidian"
                      : "h-10 border border-white/10 bg-white/[0.03] px-3 text-sm font-semibold text-slate-300 transition hover:border-signal/40 hover:text-white"
                  }
                >
                  {item.label}
                </button>
              ))}
            </div>
          </header>

          {activeView === "war-room" ? (
            <WarRoom
              onNavigate={(view) => {
                if (view === "command") {
                  setActiveView("war-room");
                  return;
                }

                if (view === "intelligence") {
                  setActiveView("news");
                  return;
                }

                setActiveView("sources");
              }}
              onOpenStory={openStory}
              onOpenEntity={openEntity}
              onOpenItem={openItem}
            />
          ) : null}

          {activeView === "stories" ? (
            <StoriesView
              selectedStoryId={selection.storyId}
              onOpenStory={openStory}
              onOpenItem={openItem}
              onOpenEntity={openEntity}
            />
          ) : null}

          {activeView === "entities" ? (
            <EntitiesView
              selectedEntity={selection.entity}
              onOpenEntity={openEntity}
              onOpenStory={openStory}
              onOpenItem={openItem}
            />
          ) : null}

          {activeView === "news" ? (
            <NewsFeedView
              selectedItemId={selection.itemId}
              onOpenItem={openItem}
              onOpenStory={openStory}
              onOpenEntity={openEntity}
            />
          ) : null}

          {activeView === "sources" ? <SourceManagement /> : null}
        </section>
      </section>
    </main>
  );
}

function StoriesView({
  selectedStoryId,
  onOpenStory,
  onOpenItem,
  onOpenEntity
}: {
  selectedStoryId: string | null;
  onOpenStory: (storyId: string) => void;
  onOpenItem: (itemId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  const [stories, setStories] = useState<Story[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(selectedStoryId);
  const [detail, setDetail] = useState<StoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadStories() {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<Story[]>("/stories?limit=100");
      setStories(data);
      setSelectedId((current) => current ?? selectedStoryId ?? data[0]?.id ?? null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load stories");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadStories();
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (selectedStoryId) {
        setSelectedId(selectedStoryId);
      }
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedStoryId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (!selectedId) {
        setDetail(null);
        return;
      }

      apiRequest<StoryDetail>(`/stories/${selectedId}`)
        .then(setDetail)
        .catch((loadError: unknown) => {
          setError(loadError instanceof Error ? loadError.message : "Unable to load story");
        });
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedId]);

  function selectStory(storyId: string) {
    setSelectedId(storyId);
    onOpenStory(storyId);
  }

  return (
    <section className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
      <div className="border border-white/10 bg-white/[0.035]">
        <div className="flex items-center justify-between gap-3 border-b border-white/10 p-4">
          <h2 className="text-lg font-semibold text-white">Active Stories</h2>
          <button
            type="button"
            onClick={() => void loadStories()}
            className="inline-flex h-9 w-9 items-center justify-center border border-white/10 text-slate-300 transition hover:border-signal/40 hover:text-signal"
            aria-label="Refresh stories"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        {error ? <p className="border-b border-white/10 p-3 text-sm text-red-300">{error}</p> : null}
        <div className="max-h-[calc(100vh-220px)] overflow-auto divide-y divide-white/10">
          {loading ? <p className="p-4 text-sm text-slate-400">Loading stories</p> : null}
          {stories.map((story) => (
            <button
              key={story.id}
              type="button"
              onClick={() => selectStory(story.id)}
              className={
                selectedId === story.id
                  ? "grid w-full gap-2 bg-signal/10 p-4 text-left"
                  : "grid w-full gap-2 p-4 text-left transition hover:bg-white/[0.04]"
              }
            >
              <div className="flex items-start justify-between gap-3">
                <span className="min-w-0 truncate text-sm font-semibold text-white">
                  {story.title}
                </span>
                <span className={`text-sm font-semibold ${riskTone(story.risk_score)}`}>
                  {story.risk_score}
                </span>
              </div>
              <p className="line-clamp-2 text-sm leading-6 text-slate-400">
                {story.summary ?? "No summary"}
              </p>
              <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                <span>{story.item_count} news</span>
                <span>{story.entity_count} entities</span>
                <span>{story.severity ?? "unknown"}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <StoryDetailPanel detail={detail} onOpenItem={onOpenItem} onOpenEntity={onOpenEntity} />
    </section>
  );
}

function StoryDetailPanel({
  detail,
  onOpenItem,
  onOpenEntity
}: {
  detail: StoryDetail | null;
  onOpenItem: (itemId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  if (!detail) {
    return (
      <section className="border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">
        Select a story
      </section>
    );
  }

  const relatedEntities = new Map<string, { entityType: string; value: string }>();
  const sourceNames = new Set<string>();

  for (const storyItem of detail.items) {
    const item = storyItem.item;

    if (!item) {
      continue;
    }

    if (item.source_name) {
      sourceNames.add(item.source_name);
    }

    for (const entity of itemEntities(item)) {
      relatedEntities.set(`${entity.entityType}:${entity.value}`, entity);
    }
  }

  return (
    <section className="grid gap-5 border border-white/10 bg-white/[0.035] p-5">
      <div className="grid gap-4 lg:grid-cols-[1fr_120px]">
        <div>
          <p className="text-xs uppercase text-signal">Story</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{detail.title}</h2>
          <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-300">
            {detail.summary ?? "No story summary"}
          </p>
        </div>
        <div className="border border-white/10 bg-obsidian/60 p-4 text-right">
          <p className={`text-3xl font-semibold ${riskTone(detail.risk_score)}`}>
            {detail.risk_score}
          </p>
          <p className="mt-1 text-xs uppercase text-slate-500">{detail.severity ?? "unknown"}</p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        {[
          ["News", detail.item_count],
          ["Entities", detail.entity_count],
          ["Sources", sourceNames.size],
          ["Last Seen", formatDate(detail.last_seen_at)]
        ].map(([label, value]) => (
          <div key={label} className="border border-white/10 bg-obsidian/50 p-3">
            <p className="text-xs uppercase text-slate-500">{label}</p>
            <p className="mt-2 truncate text-sm font-semibold text-white">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-2">
        <h3 className="text-sm font-semibold text-white">Related Entities</h3>
        <div className="flex flex-wrap gap-2">
          {[...relatedEntities.values()].slice(0, 24).map((entity) => (
            <EntityPill
              key={`${entity.entityType}-${entity.value}`}
              entityType={entity.entityType}
              value={entity.value}
              onOpen={onOpenEntity}
            />
          ))}
        </div>
      </div>

      <section className="grid gap-3">
        <h3 className="text-sm font-semibold text-white">Exact News</h3>
        <div className="grid gap-2">
          {detail.items.map((storyItem) => {
            const item = storyItem.item;

            if (!item) {
              return null;
            }

            return (
              <article
                key={storyItem.item_id}
                className="grid gap-3 border border-white/10 bg-obsidian/40 p-3 lg:grid-cols-[1fr_auto]"
              >
                <button
                  type="button"
                  onClick={() => onOpenItem(item.id)}
                  className="min-w-0 text-left"
                >
                  <p className="truncate text-sm font-semibold text-white">
                    {item.normalized_title ?? item.title}
                  </p>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                    {item.ai_summary ?? item.summary ?? item.normalized_content ?? "No content"}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                    <span>{item.source_name ?? "Unknown source"}</span>
                    <span>{formatDate(item.published_at ?? item.collected_at)}</span>
                    <span>Relevance {storyItem.relevance_score}</span>
                  </div>
                </button>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-9 items-center gap-2 border border-white/10 px-3 text-sm text-slate-300 transition hover:border-ice/40 hover:text-ice"
                >
                  <ExternalLink className="h-4 w-4" aria-hidden="true" />
                  Original
                </a>
              </article>
            );
          })}
        </div>
      </section>
    </section>
  );
}

function EntitiesView({
  selectedEntity,
  onOpenEntity,
  onOpenStory,
  onOpenItem
}: {
  selectedEntity: Selection["entity"];
  onOpenEntity: (entityType: string, value: string) => void;
  onOpenStory: (storyId: string) => void;
  onOpenItem: (itemId: string) => void;
}) {
  const [entities, setEntities] = useState<CyberEntityAggregate[]>([]);
  const [entityType, setEntityType] = useState("all");
  const [search, setSearch] = useState("");
  const [context, setContext] = useState<EntityContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadEntities() {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ limit: "100", min_score: "1" });

      if (entityType !== "all") {
        params.set("entity_type", entityType);
      }

      if (search.trim().length >= 2) {
        params.set("search", search.trim());
      }

      const data = await apiRequest<CyberEntityAggregate[]>(
        `/intelligence/entities?${params.toString()}`
      );
      setEntities(data);

      if (!selectedEntity && data[0]) {
        onOpenEntity(data[0].entity_type, data[0].normalized_value);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load entities");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadEntities();
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityType]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (!selectedEntity) {
        setContext(null);
        return;
      }

      const params = new URLSearchParams({
        entity_type: selectedEntity.entity_type,
        value: selectedEntity.value,
        limit: "100"
      });
      apiRequest<EntityContext>(`/intelligence/entities/context?${params.toString()}`)
        .then(setContext)
        .catch((loadError: unknown) => {
          setError(loadError instanceof Error ? loadError.message : "Unable to load entity context");
        });
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedEntity]);

  return (
    <section className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
      <div className="border border-white/10 bg-white/[0.035]">
        <div className="grid gap-3 border-b border-white/10 p-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">Entities</h2>
            <button
              type="button"
              onClick={() => void loadEntities()}
              className="inline-flex h-9 w-9 items-center justify-center border border-white/10 text-slate-300 transition hover:border-signal/40 hover:text-signal"
              aria-label="Refresh entities"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
          <div className="grid gap-2 sm:grid-cols-[1fr_150px]">
            <label className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    void loadEntities();
                  }
                }}
                className="h-9 w-full border border-white/10 bg-obsidian py-2 pl-9 pr-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="Search entity"
              />
            </label>
            <select
              value={entityType}
              onChange={(event) => setEntityType(event.target.value)}
              className="h-9 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
            >
              {entityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        </div>
        {error ? <p className="border-b border-white/10 p-3 text-sm text-red-300">{error}</p> : null}
        <div className="max-h-[calc(100vh-260px)] overflow-auto divide-y divide-white/10">
          {loading ? <p className="p-4 text-sm text-slate-400">Loading entities</p> : null}
          {entities.map((entity) => (
            <button
              key={`${entity.entity_type}-${entity.normalized_value}`}
              type="button"
              onClick={() => onOpenEntity(entity.entity_type, entity.normalized_value)}
              className={
                selectedEntity?.entity_type === entity.entity_type &&
                selectedEntity.value === entity.normalized_value
                  ? "grid w-full grid-cols-[1fr_56px] gap-3 bg-signal/10 p-4 text-left"
                  : "grid w-full grid-cols-[1fr_56px] gap-3 p-4 text-left transition hover:bg-white/[0.04]"
              }
            >
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-white">
                  {entity.normalized_value}
                </span>
                <span className="text-xs uppercase text-slate-500">
                  {entity.entity_type} - {entity.occurrences} hits
                </span>
              </span>
              <span className={`text-right text-sm font-semibold ${riskTone(entity.max_risk_score)}`}>
                {entity.max_risk_score}
              </span>
            </button>
          ))}
        </div>
      </div>

      <EntityDetailPanel context={context} onOpenStory={onOpenStory} onOpenItem={onOpenItem} />
    </section>
  );
}

function EntityDetailPanel({
  context,
  onOpenStory,
  onOpenItem
}: {
  context: EntityContext | null;
  onOpenStory: (storyId: string) => void;
  onOpenItem: (itemId: string) => void;
}) {
  if (!context) {
    return (
      <section className="border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">
        Select an entity
      </section>
    );
  }

  return (
    <section className="grid gap-5 border border-white/10 bg-white/[0.035] p-5">
      <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
        <div>
          <p className="text-xs uppercase text-signal">{context.entity.entity_type}</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">
            {context.entity.normalized_value}
          </h2>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
            <span>{context.entity.occurrences} occurrences</span>
            <span>{context.items.length} news</span>
            <span>{context.stories.length} stories</span>
            <span>{formatDate(context.entity.last_seen_at)}</span>
          </div>
        </div>
        <div className="border border-white/10 bg-obsidian/60 p-4 text-right">
          <p className={`text-3xl font-semibold ${riskTone(context.entity.max_risk_score)}`}>
            {context.entity.max_risk_score}
          </p>
          <p className="mt-1 text-xs uppercase text-slate-500">
            {context.entity.severity ?? "unknown"}
          </p>
        </div>
      </div>

      {context.external_references.length ? (
        <div className="flex flex-wrap gap-2">
          {context.external_references.map((reference) => (
            <a
              key={reference.url}
              href={reference.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-9 items-center gap-2 border border-ice/30 bg-ice/10 px-3 text-sm font-semibold text-ice transition hover:border-ice"
            >
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
              {reference.label}
            </a>
          ))}
        </div>
      ) : null}

      <section className="grid gap-3">
        <h3 className="text-sm font-semibold text-white">Related Stories</h3>
        <div className="grid gap-2 md:grid-cols-2">
          {context.stories.map((story) => (
            <button
              key={story.id}
              type="button"
              onClick={() => onOpenStory(story.id)}
              className="grid gap-2 border border-white/10 bg-obsidian/40 p-3 text-left transition hover:border-signal/40"
            >
              <span className="truncate text-sm font-semibold text-white">{story.title}</span>
              <span className="text-xs text-slate-500">
                Risk {story.risk_score} - {story.item_count} news
              </span>
            </button>
          ))}
          {context.stories.length === 0 ? (
            <p className="border border-white/10 p-3 text-sm text-slate-400">No related stories</p>
          ) : null}
        </div>
      </section>

      <section className="grid gap-3">
        <h3 className="text-sm font-semibold text-white">Related News</h3>
        <div className="grid gap-2">
          {context.items.map((item) => (
            <article
              key={item.id}
              className="grid gap-3 border border-white/10 bg-obsidian/40 p-3 lg:grid-cols-[1fr_auto]"
            >
              <button type="button" onClick={() => onOpenItem(item.id)} className="min-w-0 text-left">
                <p className="truncate text-sm font-semibold text-white">
                  {item.normalized_title ?? item.title}
                </p>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                  {item.ai_summary ?? item.summary ?? item.normalized_content ?? "No content"}
                </p>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                  <span>{item.source_name ?? "Unknown source"}</span>
                  <span>{formatDate(item.published_at ?? item.collected_at)}</span>
                  <span>{item.ai_severity ?? item.status}</span>
                </div>
              </button>
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-9 items-center gap-2 border border-white/10 px-3 text-sm text-slate-300 transition hover:border-ice/40 hover:text-ice"
              >
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
                Original
              </a>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

function NewsFeedView({
  selectedItemId,
  onOpenItem,
  onOpenStory,
  onOpenEntity
}: {
  selectedItemId: string | null;
  onOpenItem: (itemId: string) => void;
  onOpenStory: (storyId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  const [items, setItems] = useState<Item[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(selectedItemId);
  const [context, setContext] = useState<ItemContext | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadItems() {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ limit: "100" });

      if (search.trim().length >= 2) {
        params.set("search", search.trim());
      }

      const data = await apiRequest<Item[]>(`/items?${params.toString()}`);
      setItems(data);
      setSelectedId((current) => current ?? selectedItemId ?? data[0]?.id ?? null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load news");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadItems();
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (selectedItemId) {
        setSelectedId(selectedItemId);
      }
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedItemId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (!selectedId) {
        setContext(null);
        return;
      }

      apiRequest<ItemContext>(`/items/${selectedId}/context`)
        .then(setContext)
        .catch((loadError: unknown) => {
          setError(loadError instanceof Error ? loadError.message : "Unable to load news context");
        });
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedId]);

  function selectItem(itemId: string) {
    setSelectedId(itemId);
    onOpenItem(itemId);
  }

  return (
    <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_440px]">
      <div className="border border-white/10 bg-white/[0.035]">
        <div className="grid gap-3 border-b border-white/10 p-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">News Feed</h2>
            <button
              type="button"
              onClick={() => void loadItems()}
              className="inline-flex h-9 w-9 items-center justify-center border border-white/10 text-slate-300 transition hover:border-signal/40 hover:text-signal"
              aria-label="Refresh news"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
          <label className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void loadItems();
                }
              }}
              className="h-9 w-full border border-white/10 bg-obsidian py-2 pl-9 pr-3 text-sm text-white outline-none transition focus:border-signal/60"
              placeholder="Search news"
            />
          </label>
        </div>
        {error ? <p className="border-b border-white/10 p-3 text-sm text-red-300">{error}</p> : null}
        <div className="max-h-[calc(100vh-260px)] overflow-auto divide-y divide-white/10">
          {loading ? <p className="p-4 text-sm text-slate-400">Loading news</p> : null}
          {items.map((item) => (
            <article
              key={item.id}
              className={
                selectedId === item.id
                  ? "grid gap-3 bg-signal/10 p-4"
                  : "grid gap-3 p-4 transition hover:bg-white/[0.04]"
              }
            >
              <button type="button" onClick={() => selectItem(item.id)} className="text-left">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="min-w-0 flex-1 truncate text-sm font-semibold text-white">
                    {item.normalized_title ?? item.title}
                  </h3>
                  {item.ai_severity ? (
                    <span className="border border-signal/30 px-2 py-1 text-xs uppercase text-signal">
                      {item.ai_severity}
                    </span>
                  ) : null}
                  <span className="border border-white/10 px-2 py-1 text-xs uppercase text-slate-300">
                    {item.status}
                  </span>
                </div>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                  {item.ai_summary ?? item.summary ?? item.normalized_content ?? "No content"}
                </p>
              </button>
              <div className="flex flex-wrap items-center gap-2">
                {itemEntities(item).slice(0, 8).map((entity) => (
                  <EntityPill
                    key={`${item.id}-${entity.entityType}-${entity.value}`}
                    entityType={entity.entityType}
                    value={entity.value}
                    onOpen={onOpenEntity}
                  />
                ))}
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
                <span>
                  {item.source_name ?? "Unknown source"} -{" "}
                  {formatDate(item.published_at ?? item.collected_at)}
                </span>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-slate-400 transition hover:text-ice"
                >
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                  Original
                </a>
              </div>
            </article>
          ))}
        </div>
      </div>

      <NewsDetailPanel context={context} onOpenStory={onOpenStory} onOpenEntity={onOpenEntity} />
    </section>
  );
}

function NewsDetailPanel({
  context,
  onOpenStory,
  onOpenEntity
}: {
  context: ItemContext | null;
  onOpenStory: (storyId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  if (!context) {
    return (
      <aside className="border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">
        Select a news item
      </aside>
    );
  }

  const item = context.item;

  return (
    <aside className="grid gap-5 border border-white/10 bg-white/[0.045] p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase text-signal">News Context</p>
          <h2 className="mt-2 text-xl font-semibold leading-7 text-white">
            {item.normalized_title ?? item.title}
          </h2>
        </div>
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center border border-white/10 text-slate-300 transition hover:border-ice/50 hover:text-ice"
          aria-label="Open original"
        >
          <ExternalLink className="h-4 w-4" aria-hidden="true" />
        </a>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        {[
          ["Source", item.source_name ?? item.source_id],
          ["Published", formatDate(item.published_at)],
          ["AI Severity", item.ai_severity ?? "unknown"],
          ["AI Confidence", item.ai_confidence !== null ? `${item.ai_confidence}%` : "unknown"]
        ].map(([label, value]) => (
          <div key={label} className="border border-white/10 bg-obsidian/50 p-3">
            <p className="text-xs uppercase text-slate-500">{label}</p>
            <p className="mt-2 truncate font-semibold text-white">{value}</p>
          </div>
        ))}
      </div>

      {context.stories.length ? (
        <section className="grid gap-2">
          <h3 className="text-sm font-semibold text-white">Related Stories</h3>
          {context.stories.map((story) => (
            <button
              key={story.id}
              type="button"
              onClick={() => onOpenStory(story.id)}
              className="grid gap-1 border border-white/10 p-3 text-left transition hover:border-signal/40"
            >
              <span className="truncate text-sm font-semibold text-white">{story.title}</span>
              <span className="text-xs text-slate-500">Risk {story.risk_score}</span>
            </button>
          ))}
        </section>
      ) : null}

      <section className="grid gap-2">
        <h3 className="text-sm font-semibold text-white">Entities</h3>
        <div className="flex flex-wrap gap-2">
          {context.entities.map((entity) => (
            <EntityPill
              key={entity.id}
              entityType={entity.entity_type}
              value={entity.normalized_value}
              onOpen={onOpenEntity}
            />
          ))}
        </div>
      </section>

      {item.ai_recommended_actions?.length ? (
        <section className="grid gap-2">
          <h3 className="text-sm font-semibold text-white">Recommended Actions</h3>
          <ul className="grid gap-2 text-sm text-slate-300">
            {item.ai_recommended_actions.map((action) => (
              <li key={action} className="border border-white/10 p-3">
                {action}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="grid gap-2">
        <h3 className="text-sm font-semibold text-white">Content</h3>
        <p className="max-h-[420px] overflow-auto border border-white/10 bg-obsidian p-4 text-sm leading-6 text-slate-300">
          {item.ai_summary ?? item.normalized_content ?? item.summary ?? item.raw_content ?? "No content"}
        </p>
      </section>
    </aside>
  );
}
