from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.types import JSON
import datetime
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


class EnrichedProspect(Base):
    __tablename__ = "enriched_prospects"
    id = Column(Integer, primary_key=True)
    source_row_id = Column(String, index=True)
    primary_email_domain = Column(String)
    dns_mx = Column(JSON)
    dns_txt = Column(JSON)
    dns_ns = Column(JSON)
    dns_score = Column(Integer)
    probe_in_progress = Column(Boolean, default=False)
    phones_summary = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    emails = relationship("EmailCandidate", back_populates="prospect")
    phones = relationship("Phone", back_populates="prospect")


class EmailCandidate(Base):
    __tablename__ = "email_candidates"
    id = Column(Integer, primary_key=True)
    prospect_id = Column(Integer, ForeignKey("enriched_prospects.id"), index=True)
    email = Column(String, index=True)
    pattern = Column(String)
    score = Column(String)
    status = Column(String)
    source_signals = Column(JSON)
    prospect = relationship("EnrichedProspect", back_populates="emails")


class Phone(Base):
    __tablename__ = "phones"
    id = Column(Integer, primary_key=True)
    prospect_id = Column(Integer, ForeignKey("enriched_prospects.id"), index=True)
    raw = Column(String)
    normalized = Column(String)
    valid = Column(String)
    type = Column(String)
    carrier_guess = Column(String)
    prospect = relationship("EnrichedProspect", back_populates="phones")


class ProbeLock(Base):
    __tablename__ = "probe_locks"
    id = Column(Integer, primary_key=True)
    # Optional name for generic locks (e.g., 'reprobe_global')
    name = Column(String, index=True, nullable=True)
    # Optional prospect-specific lock
    prospect_id = Column(Integer, nullable=True)
    owner = Column(String, nullable=True)
    locked_at = Column(DateTime, default=datetime.datetime.utcnow)
    __table_args__ = (UniqueConstraint('name', name='uix_probe_locks_name'), UniqueConstraint('prospect_id', name='uix_probe_locks_prospect'),)


def acquire_lock(session, name: str = None, prospect_id: int = None, owner: str = None) -> bool:
    """Try to acquire a named or prospect-specific lock.

    Returns True if lock acquired, False if already held.
    """
    lock = ProbeLock(name=name, prospect_id=prospect_id, owner=owner)
    session.add(lock)
    try:
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False


def release_lock(session, name: str = None, prospect_id: int = None, owner: str = None) -> None:
    q = session.query(ProbeLock)
    if name:
        q = q.filter(ProbeLock.name == name)
    if prospect_id is not None:
        q = q.filter(ProbeLock.prospect_id == prospect_id)
    try:
        for l in q.all():
            session.delete(l)
        session.commit()
    except Exception:
        session.rollback()


class ProviderMetric(Base):
    __tablename__ = "provider_metrics"
    id = Column(Integer, primary_key=True)
    provider = Column(String, index=True, unique=True)
    probes = Column(Integer, default=0)
    valid = Column(Integer, default=0)
    invalid = Column(Integer, default=0)
    codes = Column(JSON)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


def upsert_provider_metrics(session, metrics: dict):
    """Persist aggregated provider metrics into provider_metrics table.

    metrics: { provider: {probes, valid, invalid, codes: {code: count}} }
    This will insert or update rows incrementally.
    """
    for provider, vals in (metrics or {}).items():
        row = session.query(ProviderMetric).filter(ProviderMetric.provider == provider).one_or_none()
        if not row:
            row = ProviderMetric(provider=provider, probes=0, valid=0, invalid=0, codes={})
            session.add(row)
        # increment counters
        row.probes = (row.probes or 0) + int(vals.get('probes', 0))
        row.valid = (row.valid or 0) + int(vals.get('valid', 0))
        row.invalid = (row.invalid or 0) + int(vals.get('invalid', 0))
        # merge codes
        codes = row.codes or {}
        for code, cnt in (vals.get('codes') or {}).items():
            codes[code] = codes.get(code, 0) + int(cnt)
        row.codes = codes
        try:
            session.commit()
        except Exception:
            session.rollback()


def create_tables(db_url: str):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_url: str):
    # Create a new engine per call to avoid cross-thread engine state issues in simple scripts.
    # Use expire_on_commit=False so ORM instances remain usable after commit in worker threads.
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    return Session()
