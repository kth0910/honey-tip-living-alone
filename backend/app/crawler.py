from dataclasses import dataclass
import asyncio
from datetime import datetime
import re
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlparse, urlunparse

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
CONSUMER24_VIEW_PATTERN = re.compile(r"selectViewList\('([^']+)'")
MAX_BACKFILL_PAGES = 20
REQUEST_DELAY_SECONDS = 1.2
NOISE_TITLES = {
    "이전",
    "다음",
    "목록",
    "검색",
    "상세보기",
    "바로가기",
    "오늘 하루열지않기",
    "오늘 하루 열지않기",
    "나의사건처리",
    "판매유형별피해구제건수",
    "처리결과별피해구제건수",
}


def normalize_space(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def extract_date(text: str) -> str:
    match = DATE_PATTERN.search(text)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def with_query_param(url: str, key: str, value: int | str) -> str:
    parsed = urlparse(url)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params[key] = str(value)
    return urlunparse(parsed._replace(query=urlencode(params)))


def page_url_candidates(source: Source, page: int) -> list[str]:
    if page <= 1:
        return [source.url]

    if "consumer.go.kr" in source.url:
        if "selectInfoRptList.do" in source.url:
            list_url = with_query_param(source.url, "page", page)
            return [with_query_param(list_url, "row", 10)]
        return [
            with_query_param(source.url, "pageIndex", page),
            with_query_param(source.url, "page", page),
        ]
    if "kca.go.kr" in source.url:
        return [
            with_query_param(source.url, "page", page),
            with_query_param(source.url, "pageIndex", page),
        ]
    if "ftc.go.kr" in source.url:
        return [
            with_query_param(source.url, "pageIndex", page),
            with_query_param(source.url, "page", page),
        ]
    return [with_query_param(source.url, "page", page)]


def infer_doc_type(source: Source, title: str) -> str:
    text = f"{source.name} {title}"
    if "리콜" in text or "회수" in text:
        return "리콜"
    if "비교" in text or "품질" in text:
        return "비교정보"
    if "안전" in text or "주의" in text:
        return "안전주의"
    return "보도자료"


def is_noise_title(title: str) -> bool:
    title = normalize_space(title)
    return title in NOISE_TITLES or title.startswith("오늘 하루")


def build_document(source: Source, title: str, href: str, row_text: str, base_url: str) -> CrawledDocument | None:
    title = normalize_space(title)
    if len(title) < 6:
        return None
    if is_noise_title(title):
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
    if "selectInfoRptList.do" in source.url:
        return parse_consumer24_info_reports(html, base_url, source)

    return parse_candidates(
        html,
        base_url,
        source,
        row_selectors=("tbody tr", ".board-list li", ".list li", ".bbs-list li"),
        link_keywords=("consumer.go.kr", "select", "Info", "BBS", "Recall"),
    )


def consumer24_detail_url(base_url: str, article_id: str) -> str:
    detail_path = "/user/ftc/consumer/cnsmrBBS/79/selectInfoRptDetail.do"
    return f"{urljoin(base_url, detail_path)}?infoId={quote(article_id)}"


def extract_consumer24_article_id(value: str) -> str:
    match = CONSUMER24_VIEW_PATTERN.search(value)
    return match.group(1) if match else ""


def parse_consumer24_info_reports(html: str, base_url: str, source: Source) -> list[CrawledDocument]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.tbl.col.data")
    if not table:
        return []

    docs: list[CrawledDocument] = []
    seen: set[str] = set()
    for row in table.select("tbody tr"):
        cols = row.find_all("td", recursive=False)
        if len(cols) < 4:
            continue

        title_cell = row.select_one("td.title")
        anchor = title_cell.select_one("a[href]") if title_cell else None
        if not anchor:
            continue

        title_spans = [normalize_space(span.get_text(" ", strip=True)) for span in anchor.select("span")]
        title = next((value for value in title_spans if value and "desc" not in value), "")
        desc = ""
        desc_node = anchor.select_one(".desc")
        if desc_node:
            desc = normalize_space(desc_node.get_text(" ", strip=True))
        if not title:
            title = normalize_space(anchor.get_text(" ", strip=True).replace(desc, ""))
        if len(title) < 6 or is_noise_title(title):
            continue

        href = anchor.get("href", "")
        article_id = extract_consumer24_article_id(href)
        url = consumer24_detail_url(base_url, article_id) if article_id else urljoin(base_url, href)
        if url in seen:
            continue

        provider = normalize_space(cols[2].get_text(" ", strip=True))
        published_at = extract_date(cols[3].get_text(" ", strip=True))
        doc_type = "비교정보"
        tags = [source.name, source.source_type, doc_type]
        if provider:
            tags.append(provider)
        docs.append(
            CrawledDocument(
                title=title[:280],
                url=url,
                summary=(desc or f"{source.name}에서 수집한 공식 소비자 비교정보입니다. 상세 내용은 원문을 확인하세요.")[:700],
                doc_type=doc_type,
                category=source.source_type,
                tags=",".join(tags),
                published_at=published_at,
            )
        )
        seen.add(url)

    return docs


def parse_kca_smartconsumer_reports(html: str, base_url: str, source: Source) -> list[CrawledDocument]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.board.m_board")
    if not table:
        return []

    docs: list[CrawledDocument] = []
    seen: set[str] = set()
    for row in table.select("tbody tr"):
        anchor = row.select_one("td.title a[href]")
        if not anchor:
            continue

        title = normalize_space(anchor.get_text(" ", strip=True))
        if len(title) < 6 or is_noise_title(title):
            continue

        url = urljoin(base_url, anchor.get("href", ""))
        if url in seen or not is_kca_article_url(url):
            continue

        category_node = row.select_one("td.b_title2")
        author_node = row.select_one("td.b_write")
        date_node = row.select_one("td.b_date")
        category = normalize_space(category_node.get_text(" ", strip=True)) if category_node else source.source_type
        author = normalize_space(author_node.get_text(" ", strip=True)) if author_node else ""
        published_at = (
            extract_date(date_node.get_text(" ", strip=True))
            if date_node
            else extract_date(row.get_text(" ", strip=True))
        )
        doc_type = infer_doc_type(source, title)
        if source.source_type == "comparison" and doc_type == "보도자료":
            doc_type = "비교정보"
        summary = f"{source.name}에서 수집한 KCA보고서 {category} 자료입니다. 상세 내용은 원문을 확인하세요."
        if author:
            summary = f"{summary} 저자: {author}."
        tags = [source.name, source.source_type, doc_type, category]
        if author:
            tags.append(author)
        docs.append(
            CrawledDocument(
                title=title[:280],
                url=url,
                summary=summary[:700],
                doc_type=doc_type,
                category=category or source.source_type,
                tags=",".join(tag for tag in tags if tag),
                published_at=published_at,
            )
        )
        seen.add(url)

    return docs


def is_kca_article_url(url: str) -> bool:
    if "kca.go.kr" not in url:
        return False
    if "/search/" in url or "/odr/" in url or "home/main.do" in url:
        return False
    return (
        "mode=view" in url
        or "selectBbsNttView.do" in url
        or "/brd/" in url
        or "repo/handle" in url
        or "board" in url
    )


def parse_kca(html: str, base_url: str, source: Source) -> list[CrawledDocument]:
    if "smartconsumer/sub.do" in source.url and "menukey=7301" in source.url:
        return parse_kca_smartconsumer_reports(html, base_url, source)

    docs = parse_candidates(
        html,
        base_url,
        source,
        row_selectors=("tbody tr", ".board-list li", ".list li", ".gallery-list li"),
        link_keywords=("kca.go.kr", "view", "board", "repo/handle"),
    )
    return [doc for doc in docs if is_kca_article_url(doc.url) and not is_noise_title(doc.title)]


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


def save_crawled_documents(db: Session, source: Source, items: list[CrawledDocument]) -> int:
    inserted = 0
    for item in items:
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
    return inserted


async def crawl_source(db: Session, source: Source, *, backfill: bool = False, max_pages: int = 1) -> int:
    run = CrawlRun(source_id=source.id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    inserted = 0
    pages_scanned = 0
    try:
        page_limit = min(max(1, max_pages), MAX_BACKFILL_PAGES) if backfill else 1
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for page in range(1, page_limit + 1):
                page_items: list[CrawledDocument] = []
                last_error: Exception | None = None
                for url in page_url_candidates(source, page):
                    try:
                        response = await client.get(url, headers={"User-Agent": "honja-sallim-radar/0.1"})
                        response.raise_for_status()
                        page_items = parse_board(response.text, url, source)
                        if page_items:
                            break
                    except Exception as exc:  # noqa: BLE001
                        last_error = exc

                if not page_items:
                    if page == 1 and last_error:
                        raise last_error
                    break

                pages_scanned += 1
                inserted += save_crawled_documents(db, source, page_items)

                if page < page_limit:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)

        run.status = "success"
        run.message = f"inserted={inserted}; pages={pages_scanned}; backfill={backfill}"
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


async def crawl_all_sources(db: Session, *, backfill: bool = False, max_pages: int = 1) -> int:
    total = 0
    for source in db.query(Source).filter(Source.is_active.is_(True)).all():
        total += await crawl_source(db, source, backfill=backfill, max_pages=max_pages)
    return total
