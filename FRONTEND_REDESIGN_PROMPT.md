# CyberSec Frontend Redesign Prompt

## Goal

Redesign the CyberSec frontend as a professional Cyber Threat Intelligence
console centered on contextual navigation.

The security expert must see how each new article becomes context:

```text
source -> news item -> normalization -> AI enrichment -> cyber entities
-> CVEs / IOCs / MITRE -> story -> operational risk
```

The application must stop feeling like a long page of stacked panels. It should
feel like one coherent cyber product with navigable workspaces and direct links
between related intelligence objects.

## UX Architecture

Use a main SOC/CTI console shell with focused workspaces:

- `War Room`
- `Stories`
- `Entities`
- `News Feed`
- `Sources`

The first screen must be operational. Do not build a marketing landing page.

## Contextual Navigation

- Clicking a story opens the exact story detail.
- Clicking a news item opens the exact news detail.
- Clicking a CVE opens an entity view showing related news and stories.
- Clicking an IOC, MITRE technique or threat actor opens its entity context.
- Each detail view must retain enough context for the analyst to move back.

## War Room

The War Room is the command view. It must show:

- Operating mode
- Top active stories
- Critical CVEs
- Entity pulse
- News timeline
- Source health

Every important row or card must link to its exact detail view.

## Stories

The Stories workspace must show:

- Story list with risk, severity, keywords, entities and number of news items
- Story detail with summary, timeline of related news, exact source articles,
  related CVEs, IOCs, MITRE techniques and involved sources
- Clear evidence for why the story exists

## Entities

The Entities workspace must group by:

- CVE
- IOC
- MITRE ATT&CK technique
- Threat actor
- Tag

Each entity detail must show:

- Maximum risk
- Occurrences
- Related stories
- Related news
- Last appearance

External safe links:

- CVE -> `https://nvd.nist.gov/vuln/detail/{CVE}`
- CVE -> `https://www.cve.org/CVERecord?id={CVE}`
- MITRE -> `https://attack.mitre.org/techniques/{ID}/`

All external links open in a new tab with `rel="noreferrer"`.

## News Feed

The News Feed workspace must show dense analyst-friendly article rows:

- Title
- Source
- Date
- Status
- AI severity
- CVEs / IOCs / MITRE detected
- Related story if available
- Original article link

Selecting a news item opens a detail panel with:

- Normalized content
- AI summary
- Entities
- Recommended actions
- Related story
- Original article link

## Visual Direction

- Professional CTI/SOC product, not a landing page.
- Dark, restrained, operational.
- Use signal green, ice/cyan and risk amber/red with intent.
- Prefer dense layouts, tables, split panes, timelines and relationship rows.
- Avoid endless scroll, repeated card grids and decorative-only visuals.
- All external/untrusted content is rendered as text.

## Implementation Notes

- Use the existing Next.js, React and Tailwind stack.
- Avoid new dependencies unless clearly necessary.
- Prefer local state navigation for this pass.
- Use existing endpoints where possible:
  - `/war-room`
  - `/stories`
  - `/stories/{id}`
  - `/intelligence/entities`
  - `/intelligence/items/{id}/entities`
  - `/items`
  - `/items/{id}`
  - `/sources`
- Add minimal backend endpoints only when required for exact relationships.

## Acceptance Criteria

- The initial view is not a long stacked page.
- War Room links to exact stories, entities, news and sources.
- A story exposes its exact source news.
- A news item links to its original external article.
- A CVE exposes related stories/news and links to NVD/CVE.org.
- A MITRE technique links to MITRE ATT&CK.
- The UI clearly communicates the intelligence chain from news to risk.
- Typecheck, lint, build and smoke tests pass.
- Do not implement RAG, reports or alerts in this redesign.
