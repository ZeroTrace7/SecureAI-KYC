"""
Stage 8 — Audit Logger

Tamper-proof audit trail using SQLAlchemy + SQLite.
Every verification is logged with full signal data.
"""

import datetime
import json

from loguru import logger
from sqlalchemy import (Column, DateTime, Float, Integer, String, Text,
                        create_engine)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

Base = declarative_base()


class AuditRecord(Base):
    """Single verification audit record."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    document_type = Column(String(50), nullable=True)
    fraud_score = Column(Float, nullable=True)
    decision = Column(String(20), nullable=True)
    explanation = Column(Text, nullable=True)
    signals_json = Column(Text, nullable=True)  # Full signal dump
    filename = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)


# ── Database setup ──
_engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(_engine)
_SessionLocal = sessionmaker(bind=_engine)


def log_verification(result: dict, filename: str = None, ip_address: str = None) -> int:
    """
    Log a verification result to the audit database.

    Args:
        result: Full pipeline result dict.
        filename: Original uploaded filename.
        ip_address: Client IP address.

    Returns:
        Audit record ID.
    """
    session = _SessionLocal()
    try:
        record = AuditRecord(
            document_type=result.get("document_type"),
            fraud_score=result.get("fraud_score"),
            decision=result.get("decision"),
            explanation=result.get("explanation"),
            signals_json=json.dumps(result, default=str),
            filename=filename,
            ip_address=ip_address,
        )
        session.add(record)
        session.commit()
        audit_id = record.id
        logger.info(
            f"Audit: Logged verification #{audit_id} ({result.get('decision')})"
        )
        return audit_id
    except Exception as e:
        session.rollback()
        logger.error(f"Audit: Failed to log — {e}")
        return -1
    finally:
        session.close()


def get_audit_record(audit_id: int) -> dict | None:
    """Retrieve a single audit record by ID."""
    session = _SessionLocal()
    try:
        record = session.query(AuditRecord).filter_by(id=audit_id).first()
        if record:
            return {
                "id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "document_type": record.document_type,
                "fraud_score": record.fraud_score,
                "decision": record.decision,
                "explanation": record.explanation,
                "signals": (
                    json.loads(record.signals_json) if record.signals_json else {}
                ),
                "filename": record.filename,
            }
        return None
    finally:
        session.close()
