import json
import datetime
from typing import List, Optional, Dict, Any
import os

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

from .config import settings

Base = declarative_base()


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    title = Column(String)
    description = Column(Text)
    url = Column(String)
    schema_json = Column(Text)
    raw_metadata_json = Column(Text)
    tags = Column(Text)
    last_updated = Column(DateTime)
    __table_args__ = (UniqueConstraint('source', 'source_id', name='_source_sourceid_uc'),)


class Preview(Base):
    __tablename__ = "previews"
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False)
    rows_json = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    dataset = relationship('Dataset')


def get_engine(db_path: str = None):
    db_path = db_path or settings.CATALOG_DB_PATH
    url = f"sqlite:///{os.path.abspath(db_path)}"
    return create_engine(url, connect_args={"check_same_thread": False})


engine = get_engine()
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def upsert_dataset(source: str, source_id: str, metadata: Dict[str, Any]) -> int:
    session = SessionLocal()
    try:
        ds = session.query(Dataset).filter_by(source=source, source_id=source_id).one_or_none()
        now = datetime.datetime.utcnow()
        if ds is None:
            ds = Dataset(source=source, source_id=source_id)
            session.add(ds)
        ds.title = metadata.get('title')
        ds.description = metadata.get('description')
        ds.url = metadata.get('source_url') or metadata.get('url')
        ds.schema_json = json.dumps(metadata.get('schema', {}))
        ds.raw_metadata_json = json.dumps(metadata.get('raw', {}))
        ds.tags = json.dumps(metadata.get('tags', []))
        ds.last_updated = now
        session.commit()
        return ds.id
    finally:
        session.close()


def get_datasets(limit: int = 50, offset: int = 0, q: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        query = session.query(Dataset)
        if source:
            query = query.filter(Dataset.source == source)
        if q:
            like = f"%{q}%"
            query = query.filter((Dataset.title.ilike(like)) | (Dataset.description.ilike(like)))
        rows = query.order_by(Dataset.id.desc()).offset(offset).limit(limit).all()
        results = []
        for r in rows:
            results.append({
                "id": r.id,
                "source": r.source,
                "source_id": r.source_id,
                "title": r.title,
                "description": r.description,
                "url": r.url,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "tags": json.loads(r.tags) if r.tags else [],
            })
        return results
    finally:
        session.close()


def get_dataset_by_id(dataset_id: int) -> Optional[Dict[str, Any]]:
    session = SessionLocal()
    try:
        r = session.query(Dataset).get(dataset_id)
        if r is None:
            return None
        return {
            "id": r.id,
            "source": r.source,
            "source_id": r.source_id,
            "title": r.title,
            "description": r.description,
            "url": r.url,
            "last_updated": r.last_updated.isoformat() if r.last_updated else None,
            "tags": json.loads(r.tags) if r.tags else [],
            "schema": json.loads(r.schema_json) if r.schema_json else {},
            "raw_metadata": json.loads(r.raw_metadata_json) if r.raw_metadata_json else {},
        }
    finally:
        session.close()


def save_preview(dataset_id: int, rows: List[Dict[str, Any]]):
    session = SessionLocal()
    try:
        p = Preview(dataset_id=dataset_id, rows_json=json.dumps(rows))
        session.add(p)
        session.commit()
        return p.id
    finally:
        session.close()


def get_preview(dataset_id: int, n: int = 10) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        p = session.query(Preview).filter(Preview.dataset_id == dataset_id).order_by(Preview.created_at.desc()).first()
        if p is None:
            return []
        rows = json.loads(p.rows_json)
        return rows[:n]
    finally:
        session.close()


if __name__ == '__main__':
    init_db()
    print("Initialized catalog.db at", settings.CATALOG_DB_PATH)
