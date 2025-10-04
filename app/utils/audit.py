"""
NASA Biology RAG - Audit Utils
Logging de retrieval y grounding.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logger para auditoría de retrieval y grounding"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
    
    def log_retrieval(self, query: str, chunks: list, filters: Dict[str, Any] = None):
        """Log de retrieval"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "query": query,
            "retrieved_count": len(chunks),
            "filters": filters,
            "chunks": [
                {
                    "source_id": c.get("source_id"),
                    "doi": c.get("doi"),
                    "section": c.get("section"),
                    "similarity": c.get("similarity"),
                }
                for c in chunks[:5]  # Solo top-5
            ],
        }
        
        log_file = self.log_dir / f"retrieval_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        logger.debug(f"📝 Logged retrieval: {query[:50]}...")
    
    def log_grounding(self, query: str, answer: str, citations: list):
        """Log de grounding (citas)"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "query": query,
            "answer_length": len(answer),
            "citation_count": len(citations),
            "citations": [c.source_id for c in citations],
        }
        
        log_file = self.log_dir / f"grounding_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        logger.debug(f"📝 Logged grounding: {len(citations)} citations")


# Singleton
_audit_logger: AuditLogger = None

def get_audit_logger() -> AuditLogger:
    """Get or create audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
