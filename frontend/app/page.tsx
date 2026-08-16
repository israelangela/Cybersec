import { Activity, Database, Radar, ShieldCheck } from "lucide-react";

import { getSystemStatus } from "@/lib/system-status";

export default async function Home() {
  const status = await getSystemStatus();

  return (
    <main className="min-h-screen overflow-hidden px-6 py-8 sm:px-10 lg:px-16">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-7xl flex-col justify-between gap-12">
        <header className="flex items-center justify-between border-b border-white/10 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center border border-signal/40 bg-signal/10 text-signal shadow-glow">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <span className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-300">
              CyberSec
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <span className="h-2 w-2 bg-signal" aria-hidden="true" />
            System Status: {status}
          </div>
        </header>

        <div className="grid items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="max-w-3xl">
            <p className="mb-5 text-sm font-semibold uppercase tracking-[0.32em] text-signal">
              Phase 0 Foundation
            </p>
            <h1 className="text-5xl font-semibold leading-tight text-white sm:text-6xl lg:text-7xl">
              CyberSec
            </h1>
            <p className="mt-6 max-w-2xl text-xl leading-8 text-slate-300">
              Cyber Threat Intelligence Platform
            </p>
          </div>

          <div className="grid gap-4">
            {[
              { label: "API", value: "FastAPI", icon: Activity },
              { label: "Database", value: "PostgreSQL", icon: Database },
              { label: "Intelligence Core", value: "Ready", icon: Radar }
            ].map((item) => (
              <div
                key={item.label}
                className="border border-white/10 bg-white/[0.04] p-5 backdrop-blur-sm"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-400">{item.label}</p>
                    <p className="mt-1 text-lg font-semibold text-white">{item.value}</p>
                  </div>
                  <item.icon className="h-6 w-6 text-signal" aria-hidden="true" />
                </div>
              </div>
            ))}
          </div>
        </div>

        <footer className="grid gap-3 border-t border-white/10 pt-5 text-sm text-slate-400 sm:grid-cols-3">
          <span>Health endpoint active</span>
          <span>Readiness backed by database</span>
          <span>Initial schema: User, Source, Item</span>
        </footer>
      </section>
    </main>
  );
}
