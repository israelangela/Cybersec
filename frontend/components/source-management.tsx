"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Pencil,
  Plus,
  Power,
  PowerOff,
  RefreshCw,
  Save,
  Trash2,
  X
} from "lucide-react";

type SourceType = "rss" | "web" | "api" | "other";

type Source = {
  id: string;
  name: string;
  url: string;
  source_type: SourceType;
  description: string | null;
  weight: string;
  is_enabled: boolean;
  last_fetched_at: string | null;
  last_error: string | null;
  error_count: number;
  created_at: string;
  updated_at: string;
};

type SourceFormState = {
  name: string;
  url: string;
  source_type: SourceType;
  description: string;
  weight: string;
  is_enabled: boolean;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const emptyForm: SourceFormState = {
  name: "",
  url: "",
  source_type: "rss",
  description: "",
  weight: "1.00",
  is_enabled: true
};

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

  return response.json() as Promise<T>;
}

export function SourceManagement() {
  const [sources, setSources] = useState<Source[]>([]);
  const [form, setForm] = useState<SourceFormState>(emptyForm);
  const [editingSourceId, setEditingSourceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const enabledCount = useMemo(
    () => sources.filter((source) => source.is_enabled).length,
    [sources]
  );

  async function loadSources() {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest<Source[]>("/sources");
      setSources(data);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load sources");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let isCurrent = true;

    apiRequest<Source[]>("/sources")
      .then((data) => {
        if (isCurrent) {
          setSources(data);
          setError(null);
        }
      })
      .catch((loadError: unknown) => {
        if (isCurrent) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load sources");
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

  function resetForm() {
    setForm(emptyForm);
    setEditingSourceId(null);
  }

  function startEdit(source: Source) {
    setForm({
      name: source.name,
      url: source.url,
      source_type: source.source_type,
      description: source.description ?? "",
      weight: source.weight,
      is_enabled: source.is_enabled
    });
    setEditingSourceId(source.id);
    setMessage(null);
    setError(null);
  }

  async function saveSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);

    const payload = {
      ...form,
      description: form.description.trim() ? form.description : null
    };

    try {
      if (editingSourceId) {
        await apiRequest<Source>(`/sources/${editingSourceId}`, {
          method: "PATCH",
          body: JSON.stringify(payload)
        });
        setMessage("Source updated");
      } else {
        await apiRequest<Source>("/sources", {
          method: "POST",
          body: JSON.stringify(payload)
        });
        setMessage("Source created");
      }

      resetForm();
      await loadSources();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save source");
    } finally {
      setSaving(false);
    }
  }

  async function toggleSource(source: Source) {
    setMessage(null);
    setError(null);

    try {
      await apiRequest<Source>(`/sources/${source.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_enabled: !source.is_enabled })
      });
      await loadSources();
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Unable to update source");
    }
  }

  async function removeSource(source: Source) {
    setMessage(null);
    setError(null);

    try {
      await apiRequest<void>(`/sources/${source.id}`, { method: "DELETE" });
      setMessage("Source deleted");

      if (editingSourceId === source.id) {
        resetForm();
      }

      await loadSources();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete source");
    }
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div className="border border-white/10 bg-white/[0.035]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 p-5">
          <div>
            <h2 className="text-xl font-semibold text-white">Sources</h2>
            <p className="mt-1 text-sm text-slate-400">
              {sources.length} total / {enabledCount} enabled
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadSources()}
            className="inline-flex h-10 items-center gap-2 border border-white/10 px-3 text-sm text-slate-200 transition hover:border-signal/50 hover:text-signal"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </button>
        </div>

        <div className="divide-y divide-white/10">
          {loading ? (
            <div className="p-5 text-sm text-slate-400">Loading sources</div>
          ) : sources.length === 0 ? (
            <div className="p-5 text-sm text-slate-400">No sources configured</div>
          ) : (
            sources.map((source) => (
              <article key={source.id} className="grid gap-4 p-5 lg:grid-cols-[1fr_auto]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="truncate text-base font-semibold text-white">{source.name}</h3>
                    <span className="border border-white/10 px-2 py-1 text-xs uppercase text-slate-300">
                      {source.source_type}
                    </span>
                    <span
                      className={
                        source.is_enabled
                          ? "inline-flex items-center gap-1 text-xs text-signal"
                          : "inline-flex items-center gap-1 text-xs text-slate-500"
                      }
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                      {source.is_enabled ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  <p className="mt-2 truncate text-sm text-ice">{source.url}</p>
                  {source.description ? (
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                      {source.description}
                    </p>
                  ) : null}
                  <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
                    <span>Weight {source.weight}</span>
                    <span>Errors {source.error_count}</span>
                    <span>Last fetched {source.last_fetched_at ?? "Never"}</span>
                  </div>
                </div>

                <div className="flex items-start gap-2">
                  <button
                    type="button"
                    onClick={() => startEdit(source)}
                    className="inline-flex h-10 w-10 items-center justify-center border border-white/10 text-slate-300 transition hover:border-ice/50 hover:text-ice"
                    aria-label={`Edit ${source.name}`}
                  >
                    <Pencil className="h-4 w-4" aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    onClick={() => void toggleSource(source)}
                    className="inline-flex h-10 w-10 items-center justify-center border border-white/10 text-slate-300 transition hover:border-signal/50 hover:text-signal"
                    aria-label={source.is_enabled ? `Disable ${source.name}` : `Enable ${source.name}`}
                  >
                    {source.is_enabled ? (
                      <PowerOff className="h-4 w-4" aria-hidden="true" />
                    ) : (
                      <Power className="h-4 w-4" aria-hidden="true" />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => void removeSource(source)}
                    className="inline-flex h-10 w-10 items-center justify-center border border-white/10 text-slate-300 transition hover:border-red-400/50 hover:text-red-300"
                    aria-label={`Delete ${source.name}`}
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      </div>

      <form onSubmit={(event) => void saveSource(event)} className="border border-white/10 bg-white/[0.045] p-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-white">
              {editingSourceId ? "Edit Source" : "New Source"}
            </h2>
            <p className="mt-1 text-sm text-slate-400">Phase 1 management</p>
          </div>
          {editingSourceId ? (
            <button
              type="button"
              onClick={resetForm}
              className="inline-flex h-9 w-9 items-center justify-center border border-white/10 text-slate-300 transition hover:border-ice/50 hover:text-ice"
              aria-label="Cancel edit"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          ) : null}
        </div>

        <div className="mt-6 grid gap-4">
          <label className="grid gap-2 text-sm text-slate-300">
            Name
            <input
              required
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              className="h-11 border border-white/10 bg-obsidian px-3 text-white outline-none transition placeholder:text-slate-600 focus:border-signal/60"
              placeholder="CISA Advisories"
            />
          </label>

          <label className="grid gap-2 text-sm text-slate-300">
            URL
            <input
              required
              type="url"
              value={form.url}
              onChange={(event) => setForm((current) => ({ ...current, url: event.target.value }))}
              className="h-11 border border-white/10 bg-obsidian px-3 text-white outline-none transition placeholder:text-slate-600 focus:border-signal/60"
              placeholder="https://example.com/feed.xml"
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="grid gap-2 text-sm text-slate-300">
              Type
              <select
                value={form.source_type}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    source_type: event.target.value as SourceType
                  }))
                }
                className="h-11 border border-white/10 bg-obsidian px-3 text-white outline-none transition focus:border-signal/60"
              >
                <option value="rss">RSS</option>
                <option value="web">Web</option>
                <option value="api">API</option>
                <option value="other">Other</option>
              </select>
            </label>

            <label className="grid gap-2 text-sm text-slate-300">
              Weight
              <input
                required
                type="number"
                min="0"
                max="10"
                step="0.01"
                value={form.weight}
                onChange={(event) =>
                  setForm((current) => ({ ...current, weight: event.target.value }))
                }
                className="h-11 border border-white/10 bg-obsidian px-3 text-white outline-none transition focus:border-signal/60"
              />
            </label>
          </div>

          <label className="grid gap-2 text-sm text-slate-300">
            Description
            <textarea
              value={form.description}
              onChange={(event) =>
                setForm((current) => ({ ...current, description: event.target.value }))
              }
              className="min-h-24 resize-y border border-white/10 bg-obsidian px-3 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-signal/60"
              placeholder="Authoritative vulnerability advisories"
            />
          </label>

          <label className="flex items-center justify-between border border-white/10 px-3 py-3 text-sm text-slate-300">
            Enabled
            <input
              type="checkbox"
              checked={form.is_enabled}
              onChange={(event) =>
                setForm((current) => ({ ...current, is_enabled: event.target.checked }))
              }
              className="h-4 w-4 accent-emerald-400"
            />
          </label>
        </div>

        {message ? <p className="mt-4 text-sm text-signal">{message}</p> : null}
        {error ? <p className="mt-4 text-sm text-red-300">{error}</p> : null}

        <button
          type="submit"
          disabled={saving}
          className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 bg-signal px-4 text-sm font-semibold text-obsidian transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {editingSourceId ? (
            <Save className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Plus className="h-4 w-4" aria-hidden="true" />
          )}
          {saving ? "Saving" : editingSourceId ? "Save Source" : "Create Source"}
        </button>
      </form>
    </section>
  );
}
