"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bell,
  Bot,
  Building2,
  CheckCircle2,
  Database,
  DollarSign,
  DownloadCloud,
  ExternalLink,
  Eye,
  FileText,
  Fingerprint,
  GitBranch,
  Layers3,
  Link2,
  Newspaper,
  Power,
  PowerOff,
  RadioTower,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Trash2,
  Users,
  Waypoints
} from "lucide-react";

import { SourceManagement } from "@/components/source-management";
import { WarRoom } from "@/components/war-room";

type ConsoleView =
  | "war-room"
  | "ask"
  | "reports"
  | "alerts"
  | "enterprise"
  | "stories"
  | "entities"
  | "news"
  | "sources";

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

type AskCitation = {
  citation_id: string;
  item_id: string;
  story_ids: string[];
  title: string;
  url: string;
  source_name: string | null;
  published_at: string | null;
  collected_at: string;
  score: number;
  excerpt: string;
  entities: string[];
};

type AskResponse = {
  answer: string;
  mode: string;
  confidence: number;
  citations: AskCitation[];
  follow_up_questions: string[];
};

type Report = {
  id: string;
  title: string;
  report_type: string;
  status: string;
  summary: string | null;
  severity: string | null;
  risk_score: number;
  story_count: number;
  item_count: number;
  entity_count: number;
  source_count: number;
  period_start: string | null;
  period_end: string | null;
  filters: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type ReportDetail = Report & {
  body_markdown: string;
  stories: Array<{
    story_id: string;
    position: number;
    story: Story;
  }>;
  items: Array<{
    item_id: string;
    citation_id: string;
    item: Item;
  }>;
};

type Watchlist = {
  id: string;
  name: string;
  description: string | null;
  entity_type: string | null;
  value_pattern: string | null;
  severity: string | null;
  min_risk_score: number;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
};

type Alert = {
  id: string;
  watchlist_id: string;
  item_id: string;
  story_id: string | null;
  title: string;
  description: string | null;
  status: string;
  severity: string | null;
  risk_score: number;
  entity_type: string;
  entity_value: string;
  evidence: Record<string, unknown>;
  matched_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
};

type AlertSyncResult = {
  status: string;
  watchlists_checked: number;
  alerts_created: number;
  skipped: number;
};

type Department = {
  id: string;
  name: string;
  description: string | null;
  owner_email: string | null;
  risk_appetite: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type EnterpriseUser = {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
};

type DepartmentMembership = {
  id: string;
  department_id: string;
  user_id: string;
  role: string;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type EnterpriseRole = {
  role: string;
  permissions: string[];
  description: string;
};

type AuditEvent = {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  outcome: string;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

type ModelUsage = {
  id: string;
  provider: string;
  model: string;
  operation: string;
  resource_type: string;
  resource_id: string;
  enrichment_id: string | null;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: string;
  raw_usage: Record<string, unknown>;
  created_at: string;
};

type EnterpriseOverview = {
  departments: number;
  active_departments: number;
  users: number;
  active_users: number;
  memberships: number;
  audit_events: number;
  model_usage_records: number;
  estimated_cost_usd: string;
  open_alerts: number;
  critical_open_alerts: number;
  recent_audit_events: AuditEvent[];
  recent_model_usage: ModelUsage[];
};

type ModelUsageSyncResult = {
  status: string;
  enrichments_checked: number;
  usage_created: number;
  skipped: number;
};

type Selection = {
  storyId: string | null;
  itemId: string | null;
  entity: { entity_type: string; value: string } | null;
};

type PipelineResult = Record<string, unknown>;

const navigation = [
  { id: "war-room" as const, label: "War Room", icon: Waypoints },
  { id: "ask" as const, label: "Ask", icon: Bot },
  { id: "reports" as const, label: "Reports", icon: FileText },
  { id: "alerts" as const, label: "Alerts", icon: Bell },
  { id: "enterprise" as const, label: "Enterprise", icon: Building2 },
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

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.text();
  return (body ? JSON.parse(body) : undefined) as T;
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

function inferEntityType(value: string) {
  if (value.toUpperCase().startsWith("CVE-")) {
    return "cve";
  }

  if (/^T\d{4}(?:\.\d{3})?$/i.test(value)) {
    return "mitre_attack";
  }

  if (/^(APT|TA|UNC|FIN)\d{1,5}$/i.test(value)) {
    return "threat_actor";
  }

  if (/^(?:[a-z0-9.-]+\.[a-z]{2,}|\d{1,3}(?:\.\d{1,3}){3})$/i.test(value)) {
    return "ioc";
  }

  return "tag";
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

function summarizePipelineResult(result: PipelineResult) {
  return Object.entries(result)
    .filter(([, value]) => typeof value === "string" || typeof value === "number")
    .slice(0, 5)
    .map(([key, value]) => `${key} ${value}`)
    .join(" / ");
}

function PipelineControls() {
  const [runningAction, setRunningAction] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const actions = [
    {
      id: "collect",
      label: "Collect RSS",
      icon: DownloadCloud,
      path: "/collection/run"
    },
    {
      id: "normalize",
      label: "Normalize",
      icon: Layers3,
      path: "/normalization/run?limit=500"
    },
    {
      id: "enrich",
      label: "Enrich Batch",
      icon: Sparkles,
      path: "/enrichment/run?limit=10"
    },
    {
      id: "sync-intel",
      label: "Sync Intel",
      icon: Fingerprint,
      path: "/intelligence/sync?limit=500"
    },
    {
      id: "sync-stories",
      label: "Sync Stories",
      icon: GitBranch,
      path: "/stories/sync?limit=500"
    }
  ];

  async function runPipelineAction(action: (typeof actions)[number]) {
    setRunningAction(action.id);
    setMessage(null);
    setError(null);

    try {
      const result = await apiRequest<PipelineResult>(action.path, { method: "POST" });
      setMessage(`${action.label}: ${summarizePipelineResult(result)}`);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : `Unable to run ${action.label}`);
    } finally {
      setRunningAction(null);
    }
  }

  return (
    <section className="mb-5 border border-white/10 bg-white/[0.035] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase text-signal">Pipeline</p>
          <p className="mt-1 text-sm text-slate-400">Collect, normalize, enrich and rebuild context</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => {
            const ActionIcon = action.icon;
            const isRunning = runningAction === action.id;

            return (
              <button
                key={action.id}
                type="button"
                onClick={() => void runPipelineAction(action)}
                disabled={runningAction !== null}
                className="inline-flex h-10 items-center gap-2 border border-white/10 px-3 text-sm font-semibold text-slate-200 transition hover:border-signal/50 hover:text-signal disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ActionIcon className={isRunning ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
                {isRunning ? "Running" : action.label}
              </button>
            );
          })}
        </div>
      </div>

      {message ? <p className="mt-3 text-sm text-signal">{message}</p> : null}
      {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
    </section>
  );
}

function AskCyberSecView({
  onOpenItem,
  onOpenStory,
  onOpenEntity
}: {
  onOpenItem: (itemId: string) => void;
  onOpenStory: (storyId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  const [question, setQuestion] = useState("Que amenazas recientes requieren prioridad?");
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(questionText = question) {
    const trimmedQuestion = questionText.trim();

    if (trimmedQuestion.length < 3) {
      setError("Write a longer question");
      return;
    }

    setQuestion(trimmedQuestion);
    setLoading(true);
    setError(null);

    try {
      const result = await apiRequest<AskResponse>("/ask", {
        method: "POST",
        body: JSON.stringify({
          question: trimmedQuestion,
          limit: 6,
          use_ai: true
        })
      });
      setResponse(result);
    } catch (askError) {
      setError(askError instanceof Error ? askError.message : "Unable to ask CyberSec");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_460px]">
      <div className="grid gap-5">
        <section className="border border-white/10 bg-white/[0.04] p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center border border-signal/40 bg-signal/10 text-signal">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase text-signal">Ask CyberSec</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">RAG with cited evidence</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Ask over enriched news, entities and stories. Answers stay tied to source citations.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              className="min-h-28 resize-y border border-white/10 bg-obsidian px-4 py-3 text-sm leading-6 text-white outline-none transition placeholder:text-slate-600 focus:border-signal/60"
              placeholder="Ask about a CVE, actor, IOC, story or defensive priority"
            />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                {[
                  "Que CVEs tienen mas riesgo ahora?",
                  "Que fuentes sostienen esta historia?",
                  "Que acciones defensivas recomienda la evidencia?"
                ].map((sample) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => void ask(sample)}
                    className="border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:border-ice/40 hover:text-ice"
                  >
                    {sample}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => void ask()}
                disabled={loading}
                className="inline-flex h-10 items-center gap-2 bg-signal px-4 text-sm font-semibold text-obsidian transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Send className={loading ? "h-4 w-4 animate-pulse" : "h-4 w-4"} aria-hidden="true" />
                {loading ? "Asking" : "Ask"}
              </button>
            </div>
          </div>

          {error ? <p className="mt-4 text-sm text-red-300">{error}</p> : null}
        </section>

        <section className="min-h-72 border border-white/10 bg-white/[0.035] p-5">
          {response ? (
            <div className="grid gap-5">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div>
                  <p className="text-xs uppercase text-slate-500">Mode {response.mode}</p>
                  <h3 className="mt-1 text-xl font-semibold text-white">Answer</h3>
                </div>
                <div className="border border-white/10 bg-obsidian/60 px-3 py-2 text-right">
                  <p className="text-lg font-semibold text-signal">{response.confidence}%</p>
                  <p className="text-xs uppercase text-slate-500">confidence</p>
                </div>
              </div>
              <p className="whitespace-pre-line text-sm leading-7 text-slate-200">{response.answer}</p>
              <div className="flex flex-wrap gap-2">
                {response.follow_up_questions.map((followUp) => (
                  <button
                    key={followUp}
                    type="button"
                    onClick={() => void ask(followUp)}
                    className="border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:border-signal/40 hover:text-signal"
                  >
                    {followUp}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex min-h-60 items-center justify-center text-center text-sm text-slate-400">
              Ask a question to generate a cited cyber intelligence answer.
            </div>
          )}
        </section>
      </div>

      <aside className="border border-white/10 bg-white/[0.04] p-5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-white">Citations</h3>
          <span className="text-xs uppercase text-slate-500">
            {response?.citations.length ?? 0} sources
          </span>
        </div>
        <div className="mt-4 grid gap-3">
          {response?.citations.map((citation) => (
            <article key={citation.citation_id} className="grid gap-3 border border-white/10 p-3">
              <div className="flex items-start justify-between gap-3">
                <button
                  type="button"
                  onClick={() => onOpenItem(citation.item_id)}
                  className="min-w-0 text-left"
                >
                  <span className="text-xs font-semibold text-signal">
                    [{citation.citation_id}] Score {citation.score}
                  </span>
                  <h4 className="mt-1 line-clamp-2 text-sm font-semibold text-white">
                    {citation.title}
                  </h4>
                </button>
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-9 w-9 shrink-0 items-center justify-center border border-white/10 text-slate-300 transition hover:border-ice/40 hover:text-ice"
                  aria-label={`Open original for ${citation.title}`}
                >
                  <ExternalLink className="h-4 w-4" aria-hidden="true" />
                </a>
              </div>
              <p className="text-sm leading-6 text-slate-400">{citation.excerpt}</p>
              <div className="flex flex-wrap gap-2">
                {citation.entities.slice(0, 8).map((entity) => (
                  <EntityPill
                    key={`${citation.citation_id}-${entity}`}
                    entityType={inferEntityType(entity)}
                    value={entity}
                    onOpen={onOpenEntity}
                  />
                ))}
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                <span>
                  {citation.source_name ?? "Unknown source"} -{" "}
                  {formatDate(citation.published_at ?? citation.collected_at)}
                </span>
                {citation.story_ids[0] ? (
                  <button
                    type="button"
                    onClick={() => onOpenStory(citation.story_ids[0])}
                    className="text-slate-300 transition hover:text-signal"
                  >
                    Open Story
                  </button>
                ) : null}
              </div>
            </article>
          ))}
          {response && response.citations.length === 0 ? (
            <p className="border border-white/10 p-3 text-sm text-slate-400">
              No cited evidence found for this question.
            </p>
          ) : null}
        </div>
      </aside>
    </section>
  );
}

function ReportsView({
  onOpenStory,
  onOpenItem
}: {
  onOpenStory: (storyId: string) => void;
  onOpenItem: (itemId: string) => void;
}) {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [title, setTitle] = useState("");
  const [reportType, setReportType] = useState("executive");
  const [minScore, setMinScore] = useState("70");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadReports() {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<Report[]>("/reports?limit=100");
      setReports(data);
      setSelectedReportId((current) => current ?? data[0]?.id ?? null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load reports");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadReports();
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (!selectedReportId) {
        setDetail(null);
        return;
      }

      apiRequest<ReportDetail>(`/reports/${selectedReportId}`)
        .then(setDetail)
        .catch((loadError: unknown) => {
          setError(loadError instanceof Error ? loadError.message : "Unable to load report");
        });
    }, 0);

    return () => window.clearTimeout(timer);
  }, [selectedReportId]);

  async function generateReport() {
    setGenerating(true);
    setError(null);
    setMessage(null);

    try {
      const result = await apiRequest<{ status: string; report: ReportDetail }>("/reports/generate", {
        method: "POST",
        body: JSON.stringify({
          title: title.trim() || null,
          report_type: reportType,
          min_score: minScore ? Number(minScore) : null,
          limit: 6
        })
      });
      setDetail(result.report);
      setSelectedReportId(result.report.id);
      setMessage("Report generated");
      await loadReports();
    } catch (generateError) {
      setError(generateError instanceof Error ? generateError.message : "Unable to generate report");
    } finally {
      setGenerating(false);
    }
  }

  async function deleteReport(reportId: string) {
    setError(null);
    setMessage(null);

    try {
      await apiRequest<void>(`/reports/${reportId}`, { method: "DELETE" });
      setDetail(null);
      setSelectedReportId(null);
      setMessage("Report deleted");
      await loadReports();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete report");
    }
  }

  return (
    <section className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
      <div className="grid gap-5">
        <section className="border border-white/10 bg-white/[0.04] p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center border border-signal/40 bg-signal/10 text-signal">
              <FileText className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-signal">Reports</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Generate Intelligence Report</h2>
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
              placeholder="Optional report title"
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <select
                value={reportType}
                onChange={(event) => setReportType(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                <option value="executive">executive</option>
                <option value="technical">technical</option>
                <option value="daily">daily</option>
              </select>
              <input
                type="number"
                min="1"
                max="100"
                value={minScore}
                onChange={(event) => setMinScore(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="Minimum risk"
              />
            </div>
            <button
              type="button"
              onClick={() => void generateReport()}
              disabled={generating}
              className="inline-flex h-10 items-center justify-center gap-2 bg-signal px-4 text-sm font-semibold text-obsidian transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <FileText className={generating ? "h-4 w-4 animate-pulse" : "h-4 w-4"} aria-hidden="true" />
              {generating ? "Generating" : "Generate Report"}
            </button>
          </div>

          {message ? <p className="mt-3 text-sm text-signal">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
        </section>

        <section className="border border-white/10 bg-white/[0.035]">
          <div className="flex items-center justify-between gap-3 border-b border-white/10 p-4">
            <h3 className="text-lg font-semibold text-white">Saved Reports</h3>
            <button
              type="button"
              onClick={() => void loadReports()}
              className="inline-flex h-9 w-9 items-center justify-center border border-white/10 text-slate-300 transition hover:border-signal/40 hover:text-signal"
              aria-label="Refresh reports"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
          <div className="max-h-[calc(100vh-420px)] overflow-auto divide-y divide-white/10">
            {loading ? <p className="p-4 text-sm text-slate-400">Loading reports</p> : null}
            {reports.map((report) => (
              <button
                key={report.id}
                type="button"
                onClick={() => setSelectedReportId(report.id)}
                className={
                  selectedReportId === report.id
                    ? "grid w-full gap-2 bg-signal/10 p-4 text-left"
                    : "grid w-full gap-2 p-4 text-left transition hover:bg-white/[0.04]"
                }
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="min-w-0 truncate text-sm font-semibold text-white">
                    {report.title}
                  </span>
                  <span className={`text-sm font-semibold ${riskTone(report.risk_score)}`}>
                    {report.risk_score}
                  </span>
                </div>
                <p className="line-clamp-2 text-sm leading-6 text-slate-400">
                  {report.summary ?? "No summary"}
                </p>
                <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                  <span>{report.story_count} stories</span>
                  <span>{report.item_count} citations</span>
                  <span>{report.report_type}</span>
                </div>
              </button>
            ))}
            {!loading && reports.length === 0 ? (
              <p className="p-4 text-sm text-slate-400">No reports generated yet</p>
            ) : null}
          </div>
        </section>
      </div>

      <ReportDetailPanel
        detail={detail}
        onDelete={deleteReport}
        onOpenStory={onOpenStory}
        onOpenItem={onOpenItem}
      />
    </section>
  );
}

function ReportDetailPanel({
  detail,
  onDelete,
  onOpenStory,
  onOpenItem
}: {
  detail: ReportDetail | null;
  onDelete: (reportId: string) => Promise<void>;
  onOpenStory: (storyId: string) => void;
  onOpenItem: (itemId: string) => void;
}) {
  if (!detail) {
    return (
      <section className="border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">
        Select or generate a report
      </section>
    );
  }

  return (
    <section className="grid gap-5 border border-white/10 bg-white/[0.04] p-5">
      <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
        <div>
          <p className="text-xs uppercase text-signal">{detail.report_type}</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{detail.title}</h2>
          <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-300">
            {detail.summary ?? "No summary"}
          </p>
        </div>
        <div className="flex flex-wrap items-start gap-2">
          <a
            href={`${apiBaseUrl}/reports/${detail.id}/markdown`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex h-10 items-center gap-2 border border-ice/30 bg-ice/10 px-3 text-sm font-semibold text-ice transition hover:border-ice"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            Markdown
          </a>
          <button
            type="button"
            onClick={() => void onDelete(detail.id)}
            className="inline-flex h-10 w-10 items-center justify-center border border-white/10 text-slate-300 transition hover:border-red-400/50 hover:text-red-300"
            aria-label="Delete report"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-5">
        {[
          ["Risk", detail.risk_score],
          ["Stories", detail.story_count],
          ["Citations", detail.item_count],
          ["Entities", detail.entity_count],
          ["Sources", detail.source_count]
        ].map(([label, value]) => (
          <div key={label} className="border border-white/10 bg-obsidian/50 p-3">
            <p className="text-xs uppercase text-slate-500">{label}</p>
            <p className="mt-2 text-lg font-semibold text-white">{value}</p>
          </div>
        ))}
      </div>

      <section className="grid gap-3">
        <h3 className="text-sm font-semibold text-white">Stories</h3>
        <div className="grid gap-2 md:grid-cols-2">
          {detail.stories.map((entry) => (
            <button
              key={entry.story_id}
              type="button"
              onClick={() => onOpenStory(entry.story_id)}
              className="grid gap-2 border border-white/10 p-3 text-left transition hover:border-signal/40"
            >
              <span className="truncate text-sm font-semibold text-white">{entry.story.title}</span>
              <span className="text-xs text-slate-500">
                Risk {entry.story.risk_score} - {entry.story.item_count} news
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="grid gap-3">
        <h3 className="text-sm font-semibold text-white">Evidence</h3>
        <div className="grid gap-2">
          {detail.items.map((entry) => (
            <article
              key={entry.item_id}
              className="grid gap-3 border border-white/10 bg-obsidian/40 p-3 lg:grid-cols-[1fr_auto]"
            >
              <button
                type="button"
                onClick={() => onOpenItem(entry.item_id)}
                className="min-w-0 text-left"
              >
                <p className="text-xs font-semibold text-signal">[{entry.citation_id}]</p>
                <p className="mt-1 truncate text-sm font-semibold text-white">
                  {entry.item.normalized_title ?? entry.item.title}
                </p>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                  {entry.item.ai_summary ?? entry.item.summary ?? "No summary"}
                </p>
              </button>
              <a
                href={entry.item.url}
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

      <section className="grid gap-3">
        <h3 className="text-sm font-semibold text-white">Markdown Preview</h3>
        <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap border border-white/10 bg-obsidian p-4 text-xs leading-6 text-slate-300">
          {detail.body_markdown}
        </pre>
      </section>
    </section>
  );
}

function alertStatusTone(status: string) {
  if (status === "open") {
    return "border-red-400/40 bg-red-500/10 text-red-200";
  }

  if (status === "acknowledged") {
    return "border-amber-300/40 bg-amber-400/10 text-amber-100";
  }

  if (status === "resolved") {
    return "border-signal/40 bg-signal/10 text-signal";
  }

  return "border-white/10 bg-white/[0.04] text-slate-300";
}

function AlertsView({
  onOpenStory,
  onOpenItem,
  onOpenEntity
}: {
  onOpenStory: (storyId: string) => void;
  onOpenItem: (itemId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [entityType, setEntityType] = useState("all");
  const [valuePattern, setValuePattern] = useState("");
  const [severity, setSeverity] = useState("all");
  const [minRiskScore, setMinRiskScore] = useState("70");
  const [isEnabled, setIsEnabled] = useState(true);
  const [statusFilter, setStatusFilter] = useState("open");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedAlert = alerts.find((alert) => alert.id === selectedAlertId) ?? alerts[0] ?? null;
  const selectedWatchlist = selectedAlert
    ? watchlists.find((watchlist) => watchlist.id === selectedAlert.watchlist_id)
    : null;

  async function loadWatchlists() {
    const data = await apiRequest<Watchlist[]>("/watchlists?limit=100");
    setWatchlists(data);
  }

  async function loadAlerts(nextStatus = statusFilter) {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ limit: "100" });

      if (nextStatus !== "all") {
        params.set("status", nextStatus);
      }

      const data = await apiRequest<Alert[]>(`/alerts?${params.toString()}`);
      setAlerts(data);
      setSelectedAlertId((current) => current ?? data[0]?.id ?? null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load alerts");
    } finally {
      setLoading(false);
    }
  }

  async function refreshAll(nextStatus = statusFilter) {
    await Promise.all([loadWatchlists(), loadAlerts(nextStatus)]);
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
      void loadAlerts(statusFilter);
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  async function createWatchlist() {
    const trimmedName = name.trim();

    if (!trimmedName) {
      setError("Watchlist name is required");
      return;
    }

    setCreating(true);
    setMessage(null);
    setError(null);

    try {
      await apiRequest<Watchlist>("/watchlists", {
        method: "POST",
        body: JSON.stringify({
          name: trimmedName,
          entity_type: entityType === "all" ? null : entityType,
          value_pattern: valuePattern.trim() || null,
          severity: severity === "all" ? null : severity,
          min_risk_score: Number(minRiskScore) || 1,
          is_enabled: isEnabled
        })
      });
      setName("");
      setValuePattern("");
      setMessage("Watchlist created");
      await refreshAll();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create watchlist");
    } finally {
      setCreating(false);
    }
  }

  async function syncAlerts() {
    setSyncing(true);
    setMessage(null);
    setError(null);

    try {
      const result = await apiRequest<AlertSyncResult>("/alerts/sync?limit=500", { method: "POST" });
      setMessage(
        `Alerts sync: ${result.alerts_created} created / ${result.watchlists_checked} watchlists`
      );
      await refreshAll();
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Unable to sync alerts");
    } finally {
      setSyncing(false);
    }
  }

  async function updateAlertStatus(alertId: string, nextStatus: string) {
    setMessage(null);
    setError(null);

    try {
      const updated = await apiRequest<Alert>(`/alerts/${alertId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus })
      });
      setAlerts((current) =>
        current
          .map((alert) => (alert.id === alertId ? updated : alert))
          .filter((alert) => statusFilter === "all" || alert.status === statusFilter)
      );
      setSelectedAlertId(updated.id);
      setMessage(`Alert marked as ${nextStatus}`);
    } catch (statusError) {
      setError(statusError instanceof Error ? statusError.message : "Unable to update alert");
    }
  }

  async function deleteWatchlist(watchlistId: string) {
    setMessage(null);
    setError(null);

    try {
      await apiRequest<void>(`/watchlists/${watchlistId}`, { method: "DELETE" });
      setMessage("Watchlist deleted");
      await refreshAll();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete watchlist");
    }
  }

  return (
    <section className="grid gap-5 xl:grid-cols-[430px_minmax(0,1fr)]">
      <div className="grid gap-5">
        <section className="border border-white/10 bg-white/[0.04] p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center border border-signal/40 bg-signal/10 text-signal">
              <Bell className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase text-signal">Watchlists</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Detection Rules</h2>
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
              placeholder="Watchlist name"
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <select
                value={entityType}
                onChange={(event) => setEntityType(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                {entityTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              <select
                value={severity}
                onChange={(event) => setSeverity(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                {["all", "critical", "high", "medium", "low", "unknown"].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-3 sm:grid-cols-[1fr_120px]">
              <input
                value={valuePattern}
                onChange={(event) => setValuePattern(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="CVE, IOC, actor or tag"
              />
              <input
                type="number"
                min="1"
                max="100"
                value={minRiskScore}
                onChange={(event) => setMinRiskScore(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="Risk"
              />
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setIsEnabled((current) => !current)}
                className="inline-flex h-10 items-center gap-2 border border-white/10 px-3 text-sm font-semibold text-slate-300 transition hover:border-signal/40 hover:text-signal"
              >
                {isEnabled ? (
                  <Power className="h-4 w-4 text-signal" aria-hidden="true" />
                ) : (
                  <PowerOff className="h-4 w-4 text-slate-500" aria-hidden="true" />
                )}
                {isEnabled ? "Enabled" : "Disabled"}
              </button>
              <button
                type="button"
                onClick={() => void createWatchlist()}
                disabled={creating}
                className="inline-flex h-10 items-center gap-2 bg-signal px-4 text-sm font-semibold text-obsidian transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Bell className={creating ? "h-4 w-4 animate-pulse" : "h-4 w-4"} aria-hidden="true" />
                {creating ? "Creating" : "Create"}
              </button>
            </div>
          </div>
        </section>

        <section className="border border-white/10 bg-white/[0.035]">
          <div className="flex items-center justify-between gap-3 border-b border-white/10 p-4">
            <h3 className="text-lg font-semibold text-white">Rules</h3>
            <button
              type="button"
              onClick={() => void refreshAll()}
              className="inline-flex h-9 w-9 items-center justify-center border border-white/10 text-slate-300 transition hover:border-signal/40 hover:text-signal"
              aria-label="Refresh watchlists"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
          <div className="max-h-[calc(100vh-560px)] overflow-auto divide-y divide-white/10">
            {watchlists.map((watchlist) => (
              <article key={watchlist.id} className="grid gap-2 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-white">{watchlist.name}</p>
                    <p className="mt-1 text-xs uppercase text-slate-500">
                      {watchlist.entity_type ?? "all"} / {watchlist.severity ?? "all"} / risk{" "}
                      {watchlist.min_risk_score}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void deleteWatchlist(watchlist.id)}
                    className="inline-flex h-9 w-9 shrink-0 items-center justify-center border border-white/10 text-slate-300 transition hover:border-red-400/50 hover:text-red-300"
                    aria-label={`Delete ${watchlist.name}`}
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span
                    className={
                      watchlist.is_enabled
                        ? "border border-signal/30 px-2 py-1 text-signal"
                        : "border border-white/10 px-2 py-1 text-slate-500"
                    }
                  >
                    {watchlist.is_enabled ? "enabled" : "disabled"}
                  </span>
                  {watchlist.value_pattern ? (
                    <span className="border border-white/10 px-2 py-1 text-slate-300">
                      {watchlist.value_pattern}
                    </span>
                  ) : null}
                </div>
              </article>
            ))}
            {watchlists.length === 0 ? (
              <p className="p-4 text-sm text-slate-400">No watchlists created yet</p>
            ) : null}
          </div>
        </section>
      </div>

      <section className="grid gap-5">
        <section className="border border-white/10 bg-white/[0.04] p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase text-signal">Alerts</p>
              <h2 className="mt-1 text-xl font-semibold text-white">Analyst Triage</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                {["open", "acknowledged", "resolved", "dismissed", "all"].map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void syncAlerts()}
                disabled={syncing}
                className="inline-flex h-10 items-center gap-2 border border-signal/40 bg-signal/10 px-3 text-sm font-semibold text-signal transition hover:bg-signal hover:text-obsidian disabled:cursor-not-allowed disabled:opacity-50"
              >
                <RefreshCw className={syncing ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
                {syncing ? "Syncing" : "Sync Alerts"}
              </button>
            </div>
          </div>
          {message ? <p className="mt-3 text-sm text-signal">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
        </section>

        <section className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_440px]">
          <div className="border border-white/10 bg-white/[0.035]">
            <div className="max-h-[calc(100vh-320px)] overflow-auto divide-y divide-white/10">
              {loading ? <p className="p-4 text-sm text-slate-400">Loading alerts</p> : null}
              {alerts.map((alert) => (
                <button
                  key={alert.id}
                  type="button"
                  onClick={() => setSelectedAlertId(alert.id)}
                  className={
                    selectedAlert?.id === alert.id
                      ? "grid w-full gap-3 bg-signal/10 p-4 text-left"
                      : "grid w-full gap-3 p-4 text-left transition hover:bg-white/[0.04]"
                  }
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-semibold text-white">
                        {alert.title}
                      </span>
                      <span className="mt-1 block text-xs uppercase text-slate-500">
                        {alert.entity_type} / {alert.entity_value}
                      </span>
                    </span>
                    <span className={`text-sm font-semibold ${riskTone(alert.risk_score)}`}>
                      {alert.risk_score}
                    </span>
                  </div>
                  <p className="line-clamp-2 text-sm leading-6 text-slate-400">
                    {alert.description ?? "No alert description"}
                  </p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className={`border px-2 py-1 ${alertStatusTone(alert.status)}`}>
                      {alert.status}
                    </span>
                    <span className="border border-white/10 px-2 py-1 text-slate-300">
                      {alert.severity ?? "unknown"}
                    </span>
                    <span className="border border-white/10 px-2 py-1 text-slate-500">
                      {formatDate(alert.matched_at)}
                    </span>
                  </div>
                </button>
              ))}
              {!loading && alerts.length === 0 ? (
                <p className="p-4 text-sm text-slate-400">No alerts for this filter</p>
              ) : null}
            </div>
          </div>

          <AlertDetailPanel
            alert={selectedAlert}
            watchlist={selectedWatchlist ?? null}
            onUpdateStatus={updateAlertStatus}
            onOpenStory={onOpenStory}
            onOpenItem={onOpenItem}
            onOpenEntity={onOpenEntity}
          />
        </section>
      </section>
    </section>
  );
}

function AlertDetailPanel({
  alert,
  watchlist,
  onUpdateStatus,
  onOpenStory,
  onOpenItem,
  onOpenEntity
}: {
  alert: Alert | null;
  watchlist: Watchlist | null;
  onUpdateStatus: (alertId: string, nextStatus: string) => Promise<void>;
  onOpenStory: (storyId: string) => void;
  onOpenItem: (itemId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  if (!alert) {
    return (
      <aside className="border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">
        Select an alert
      </aside>
    );
  }

  const triageActions = [
    { status: "acknowledged", icon: CheckCircle2 },
    { status: "resolved", icon: ShieldCheck },
    { status: "dismissed", icon: Trash2 }
  ];

  return (
    <aside className="grid gap-5 border border-white/10 bg-white/[0.045] p-5">
      <div className="grid gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase text-signal">Alert Detail</p>
            <h2 className="mt-2 text-xl font-semibold leading-7 text-white">{alert.title}</h2>
          </div>
          <span className={`shrink-0 border px-2 py-1 text-xs ${alertStatusTone(alert.status)}`}>
            {alert.status}
          </span>
        </div>
        <p className="text-sm leading-6 text-slate-300">
          {alert.description ?? "No alert description"}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        {[
          ["Risk", alert.risk_score],
          ["Severity", alert.severity ?? "unknown"],
          ["Matched", formatDate(alert.matched_at)],
          ["Rule", watchlist?.name ?? alert.watchlist_id]
        ].map(([label, value]) => (
          <div key={label} className="border border-white/10 bg-obsidian/50 p-3">
            <p className="text-xs uppercase text-slate-500">{label}</p>
            <p className="mt-2 truncate font-semibold text-white">{value}</p>
          </div>
        ))}
      </div>

      <section className="grid gap-2">
        <h3 className="text-sm font-semibold text-white">Matched Entity</h3>
        <div className="flex flex-wrap gap-2">
          <EntityPill
            entityType={alert.entity_type}
            value={alert.entity_value}
            onOpen={onOpenEntity}
          />
        </div>
      </section>

      <section className="grid gap-2">
        <h3 className="text-sm font-semibold text-white">Context Links</h3>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onOpenItem(alert.item_id)}
            className="inline-flex h-9 items-center gap-2 border border-white/10 px-3 text-sm text-slate-300 transition hover:border-signal/40 hover:text-signal"
          >
            <Newspaper className="h-4 w-4" aria-hidden="true" />
            News
          </button>
          {alert.story_id ? (
            <button
              type="button"
              onClick={() => onOpenStory(alert.story_id!)}
              className="inline-flex h-9 items-center gap-2 border border-white/10 px-3 text-sm text-slate-300 transition hover:border-signal/40 hover:text-signal"
            >
              <GitBranch className="h-4 w-4" aria-hidden="true" />
              Story
            </button>
          ) : null}
        </div>
      </section>

      <section className="grid gap-2">
        <h3 className="text-sm font-semibold text-white">Triage</h3>
        <div className="grid gap-2 sm:grid-cols-3">
          {triageActions.map(({ status, icon: StatusIcon }) => (
            <button
              key={status}
              type="button"
              onClick={() => void onUpdateStatus(alert.id, status)}
              disabled={alert.status === status}
              className="inline-flex h-10 items-center justify-center gap-2 border border-white/10 px-3 text-sm font-semibold text-slate-300 transition hover:border-signal/40 hover:text-signal disabled:cursor-not-allowed disabled:opacity-50"
            >
              <StatusIcon className="h-4 w-4" aria-hidden="true" />
              {status}
            </button>
          ))}
        </div>
      </section>

      <section className="grid gap-2">
        <h3 className="text-sm font-semibold text-white">Evidence</h3>
        <pre className="max-h-72 overflow-auto whitespace-pre-wrap border border-white/10 bg-obsidian p-4 text-xs leading-6 text-slate-300">
          {JSON.stringify(alert.evidence, null, 2)}
        </pre>
      </section>
    </aside>
  );
}

function EnterpriseView() {
  const [overview, setOverview] = useState<EnterpriseOverview | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<EnterpriseUser[]>([]);
  const [memberships, setMemberships] = useState<DepartmentMembership[]>([]);
  const [roles, setRoles] = useState<EnterpriseRole[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [modelUsage, setModelUsage] = useState<ModelUsage[]>([]);
  const [departmentName, setDepartmentName] = useState("");
  const [departmentOwner, setDepartmentOwner] = useState("");
  const [riskAppetite, setRiskAppetite] = useState("medium");
  const [userEmail, setUserEmail] = useState("");
  const [userName, setUserName] = useState("");
  const [membershipDepartmentId, setMembershipDepartmentId] = useState("");
  const [membershipUserId, setMembershipUserId] = useState("");
  const [membershipRole, setMembershipRole] = useState("analyst");
  const [loading, setLoading] = useState(true);
  const [syncingUsage, setSyncingUsage] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshEnterprise() {
    setLoading(true);
    setError(null);

    try {
      const [
        overviewData,
        departmentData,
        userData,
        membershipData,
        roleData,
        auditData,
        usageData
      ] = await Promise.all([
        apiRequest<EnterpriseOverview>("/enterprise/overview"),
        apiRequest<Department[]>("/enterprise/departments?limit=100"),
        apiRequest<EnterpriseUser[]>("/enterprise/users?limit=100"),
        apiRequest<DepartmentMembership[]>("/enterprise/memberships?limit=100"),
        apiRequest<EnterpriseRole[]>("/enterprise/roles"),
        apiRequest<AuditEvent[]>("/enterprise/audit-events?limit=12"),
        apiRequest<ModelUsage[]>("/enterprise/model-usage?limit=12")
      ]);

      setOverview(overviewData);
      setDepartments(departmentData);
      setUsers(userData);
      setMemberships(membershipData);
      setRoles(roleData);
      setAuditEvents(auditData);
      setModelUsage(usageData);
      setMembershipDepartmentId((current) => current || departmentData[0]?.id || "");
      setMembershipUserId((current) => current || userData[0]?.id || "");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load enterprise data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshEnterprise();
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  async function createDepartment() {
    const trimmedName = departmentName.trim();

    if (!trimmedName) {
      setError("Department name is required");
      return;
    }

    setMessage(null);
    setError(null);

    try {
      await apiRequest<Department>("/enterprise/departments", {
        method: "POST",
        body: JSON.stringify({
          name: trimmedName,
          owner_email: departmentOwner.trim() || null,
          risk_appetite: riskAppetite,
          is_active: true
        })
      });
      setDepartmentName("");
      setDepartmentOwner("");
      setMessage("Department created");
      await refreshEnterprise();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create department");
    }
  }

  async function createUser() {
    const trimmedEmail = userEmail.trim();

    if (!trimmedEmail) {
      setError("User email is required");
      return;
    }

    setMessage(null);
    setError(null);

    try {
      await apiRequest<EnterpriseUser>("/enterprise/users", {
        method: "POST",
        body: JSON.stringify({
          email: trimmedEmail,
          full_name: userName.trim() || null,
          is_active: true,
          is_superuser: false
        })
      });
      setUserEmail("");
      setUserName("");
      setMessage("Enterprise user created");
      await refreshEnterprise();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create user");
    }
  }

  async function createMembership() {
    if (!membershipDepartmentId || !membershipUserId) {
      setError("Select a department and user first");
      return;
    }

    setMessage(null);
    setError(null);

    try {
      await apiRequest<DepartmentMembership>(
        `/enterprise/departments/${membershipDepartmentId}/memberships`,
        {
          method: "POST",
          body: JSON.stringify({
            user_id: membershipUserId,
            role: membershipRole,
            permissions: [],
            is_active: true
          })
        }
      );
      setMessage("Membership created");
      await refreshEnterprise();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create membership");
    }
  }

  async function syncUsage() {
    setSyncingUsage(true);
    setMessage(null);
    setError(null);

    try {
      const result = await apiRequest<ModelUsageSyncResult>("/enterprise/model-usage/sync?limit=500", {
        method: "POST"
      });
      setMessage(
        `Model usage sync: ${result.usage_created} created / ${result.enrichments_checked} enrichments`
      );
      await refreshEnterprise();
    } catch (syncError) {
      setError(syncError instanceof Error ? syncError.message : "Unable to sync model usage");
    } finally {
      setSyncingUsage(false);
    }
  }

  const roleMap = new Map(roles.map((role) => [role.role, role]));
  const departmentMap = new Map(departments.map((department) => [department.id, department]));
  const userMap = new Map(users.map((user) => [user.id, user]));

  return (
    <section className="grid gap-5">
      <section className="border border-white/10 bg-white/[0.04] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center border border-signal/40 bg-signal/10 text-signal">
              <Building2 className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-signal">Enterprise</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Governance Control Plane</h2>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void syncUsage()}
              disabled={syncingUsage}
              className="inline-flex h-10 items-center gap-2 border border-ice/30 bg-ice/10 px-3 text-sm font-semibold text-ice transition hover:border-ice disabled:cursor-not-allowed disabled:opacity-60"
            >
              <DollarSign className={syncingUsage ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
              {syncingUsage ? "Syncing" : "Sync Usage"}
            </button>
            <button
              type="button"
              onClick={() => void refreshEnterprise()}
              className="inline-flex h-10 w-10 items-center justify-center border border-white/10 text-slate-300 transition hover:border-signal/40 hover:text-signal"
              aria-label="Refresh enterprise"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
        {message ? <p className="mt-3 text-sm text-signal">{message}</p> : null}
        {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
      </section>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {[
          ["Departments", overview?.departments ?? 0],
          ["Users", overview?.users ?? 0],
          ["Memberships", overview?.memberships ?? 0],
          ["Open Alerts", overview?.open_alerts ?? 0],
          ["Model Usage", overview?.model_usage_records ?? 0]
        ].map(([label, value]) => (
          <div key={label} className="border border-white/10 bg-white/[0.035] p-4">
            <p className="text-xs uppercase text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
        <div className="grid gap-5">
          <section className="border border-white/10 bg-white/[0.04] p-5">
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-signal" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-white">Departments</h3>
            </div>
            <div className="mt-4 grid gap-3">
              <input
                value={departmentName}
                onChange={(event) => setDepartmentName(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="Department name"
              />
              <input
                value={departmentOwner}
                onChange={(event) => setDepartmentOwner(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="Owner email"
              />
              <select
                value={riskAppetite}
                onChange={(event) => setRiskAppetite(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                {["low", "medium", "high"].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void createDepartment()}
                className="inline-flex h-10 items-center justify-center gap-2 bg-signal px-4 text-sm font-semibold text-obsidian transition hover:bg-emerald-300"
              >
                <Building2 className="h-4 w-4" aria-hidden="true" />
                Create Department
              </button>
            </div>
          </section>

          <section className="border border-white/10 bg-white/[0.04] p-5">
            <div className="flex items-center gap-3">
              <Users className="h-5 w-5 text-signal" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-white">Users And Roles</h3>
            </div>
            <div className="mt-4 grid gap-3">
              <input
                value={userEmail}
                onChange={(event) => setUserEmail(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="user@example.com"
              />
              <input
                value={userName}
                onChange={(event) => setUserName(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none transition focus:border-signal/60"
                placeholder="Full name"
              />
              <button
                type="button"
                onClick={() => void createUser()}
                className="inline-flex h-10 items-center justify-center gap-2 border border-signal/40 bg-signal/10 px-4 text-sm font-semibold text-signal transition hover:bg-signal hover:text-obsidian"
              >
                <Users className="h-4 w-4" aria-hidden="true" />
                Create User
              </button>
            </div>
            <div className="mt-5 grid gap-3 border-t border-white/10 pt-4">
              <select
                value={membershipDepartmentId}
                onChange={(event) => setMembershipDepartmentId(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                <option value="">Select department</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </select>
              <select
                value={membershipUserId}
                onChange={(event) => setMembershipUserId(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                <option value="">Select user</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.email}
                  </option>
                ))}
              </select>
              <select
                value={membershipRole}
                onChange={(event) => setMembershipRole(event.target.value)}
                className="h-10 border border-white/10 bg-obsidian px-3 text-sm text-white outline-none"
              >
                {roles.map((role) => (
                  <option key={role.role} value={role.role}>
                    {role.role}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void createMembership()}
                className="inline-flex h-10 items-center justify-center gap-2 border border-ice/30 bg-ice/10 px-4 text-sm font-semibold text-ice transition hover:border-ice"
              >
                <ShieldCheck className="h-4 w-4" aria-hidden="true" />
                Assign Role
              </button>
            </div>
          </section>
        </div>

        <section className="grid gap-5">
          <div className="grid gap-5 2xl:grid-cols-2">
            <section className="border border-white/10 bg-white/[0.035]">
              <div className="border-b border-white/10 p-4">
                <h3 className="text-lg font-semibold text-white">Department Directory</h3>
              </div>
              <div className="max-h-80 overflow-auto divide-y divide-white/10">
                {loading ? <p className="p-4 text-sm text-slate-400">Loading enterprise data</p> : null}
                {departments.map((department) => (
                  <article key={department.id} className="grid gap-2 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">{department.name}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {department.owner_email ?? "No owner"} / {department.risk_appetite}
                        </p>
                      </div>
                      <span
                        className={
                          department.is_active
                            ? "border border-signal/30 px-2 py-1 text-xs text-signal"
                            : "border border-white/10 px-2 py-1 text-xs text-slate-500"
                        }
                      >
                        {department.is_active ? "active" : "inactive"}
                      </span>
                    </div>
                  </article>
                ))}
                {!loading && departments.length === 0 ? (
                  <p className="p-4 text-sm text-slate-400">No departments yet</p>
                ) : null}
              </div>
            </section>

            <section className="border border-white/10 bg-white/[0.035]">
              <div className="border-b border-white/10 p-4">
                <h3 className="text-lg font-semibold text-white">Memberships</h3>
              </div>
              <div className="max-h-80 overflow-auto divide-y divide-white/10">
                {memberships.map((membership) => {
                  const department = departmentMap.get(membership.department_id);
                  const user = userMap.get(membership.user_id);
                  const role = roleMap.get(membership.role);

                  return (
                    <article key={membership.id} className="grid gap-2 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-white">
                            {user?.email ?? membership.user_id}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            {department?.name ?? membership.department_id} / {membership.role}
                          </p>
                        </div>
                        <span className="border border-white/10 px-2 py-1 text-xs text-slate-300">
                          {membership.permissions.length}
                        </span>
                      </div>
                      <p className="line-clamp-2 text-xs leading-5 text-slate-500">
                        {role?.description ?? "Custom role permissions"}
                      </p>
                    </article>
                  );
                })}
                {memberships.length === 0 ? (
                  <p className="p-4 text-sm text-slate-400">No memberships assigned yet</p>
                ) : null}
              </div>
            </section>
          </div>

          <div className="grid gap-5 2xl:grid-cols-2">
            <section className="border border-white/10 bg-white/[0.035]">
              <div className="border-b border-white/10 p-4">
                <h3 className="text-lg font-semibold text-white">Audit Trail</h3>
              </div>
              <div className="max-h-96 overflow-auto divide-y divide-white/10">
                {auditEvents.map((event) => (
                  <article key={event.id} className="grid gap-2 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <p className="min-w-0 truncate text-sm font-semibold text-white">
                        {event.action}
                      </p>
                      <span className="border border-signal/30 px-2 py-1 text-xs text-signal">
                        {event.outcome}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                      <span>{event.resource_type}</span>
                      <span>{event.actor_type}</span>
                      <span>{formatDate(event.created_at)}</span>
                    </div>
                  </article>
                ))}
                {auditEvents.length === 0 ? (
                  <p className="p-4 text-sm text-slate-400">No audit events yet</p>
                ) : null}
              </div>
            </section>

            <section className="border border-white/10 bg-white/[0.035]">
              <div className="border-b border-white/10 p-4">
                <h3 className="text-lg font-semibold text-white">Model Usage</h3>
              </div>
              <div className="max-h-96 overflow-auto divide-y divide-white/10">
                {modelUsage.map((usage) => (
                  <article key={usage.id} className="grid gap-2 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">{usage.model}</p>
                        <p className="mt-1 text-xs uppercase text-slate-500">
                          {usage.provider} / {usage.operation}
                        </p>
                      </div>
                      <span className="border border-white/10 px-2 py-1 text-xs text-slate-300">
                        ${usage.estimated_cost_usd}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                      <span>in {usage.input_tokens}</span>
                      <span>out {usage.output_tokens}</span>
                      <span>{formatDate(usage.created_at)}</span>
                    </div>
                  </article>
                ))}
                {modelUsage.length === 0 ? (
                  <p className="p-4 text-sm text-slate-400">No model usage records yet</p>
                ) : null}
              </div>
            </section>
          </div>
        </section>
      </section>
    </section>
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

          <PipelineControls />

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

          {activeView === "ask" ? (
            <AskCyberSecView
              onOpenItem={openItem}
              onOpenStory={openStory}
              onOpenEntity={openEntity}
            />
          ) : null}

          {activeView === "reports" ? (
            <ReportsView onOpenStory={openStory} onOpenItem={openItem} />
          ) : null}

          {activeView === "alerts" ? (
            <AlertsView
              onOpenStory={openStory}
              onOpenItem={openItem}
              onOpenEntity={openEntity}
            />
          ) : null}

          {activeView === "enterprise" ? <EnterpriseView /> : null}

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

      <NewsDetailPanel
        context={context}
        onContextUpdated={setContext}
        onOpenStory={onOpenStory}
        onOpenEntity={onOpenEntity}
      />
    </section>
  );
}

function NewsDetailPanel({
  context,
  onContextUpdated,
  onOpenStory,
  onOpenEntity
}: {
  context: ItemContext | null;
  onContextUpdated: (context: ItemContext) => void;
  onOpenStory: (storyId: string) => void;
  onOpenEntity: (entityType: string, value: string) => void;
}) {
  const [enriching, setEnriching] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!context) {
    return (
      <aside className="border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">
        Select a news item
      </aside>
    );
  }

  const item = context.item;

  async function enrichItem() {
    setEnriching(true);
    setMessage(null);
    setError(null);

    try {
      const result = await apiRequest<{ status: string; error: string | null }>(
        `/enrichment/items/${item.id}/run`,
        { method: "POST" }
      );

      if (result.status === "error") {
        setError(result.error ?? "Unable to enrich item");
        return;
      }

      const updatedContext = await apiRequest<ItemContext>(`/items/${item.id}/context`);
      onContextUpdated(updatedContext);
      setMessage(result.status === "completed" ? "AI enrichment completed" : result.status);
    } catch (enrichmentError) {
      setError(enrichmentError instanceof Error ? enrichmentError.message : "Unable to enrich item");
    } finally {
      setEnriching(false);
    }
  }

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

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => void enrichItem()}
          disabled={enriching || item.status !== "normalized" || item.is_duplicate}
          className="inline-flex h-10 items-center gap-2 border border-signal/40 bg-signal/10 px-3 text-sm font-semibold text-signal transition hover:bg-signal hover:text-obsidian disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Sparkles className={enriching ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
          {enriching ? "Enriching" : item.ai_summary ? "Refresh AI Enrichment" : "Enrich Item"}
        </button>
        {message ? <span className="self-center text-sm text-signal">{message}</span> : null}
        {error ? <span className="self-center text-sm text-red-300">{error}</span> : null}
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
