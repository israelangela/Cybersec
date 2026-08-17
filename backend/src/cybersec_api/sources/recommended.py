from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.models.source import Source

RECOMMENDED_SOURCES = (
    (
        "Dark Reading",
        "https://www.darkreading.com/rss.xml",
        "Enterprise security news and analysis",
        "1.70",
    ),
    (
        "SecurityWeek",
        "https://www.securityweek.com/feed/",
        "Cybersecurity news, incidents and research",
        "1.70",
    ),
    (
        "The Hacker News",
        "https://feeds.feedburner.com/TheHackersNews",
        "Threat, vulnerability and security news",
        "1.60",
    ),
    (
        "Krebs on Security",
        "https://krebsonsecurity.com/feed/",
        "Independent cybercrime and investigation reporting",
        "1.70",
    ),
    (
        "Google Security Blog",
        "https://security.googleblog.com/feeds/posts/default",
        "Security research and advisories from Google",
        "1.90",
    ),
    (
        "Cisco Talos Intelligence",
        "https://blog.talosintelligence.com/rss/",
        "Threat intelligence and vulnerability research",
        "1.90",
    ),
    (
        "Palo Alto Unit 42",
        "https://unit42.paloaltonetworks.com/feed/",
        "Incident response and threat research",
        "1.90",
    ),
    (
        "ESET WeLiveSecurity",
        "https://www.welivesecurity.com/en/rss/feed/",
        "Malware research and threat analysis",
        "1.70",
    ),
    (
        "Malwarebytes Labs",
        "https://www.malwarebytes.com/blog/feed/index.xml",
        "Malware, scams and threat research",
        "1.70",
    ),
    (
        "Microsoft Security Blog",
        "https://www.microsoft.com/en-us/security/blog/feed/",
        "Microsoft threat intelligence and defensive guidance",
        "1.90",
    ),
    (
        "PortSwigger Research",
        "https://portswigger.net/research/rss",
        "Web security research and techniques",
        "1.80",
    ),
    (
        "Schneier on Security",
        "https://www.schneier.com/feed/atom/",
        "Security analysis, policy and cryptography",
        "1.50",
    ),
    (
        "Cloudflare Blog",
        "https://blog.cloudflare.com/rss/",
        "Internet security, resilience and incident analysis",
        "1.60",
    ),
    (
        "SentinelOne Labs",
        "https://www.sentinelone.com/feed/",
        "Endpoint threats and malware research",
        "1.70",
    ),
    (
        "Check Point Research",
        "https://blog.checkpoint.com/feed/",
        "Threat campaigns and vulnerability intelligence",
        "1.70",
    ),
    (
        "Bitdefender Labs",
        "https://www.bitdefender.com/blog/api/rss/labs/",
        "Malware and threat research",
        "1.70",
    ),
    (
        "Security Affairs",
        "https://securityaffairs.com/feed",
        "Cybercrime, breaches and threat intelligence",
        "1.50",
    ),
    (
        "Ars Technica Security",
        "https://arstechnica.com/security/feed/",
        "Security news and technical reporting",
        "1.50",
    ),
    (
        "Help Net Security",
        "https://www.helpnetsecurity.com/feed/",
        "Enterprise security news and analysis",
        "1.50",
    ),
    (
        "The Register Security",
        "https://www.theregister.com/security/headlines.atom",
        "Security incidents, vulnerabilities and industry news",
        "1.50",
    ),
)


async def add_recommended_sources(session: AsyncSession) -> tuple[list[Source], int]:
    urls = [entry[1] for entry in RECOMMENDED_SOURCES]
    existing_urls = set(
        (await session.scalars(select(Source.url).where(Source.url.in_(urls)))).all()
    )

    for name, url, description, weight in RECOMMENDED_SOURCES:
        if url in existing_urls:
            continue
        session.add(
            Source(
                name=name,
                url=url,
                source_type="rss",
                description=description,
                weight=Decimal(weight),
                is_enabled=True,
            )
        )

    created = len(RECOMMENDED_SOURCES) - len(existing_urls)
    await session.commit()
    result = await session.scalars(
        select(Source).where(Source.url.in_(urls)).order_by(Source.name.asc())
    )
    return list(result.all()), created
