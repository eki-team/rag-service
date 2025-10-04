"""
NASA Biology RAG - Text Utils
Splitters, normalizadores, text processing.
"""
import re
from typing import List


def normalize_whitespace(text: str) -> str:
    """Normalizar espacios en blanco"""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """Split texto en oraciones (simple)"""
    # Simple split por . ! ?
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def extract_top_sentences(text: str, n: int = 3) -> List[str]:
    """Extraer las primeras N oraciones"""
    sentences = split_into_sentences(text)
    return sentences[:n]


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncar texto a max_chars"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def normalize_organism_name(name: str) -> str:
    """Normalizar nombre de organismo (e.g., mouse -> Mus musculus)"""
    from app.core.constants import ORGANISM_ALIASES
    normalized = name.strip().lower()
    return ORGANISM_ALIASES.get(normalized, name)
