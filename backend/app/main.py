from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crawler import crawl_all_sources, crawl_source
from app.database import get_db, init_db
from app.models import Document, Source
from app.repository import list_sources, search_documents
from app.seed import seed_database

settings = get_settings()
app = FastAPI(title="혼자살림 레이더 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.post("/api/admin/seed")
def seed(
    x_crawl_token: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if settings.app_env != "local":
        assert_admin_token(x_crawl_token)
    seed_database(db)
    return {"status": "seeded"}


@app.get("/api/sources")
def sources(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "sourceType": source.source_type,
            "crawlInterval": source.crawl_interval,
            "isActive": source.is_active,
        }
        for source in list_sources(db)
    ]


@app.get("/api/documents")
def documents(
    db: Session = Depends(get_db),
    query: str = "",
    doc_type: str = Query("", alias="type"),
    source_id: int | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "summary": doc.summary,
            "url": doc.url,
            "type": doc.doc_type,
            "category": doc.category,
            "tags": [tag for tag in doc.tags.split(",") if tag],
            "publishedAt": doc.published_at,
            "collectedAt": doc.collected_at.date().isoformat(),
            "source": doc.source.name,
        }
        for doc in search_documents(db, query=query, doc_type=doc_type, source_id=source_id, limit=limit, offset=offset)
    ]


def assert_admin_token(token: str | None) -> None:
    if token != settings.crawl_admin_token:
        raise HTTPException(status_code=401, detail="invalid admin token")


@app.post("/api/admin/prune")
def prune_bad_documents(
    x_crawl_token: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    assert_admin_token(x_crawl_token)
    bad_titles = [
        "오늘 하루열지않기",
        "오늘 하루 열지않기",
        "나의사건처리",
        "판매유형별피해구제건수",
        "처리결과별피해구제건수",
    ]
    bad_ids = [
        doc_id
        for (doc_id,) in db.query(Document.id)
        .join(Document.source)
        .filter(
            or_(
                Document.title.in_(bad_titles),
                Document.title.like("오늘 하루%"),
                Document.url.like("%/home/main.do?page=%"),
                Document.url.like("%/odr/%"),
                Document.url.like("%/search/%"),
            )
        )
        .all()
    ]
    if bad_ids:
        db.query(Document).filter(Document.id.in_(bad_ids)).delete(synchronize_session=False)
        db.commit()
    return {"status": "pruned", "deleted": len(bad_ids)}


@app.post("/api/admin/crawl")
async def crawl(
    x_crawl_token: Annotated[str | None, Header()] = None,
    source_id: int | None = None,
    backfill: bool = False,
    max_pages: int = Query(1, ge=1, le=20),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    assert_admin_token(x_crawl_token)
    if source_id:
        source = db.get(Source, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="source not found")
        inserted = await crawl_source(db, source, backfill=backfill, max_pages=max_pages)
    else:
        inserted = await crawl_all_sources(db, backfill=backfill, max_pages=max_pages)
    return {"status": "done", "inserted": inserted, "backfill": str(backfill), "maxPages": max_pages}
