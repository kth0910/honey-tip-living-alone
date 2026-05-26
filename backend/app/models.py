from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    url: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(40), default="board")
    crawl_interval: Mapped[str] = mapped_column(String(40), default="daily")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="source")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("url", name="uq_documents_url"),
        Index("ix_documents_search", "title", "summary", "category", "doc_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(Text)
    doc_type: Mapped[str] = mapped_column(String(40), index=True)
    category: Mapped[str] = mapped_column(String(80), default="")
    tags: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[str] = mapped_column(String(20), default="")
    collected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    source: Mapped[Source] = relationship(back_populates="documents")


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="running")
    message: Mapped[str] = mapped_column(Text, default="")
    inserted_count: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
