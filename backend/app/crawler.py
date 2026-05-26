from dataclasses import dataclass
from datetime import datetime
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CrawlRun, Document, Source


@dataclass
class CrawledDocument:
    title: str
    url: str
    summary: str = ""
    doc_type: str = "보도자료"
    category: str = ""
    tags: str = ""
    published_at: str = ""


DATE_PATTERN = re.compile(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})")


def normalize_space(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def extract_date(text: str) -> str:
    match = DATE_PATTERN.search(text)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def infer_doc_type(source: Source, title: str) -> str:
    text = f"{source.name} {title}"
    if "리콜" in text or "회수" in text:
        return "리콜"
    if "비교" in text or "품질" in text:
        return "비교정보"
    if "안전" in text or "주의" in text:
        return "안전주의"
    return "보도자료"


def build_document(source: Source, title: str, href: str, row_text: str, base_url: str) -> CrawledDocument | None:
    title = normalize_space(title)
    if len(title) < 6:
        return None
    if title in {"이전", "다음", "목록", "검색", "상세보기", "바로가기"}:
        return None

    url = urljoin(base_url, href)
    if not url.startswith("http"):
        return None

    doc_type = infer_doc_type(source, title)
    published_at = extract_date(row_text)
    return CrawledDocument(
        title=title[:280],
        url=url,
        summary=f"{source.name}에서 수집한 공식 소비자정보입니다. 상세 내용은 원문을 확인하세요.",
        doc_type=doc_type,
        category=source.source_type,
        tags=",".join([source.name, source.source_type, doc_type]),
        published_at=published_at,
    )


def parse_candidates(
    html: str,
    base_url: str,
    source: Source,
    *,
    row_selectors: tuple[str, ...],
    link_keywords: tuple[str, ...],
) -> list[CrawledDocument]:
    soup = BeautifulSoup(html, "html.parser")
    docs: list[CrawledDocument] = []
    seen: set[str] = set()

    rows = []
    for selector in row_selectors:
        rows.extend(soup.select(selector))
    if not rows:
        rows = list(soup.select("tr, li, article, div"))

    for row in rows:
        row_text = normalize_space(row.get_text(" ", strip=True))
        if len(row_text) < 8:
            continue
        for anchor in row.select("a[href]"):
            href = anchor.get("href", "")
            resolved = urljoin(base_url, href)
            if link_keywords and not any(keyword in resolved for keyword in link_keywords):
                continue
            if resolved in seen:
                continue
            item = build_document(source, anchor.get_text(" ", strip=True), href, row_text, base_url)
            if not item:
                continue
            seen.add(resolved)
            docs.append(item)
            if len(docs) >= 30:
                return docs

    return docs


def parse_consumer24(html: str, base_url: str, source: Source) -> list[CrawledDocument]:
    return parse_candidates(
        html,
        base_url,
        source,
        row_selectors=("tbody tr", ".board-list li", ".list li", ".bbs-list li"),
        link_keywords=("consumer.go.kr", "select", "Info", "BBS", "Recall"),
    )


def parse_kca(html: str, base_url: str, source: Source) -> list[CrawledDocument]:
    return parse_candidates(
        html,
        base_url,
        source,
        row_selectors=("tbody tr", ".board-list li", ".list li", ".gallery-list li"),
        link_keywords=("kca.go.kr", "view", "sub.do", "board", "repo/handle"),
    )


def parse_ftc(html: str, base_url: str, source: Source) -> list[CrawledDocument]:
    return parse_candidates(
        html,
        base_url,
        source,
        row_selectors=("tbody tr", ".board-list li", ".list li", ".bbs-list li"),
        link_keywords=("ftc.go.kr", "selectReport", "contents.do", "UserView", "board"),
    )


def parse_board(html: str, base_url: str, source: Source) -> list[CrawledDocument]:
    if "consumer.go.kr" in source.url:
        return parse_consumer24(html, base_url, source)
    if "kca.go.kr" in source.url:
        return parse_kca(html, base_url, source)
    if "ftc.go.kr" in source.url:
        return parse_ftc(html, base_url, source)
    return parse_candidates(
        html,
        base_url,
        source,
        row_selectors=("tbody tr", "li", "article"),
        link_keywords=(),
    )


async def crawl_source(db: Session, source: Source) -> int:
    run = CrawlRun(source_id=source.id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    inserted = 0
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(source.url, headers={"User-Agent": "honja-sallim-radar/0.1"})
            response.raise_for_status()

        for item in parse_board(response.text, source.url, source):
            db.add(
                Document(
                    source_id=source.id,
                    title=item.title,
                    summary=item.summary,
                    url=item.url,
                    doc_type=item.doc_type,
                    category=item.category,
                    tags=item.tags,
                    published_at=item.published_at,
                )
            )
            try:
                db.commit()
                inserted += 1
            except IntegrityError:
                db.rollback()

        run.status = "success"
        run.message = f"inserted={inserted}"
        run.inserted_count = inserted
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run.status = "failed"
        run.message = str(exc)
    finally:
        run.finished_at = datetime.utcnow()
        db.add(run)
        db.commit()

    return inserted


async def crawl_all_sources(db: Session) -> int:
    total = 0
    for source in db.query(Source).filter(Source.is_active.is_(True)).all():
        total += await crawl_source(db, source)
    return total
