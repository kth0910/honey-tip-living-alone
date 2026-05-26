from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Document, Source


def list_sources(db: Session) -> list[Source]:
    return list(db.scalars(select(Source).order_by(Source.name)).all())


def search_documents(
    db: Session,
    query: str = "",
    doc_type: str = "",
    source_id: int | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[Document]:
    stmt = select(Document).join(Document.source)

    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Document.title.ilike(pattern),
                Document.summary.ilike(pattern),
                Document.category.ilike(pattern),
                Document.tags.ilike(pattern),
                Source.name.ilike(pattern),
            )
        )

    if doc_type and doc_type != "전체":
        stmt = stmt.where(Document.doc_type == doc_type)

    if source_id:
        stmt = stmt.where(Document.source_id == source_id)

    stmt = stmt.order_by(Document.collected_at.desc(), Document.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())
