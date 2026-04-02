"""
Blockchain-Inspired Document Hash Ledger

Implements a tamper-proof hash chain for document verification:

  1. Document Hashing: SHA-256 content hash + perceptual hash (pHash)
     for visual similarity matching.
  2. Chain Structure: Each block stores prev_hash, document_hash, phash,
     timestamp — forming an immutable linked chain.
  3. Verification: Compare new documents against the ledger to detect
     re-submissions of known documents (genuine or forged).

SQLite-backed (same database as audit log) for zero-dependency deployment.
"""

import datetime
import hashlib
import json

from loguru import logger
from sqlalchemy import (
    Column, DateTime, Integer, String, Text,
    create_engine, desc,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

Base = declarative_base()


class BlockchainBlock(Base):
    """Single block in the document hash chain."""

    __tablename__ = "blockchain_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    document_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    perceptual_hash = Column(String(64), nullable=True)  # pHash hex
    prev_block_hash = Column(String(64), nullable=False)  # chain link
    block_hash = Column(String(64), nullable=False, unique=True)  # this block's hash
    filename = Column(String(255), nullable=True)
    document_type = Column(String(50), nullable=True)
    fraud_decision = Column(String(20), nullable=True)
    nonce = Column(Integer, default=0)
    metadata_json = Column(Text, nullable=True)


# ── Database setup ──
_engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(_engine)
_SessionLocal = sessionmaker(bind=_engine)

# Genesis block hash (fixed)
GENESIS_HASH = "0" * 64


def _compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of file contents."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Blockchain: Cannot hash file — {e}")
        return ""


def _compute_perceptual_hash(file_path: str) -> str:
    """Compute perceptual hash (pHash) for visual similarity."""
    try:
        import imagehash
        from PIL import Image

        img = Image.open(file_path)
        phash = imagehash.phash(img, hash_size=16)
        return str(phash)
    except ImportError:
        logger.warning("Blockchain: imagehash not installed, skipping pHash")
        return ""
    except Exception as e:
        logger.warning(f"Blockchain: pHash computation failed — {e}")
        return ""


def _compute_block_hash(
    prev_hash: str,
    doc_hash: str,
    timestamp: str,
    nonce: int = 0,
) -> str:
    """Compute the hash of a block (chain integrity)."""
    block_data = f"{prev_hash}{doc_hash}{timestamp}{nonce}"
    return hashlib.sha256(block_data.encode()).hexdigest()


def _get_latest_block_hash() -> str:
    """Get the hash of the most recent block in the chain."""
    session = _SessionLocal()
    try:
        latest = (
            session.query(BlockchainBlock)
            .order_by(desc(BlockchainBlock.id))
            .first()
        )
        if latest:
            return latest.block_hash
        return GENESIS_HASH
    finally:
        session.close()


def register_document(
    file_path: str,
    filename: str = None,
    document_type: str = None,
    fraud_decision: str = None,
) -> dict:
    """
    Register a document in the blockchain ledger.

    Creates a new block with the document's content hash and
    perceptual hash, linked to the previous block.

    Returns:
        dict with: block_id, document_hash, perceptual_hash, block_hash,
                   registered (bool)
    """
    doc_hash = _compute_file_hash(file_path)
    if not doc_hash:
        return {
            "registered": False,
            "error": "Cannot compute document hash",
        }

    phash = _compute_perceptual_hash(file_path)
    prev_hash = _get_latest_block_hash()
    now = datetime.datetime.utcnow()
    timestamp_str = now.isoformat()

    block_hash = _compute_block_hash(prev_hash, doc_hash, timestamp_str)

    session = _SessionLocal()
    try:
        block = BlockchainBlock(
            timestamp=now,
            document_hash=doc_hash,
            perceptual_hash=phash,
            prev_block_hash=prev_hash,
            block_hash=block_hash,
            filename=filename,
            document_type=document_type,
            fraud_decision=fraud_decision,
            metadata_json=json.dumps({
                "phash": phash,
                "registered_at": timestamp_str,
            }),
        )
        session.add(block)
        session.commit()
        block_id = block.id

        logger.info(
            f"Blockchain: Registered document #{block_id} "
            f"hash={doc_hash[:16]}... block={block_hash[:16]}..."
        )

        return {
            "registered": True,
            "block_id": block_id,
            "document_hash": doc_hash,
            "perceptual_hash": phash,
            "block_hash": block_hash,
            "prev_block_hash": prev_hash,
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Blockchain: Registration failed — {e}")
        return {"registered": False, "error": str(e)}
    finally:
        session.close()


def verify_document(file_path: str) -> dict:
    """
    Verify a document against the blockchain ledger.

    Checks:
    1. Exact hash match (identical document previously seen)
    2. Perceptual similarity (visually similar document)
    3. Chain integrity validation

    Returns:
        dict with: hash_verified, previously_seen, similar_documents,
                   chain_valid, document_hash, match_details
    """
    doc_hash = _compute_file_hash(file_path)
    phash = _compute_perceptual_hash(file_path)

    result = {
        "hash_verified": False,
        "previously_seen": False,
        "exact_match": None,
        "similar_count": 0,
        "chain_valid": True,
        "document_hash": doc_hash,
        "perceptual_hash": phash,
        "blockchain_score": 0.0,
        "total_blocks": 0,
        "match_details": [],
    }

    if not doc_hash:
        result["match_details"].append("Cannot compute document hash")
        return result

    session = _SessionLocal()
    try:
        # ── Check total chain size ──
        total_blocks = session.query(BlockchainBlock).count()
        result["total_blocks"] = total_blocks

        # ── 1. Exact hash match ──
        exact_match = (
            session.query(BlockchainBlock)
            .filter_by(document_hash=doc_hash)
            .first()
        )

        if exact_match:
            result["previously_seen"] = True
            result["hash_verified"] = True
            result["exact_match"] = {
                "block_id": exact_match.id,
                "registered_at": exact_match.timestamp.isoformat(),
                "filename": exact_match.filename,
                "fraud_decision": exact_match.fraud_decision,
            }

            # If previously flagged as forged, high score
            if exact_match.fraud_decision in ("FORGED", "REJECTED"):
                result["blockchain_score"] = 0.9
                result["match_details"].append(
                    f"⚠ ALERT: This exact document was previously submitted "
                    f"and flagged as {exact_match.fraud_decision} "
                    f"(Block #{exact_match.id}, {exact_match.timestamp.isoformat()})"
                )
            else:
                result["blockchain_score"] = 0.0
                result["match_details"].append(
                    f"Document previously verified as {exact_match.fraud_decision or 'UNKNOWN'} "
                    f"(Block #{exact_match.id})"
                )

        # ── 2. Perceptual similarity check ──
        if phash and not exact_match:
            try:
                import imagehash

                query_phash = imagehash.hex_to_hash(phash)
                all_blocks = (
                    session.query(BlockchainBlock)
                    .filter(BlockchainBlock.perceptual_hash.isnot(None))
                    .filter(BlockchainBlock.perceptual_hash != "")
                    .all()
                )

                similar = []
                for block in all_blocks:
                    try:
                        block_phash = imagehash.hex_to_hash(block.perceptual_hash)
                        distance = query_phash - block_phash
                        # pHash distance < 15 = visually very similar
                        if distance < 15:
                            similar.append({
                                "block_id": block.id,
                                "distance": distance,
                                "filename": block.filename,
                                "fraud_decision": block.fraud_decision,
                            })
                    except Exception:
                        continue

                result["similar_count"] = len(similar)
                if similar:
                    result["previously_seen"] = True
                    result["match_details"].append(
                        f"Found {len(similar)} visually similar document(s) in ledger"
                    )
                    # If similar to a known forged document, moderate suspicion
                    for s in similar:
                        if s["fraud_decision"] in ("FORGED", "REJECTED"):
                            result["blockchain_score"] = max(
                                result["blockchain_score"], 0.6
                            )
                            result["match_details"].append(
                                f"Similar to previously forged document "
                                f"(Block #{s['block_id']}, distance={s['distance']})"
                            )

            except ImportError:
                pass  # imagehash not available, skip similarity

        # ── 3. Chain integrity validation ──
        if total_blocks > 0:
            blocks = (
                session.query(BlockchainBlock)
                .order_by(BlockchainBlock.id)
                .all()
            )
            chain_valid = True
            prev_hash = GENESIS_HASH

            for block in blocks:
                if block.prev_block_hash != prev_hash:
                    chain_valid = False
                    result["match_details"].append(
                        f"Chain integrity BROKEN at Block #{block.id}"
                    )
                    break
                prev_hash = block.block_hash

            result["chain_valid"] = chain_valid

        if not result["previously_seen"]:
            result["match_details"].append("First-time document — no prior record in ledger")

        logger.info(
            f"Blockchain: verified={result['hash_verified']} "
            f"seen={result['previously_seen']} "
            f"chain_ok={result['chain_valid']} "
            f"blocks={total_blocks}"
        )

        return result

    except Exception as e:
        logger.error(f"Blockchain: Verification error — {e}")
        result["match_details"].append(f"Verification error: {e}")
        return result
    finally:
        session.close()
