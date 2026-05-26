from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crawler import crawl_all_sources, crawl_source
from app.database import get_db, init_db
from app.models import Source
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


@app.post("/api/admin/crawl")
async def crawl(
    x_crawl_token: Annotated[str | None, Header()] = None,
    source_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    assert_admin_token(x_crawl_token)
    if source_id:
        source = db.get(Source, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="source not found")
        inserted = await crawl_source(db, source)
    else:
        inserted = await crawl_all_sources(db)
    return {"status": "done", "inserted": inserted}
