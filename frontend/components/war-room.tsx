"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Clock,
  DatabaseZap,
  Flame,
  RadioTower,
  RefreshCw,
  ShieldAlert,
  Signal,
  Siren,
  Waypoints
} from "lucide-react";

type WarRoomSummary = {
  active_stories: number;
  critical_stories: number;
  high_risk_entities: number;
  enriched_items: number;
  fresh_items_24h: number;
  stale_sources: number;
  max_story_risk_score: number;
  operation_mode: string;
};

type WarRoomRiskStory = {
  id: string;
  title: string;
  summary: string | null;
  severity: string | null;
  risk_score: number;
  item_count: number;
  entity_count: number;
  keywords: string[];
  first_seen_at: string | null;
  last_seen_at: string | null;
  urgency: string;
};

type WarRoomEntityPulse = {
  entity_type: string;
  normalized_value: string;
  occurrences: number;
  max_risk_score: number;
  severity: string | null;
  last_seen_at: string | null;
};

type WarRoomTimelineEvent = {
  event_type: string;
  title: string;
  description: string | null;
  severity: string | null;
  risk_score: number | null;
  occurred_at: string | null;
  story_id: string | null;
  item_id: string | null;
  source_name: string | null;
};

type WarRoomSourceHealth = {
  id: string;
  name: string;
  source_type: string;
  is_enabled: boolean;
  status: string;
  last_fetched_at: string | null;
  error_count: number;
  last_error: string | null;
};

type WarRoomSnapshot = {
  summary: WarRoomSummary;
  risk_queue: WarRoomRiskStory[];
  entity_pulse: WarRoomEntityPulse[];
  timeline: WarRoomTimelineEvent[];
  source_health: WarRoomSourceHealth[];
};

type WarRoomProps = {
  onNavigate?: (view: "command" | "intelligence" | "sources") => void;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiRequest<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`);

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? "Request failed");
  }

  return response.json() as Promise<T>;
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Unknown";
}

function modeTone(mode: string) {
  if (mode === "hot") {
    return "border-red-300/40 bg-red-500/10 text-red-100";
  }

  if (mode === "active") {
    return "border-amber-200/40 bg-amber-200/10 text-amber-100";
  }

  return "border-emerald-300/30 bg-emerald-300/10 text-emerald-100";
}

function healthTone(status: string) {
  if (status === "healthy") {
    return "text-emerald-200";
  }

  if (status === "disabled") {
    return "text-slate-500";
  }

  if (status === "degraded") {
    return "text-red-200";
  }

  return "text-amber-100";
}

export function WarRoom({ onNavigate }: WarRoomProps) {
  const [snapshot, setSnapshot] = useState<WarRoomSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadWarRoom() {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<WarRoomSnapshot>("/war-room?limit=10");
      setSnapshot(data);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load War Room");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadWarRoom();
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  const summary = snapshot?.summary;

  return (
    <section className="grid gap-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase text-signal">Cyber War Room</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Operational Command View</h2>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`inline-flex h-10 items-center gap-2 border px-3 text-sm font-semibold uppercase ${modeTone(
              summary?.operation_mode ?? "watch"
            )}`}
          >
            <Siren className="h-4 w-4" aria-hidden="true" />
            {summary?.operation_mode ?? "loading"}
          </span>
          <button
            type="button"
            onClick={() => void loadWarRoom()}
            disabled={loading}
            className="inline-flex h-10 items-center gap-2 border border-white/10 px-3 text-sm font-semibold text-slate-200 transition hover:border-signal/50 hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => onNavigate?.("intelligence")}
            className="inline-flex h-10 items-center gap-2 border border-ice/30 bg-ice/10 px-3 text-sm font-semibold text-ice transition hover:border-ice hover:bg-ice/15"
          >
            Investigate
          </button>
        </div>
      </div>

      {error ? <div className="border border-red-400/30 p-3 text-sm text-red-200">{error}</div> : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-7">
        {[
          { label: "Active Stories", value: summary?.active_stories ?? 0, icon: Waypoints },
          { label: "Critical Stories", value: summary?.critical_stories ?? 0, icon: Flame },
          { label: "High Risk Entities", value: summary?.high_risk_entities ?? 0, icon: ShieldAlert },
          { label: "Enriched Items", value: summary?.enriched_items ?? 0, icon: DatabaseZap },
          { label: "Fresh 24h", value: summary?.fresh_items_24h ?? 0, icon: Clock },
          { label: "Stale Sources", value: summary?.stale_sources ?? 0, icon: RadioTower },
          { label: "Max Risk", value: summary?.max_story_risk_score ?? 0, icon: Activity }
        ].map((metric) => {
          const MetricIcon = metric.icon;

          return (
            <div key={metric.label} className="border border-white/10 bg-obsidian/60 p-4">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <MetricIcon className="h-4 w-4 text-signal" aria-hidden="true" />
                {metric.label}
              </div>
              <p className="mt-2 text-2xl font-semibold text-white">{metric.value}</p>
            </div>
          );
        })}
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <section className="min-w-0 border border-white/10 bg-white/[0.025] p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-lg font-semibold text-white">Risk Queue</h3>
            <span className="text-xs uppercase text-slate-500">Stories</span>
          </div>
          <div className="mt-4 grid gap-3">
            {snapshot?.risk_queue.map((story) => (
              <article key={story.id} className="grid gap-3 border border-white/10 bg-obsidian/50 p-3">
                <div className="grid gap-3 sm:grid-cols-[1fr_72px]">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="truncate text-sm font-semibold text-white">{story.title}</h4>
                      <span className="border border-white/10 px-2 py-1 text-xs uppercase text-slate-300">
                        {story.urgency}
                      </span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                      {story.summary ?? "No story summary"}
                    </p>
                  </div>
                  <div className="text-left sm:text-right">
                    <p className="text-2xl font-semibold text-amber-100">{story.risk_score}</p>
                    <p className="text-xs uppercase text-slate-500">{story.severity ?? "unknown"}</p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                  <span>{story.item_count} items</span>
                  <span>{story.entity_count} entities</span>
                  <span>{formatDate(story.last_seen_at)}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {story.keywords.slice(0, 6).map((keyword) => (
                    <span key={keyword} className="border border-white/10 px-2 py-1 text-xs text-slate-300">
                      {keyword}
                    </span>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => onNavigate?.("intelligence")}
                  className="inline-flex h-9 w-fit items-center border border-white/10 px-3 text-xs font-semibold uppercase text-slate-300 transition hover:border-ice/40 hover:text-ice"
                >
                  Open in Intelligence
                </button>
              </article>
            ))}
            {snapshot && snapshot.risk_queue.length === 0 ? (
              <p className="border border-white/10 p-3 text-sm text-slate-400">No active stories</p>
            ) : null}
          </div>
        </section>

        <div className="grid gap-5">
          <section className="border border-white/10 bg-white/[0.025] p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-white">Entity Pulse</h3>
              <span className="text-xs uppercase text-slate-500">Top signals</span>
            </div>
            <div className="mt-4 grid gap-2">
              {snapshot?.entity_pulse.slice(0, 7).map((entity) => (
                <button
                  key={`${entity.entity_type}-${entity.normalized_value}`}
                  type="button"
                  onClick={() => onNavigate?.("intelligence")}
                  className="grid grid-cols-[1fr_64px] gap-3 border border-white/10 p-3 text-left transition hover:border-fuchsia-200/40"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold text-slate-200">
                      {entity.normalized_value}
                    </span>
                    <span className="text-xs uppercase text-slate-500">
                      {entity.entity_type} {entity.severity ?? "unknown"} - {entity.occurrences} hits
                    </span>
                  </span>
                  <span className="text-right text-sm font-semibold text-fuchsia-200">
                    {entity.max_risk_score}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="border border-white/10 bg-white/[0.025] p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-white">Source Health</h3>
              <Signal className="h-4 w-4 text-signal" aria-hidden="true" />
            </div>
            <div className="mt-4 grid gap-2">
              {snapshot?.source_health.slice(0, 6).map((source) => (
                <button
                  key={source.id}
                  type="button"
                  onClick={() => onNavigate?.("sources")}
                  className="grid grid-cols-[1fr_88px] gap-3 border border-white/10 p-3 text-left transition hover:border-signal/40"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold text-slate-200">
                      {source.name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatDate(source.last_fetched_at)}
                    </span>
                  </span>
                  <span className={`text-right text-xs font-semibold uppercase ${healthTone(source.status)}`}>
                    {source.status}
                  </span>
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>

      <section className="border border-white/10 bg-white/[0.025] p-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-white">Operational Timeline</h3>
          <span className="text-xs uppercase text-slate-500">Recent activity</span>
        </div>
        <div className="mt-4 grid gap-2 lg:grid-cols-2">
          {snapshot?.timeline.slice(0, 8).map((event) => (
            <div
              key={`${event.event_type}-${event.story_id ?? event.item_id}-${event.occurred_at}`}
              className="grid gap-2 border border-white/10 p-3"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="border border-white/10 px-2 py-1 text-xs uppercase text-slate-400">
                  {event.event_type}
                </span>
                {event.risk_score !== null ? (
                  <span className="text-xs font-semibold text-amber-100">Risk {event.risk_score}</span>
                ) : null}
                {event.severity ? <span className="text-xs uppercase text-signal">{event.severity}</span> : null}
              </div>
              <p className="truncate text-sm font-semibold text-white">{event.title}</p>
              <p className="line-clamp-2 text-sm leading-6 text-slate-400">
                {event.description ?? event.source_name ?? "No event description"}
              </p>
              <span className="text-xs text-slate-500">{formatDate(event.occurred_at)}</span>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
