"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  Blocks,
  Database,
  Eye,
  RadioTower,
  ShieldCheck,
  TerminalSquare,
  Waypoints
} from "lucide-react";

import { IntelligenceWorkbench } from "@/components/intelligence-workbench";
import { SourceManagement } from "@/components/source-management";
import { WarRoom } from "@/components/war-room";

type ConsoleView = "command" | "intelligence" | "sources";

type ConsoleNavItem = {
  id: ConsoleView;
  label: string;
  description: string;
  icon: typeof Waypoints;
};

const navigation: ConsoleNavItem[] = [
  {
    id: "command",
    label: "Command",
    description: "War Room",
    icon: Waypoints
  },
  {
    id: "intelligence",
    label: "Intelligence",
    description: "Workbench",
    icon: TerminalSquare
  },
  {
    id: "sources",
    label: "Sources",
    description: "Feeds",
    icon: RadioTower
  }
];

type CybersecConsoleProps = {
  status: string;
};

export function CybersecConsole({ status }: CybersecConsoleProps) {
  const [activeView, setActiveView] = useState<ConsoleView>("command");

  const activeNav = useMemo(
    () => navigation.find((item) => item.id === activeView) ?? navigation[0],
    [activeView]
  );

  return (
    <main className="min-h-screen overflow-hidden">
      <div className="fixed inset-0 -z-10 bg-obsidian">
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(0deg,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:56px_56px]" />
        <div className="absolute inset-0 bg-[linear-gradient(135deg,#07080d_0%,#10131b_48%,#07110e_100%)]" />
        <div className="absolute left-0 top-0 h-full w-1/2 bg-[linear-gradient(115deg,rgba(34,197,94,0.08),transparent_55%)]" />
      </div>

      <section className="mx-auto grid min-h-screen w-full max-w-[1600px] gap-0 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-white/10 bg-black/25 p-5 backdrop-blur-xl lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r lg:border-white/10">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center border border-signal/40 bg-signal/10 text-signal shadow-glow">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase text-slate-300">
                CyberSec
              </p>
              <p className="mt-1 text-xs uppercase text-slate-500">Threat Intelligence</p>
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
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{item.label}</span>
                    <span className="block text-xs uppercase text-slate-500">{item.description}</span>
                  </span>
                </button>
              );
            })}
          </nav>

          <div className="mt-6 hidden border border-white/10 bg-white/[0.025] p-4 lg:block">
            <Blocks className="h-5 w-5 text-ice" aria-hidden="true" />
            <p className="mt-3 text-sm font-semibold text-white">Phase 8 Console</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              War Room, intelligence operations and source control are separated
              into focused workspaces.
            </p>
          </div>
        </aside>

        <section className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
          <header className="mb-5 grid gap-4 border border-white/10 bg-black/20 p-5 backdrop-blur-xl lg:grid-cols-[1fr_auto]">
            <div>
              <p className="text-sm font-semibold uppercase text-signal">Phase 8 Cyber War Room</p>
              <h1 className="mt-2 text-3xl font-semibold leading-tight text-white sm:text-4xl">
                {activeNav.label}
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
                {activeView === "command"
                  ? "Operational view for risk, stories, entities, timeline and source health."
                  : activeView === "intelligence"
                    ? "Investigate collected items, enrich intelligence and synchronize analytical layers."
                    : "Manage cyber intelligence feeds and collection readiness."}
              </p>
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

          {activeView === "command" ? (
            <WarRoom onNavigate={setActiveView} />
          ) : activeView === "intelligence" ? (
            <IntelligenceWorkbench />
          ) : (
            <SourceManagement />
          )}
        </section>
      </section>
    </main>
  );
}
