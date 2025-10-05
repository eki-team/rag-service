"""
Document Verification Module
Validates metadata, DOI, publication year, abstract, etc.
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

from .models import (
    ScientificDocument,
    DocumentChunk,
    VerificationCheck,
    ChunkVerification,
)


class DocumentVerifier:
    """Verifies document and chunk metadata"""

    # Regex patterns
    DOI_PATTERN = re.compile(r"^10\.\S+/\S+$")
    
    # Year constraints
    MIN_YEAR = 1900
    MAX_YEAR = datetime.now().year

    def __init__(self):
        self.current_year = datetime.now().year

    def verify_document(self, doc: ScientificDocument) -> Tuple[bool, List[str]]:
        """
        Verify document-level metadata
        Returns: (is_valid, warnings)
        """
        warnings = []
        checks = []

        # Check 1: Publication year consistency
        year_check = self._verify_year(doc.publication_year)
        checks.append(year_check)
        if not year_check.result:
            warnings.append(f"Invalid publication_year: {doc.publication_year}")

        # Check 2: DOI format
        doi = doc.metadata.article_metadata.doi
        doi_check = self._verify_doi(doi)
        checks.append(doi_check)
        if doi and not doi_check.result:
            warnings.append(f"Invalid DOI format: {doi}")

        # Check 3: Abstract length
        abstract_check = self._verify_abstract(doc.abstract)
        checks.append(abstract_check)
        if not abstract_check.result:
            warnings.append(f"Abstract out of range: {len(doc.abstract.split())} words")

        # Check 4: Title match (if we have metadata)
        title_check = self._verify_title_match(
            doc.metadata.article_metadata.title, doc.text
        )
        checks.append(title_check)

        # Check 5: Authors presence
        authors_check = VerificationCheck(
            name="authors-present",
            result=len(doc.metadata.article_metadata.authors) > 0
        )
        checks.append(authors_check)
        if not authors_check.result:
            warnings.append("No authors found")

        # Check 6: Source URL validity
        url_check = self._verify_url(doc.source_url)
        checks.append(url_check)
        if not url_check.result:
            warnings.append(f"Invalid source_url: {doc.source_url}")

        is_valid = all(check.result for check in checks)
        return is_valid, warnings

    def calculate_confidence(
        self, doc: ScientificDocument, checks: List[VerificationCheck]
    ) -> float:
        """
        Calculate verification confidence score (0-1)
        Heuristic based on multiple factors
        """
        confidence = 0.0

        # +0.2 if DOI valid
        if doc.metadata.article_metadata.doi and self.DOI_PATTERN.match(
            doc.metadata.article_metadata.doi
        ):
            confidence += 0.2

        # +0.2 if title match > 0.95 similarity
        title = doc.metadata.article_metadata.title
        if title and self._title_similarity(title, doc.text) > 0.95:
            confidence += 0.2

        # +0.2 if year validated
        if self._verify_year(doc.publication_year).result:
            confidence += 0.2

        # +0.2 if abstract in range
        if self._verify_abstract(doc.abstract).result:
            confidence += 0.2

        # +0.2 if authors ≥1 and source_url valid
        if (
            len(doc.metadata.article_metadata.authors) >= 1
            and self._verify_url(doc.source_url).result
        ):
            confidence += 0.2

        return min(confidence, 1.0)

    def verify_chunk(
        self,
        chunk: DocumentChunk,
        parent_doc: ScientificDocument
    ) -> ChunkVerification:
        """
        Verify chunk-level data
        """
        checks = []
        notes = []

        # Check 1: Section balance (not 80% references/tables)
        balance_check = self._verify_section_balance(chunk.text)
        checks.append(balance_check)
        if not balance_check.result:
            notes.append("Chunk is mostly references/tables")

        # Check 2: Synthesis claims have evidence
        claims_check = self._verify_claims(chunk)
        checks.append(claims_check)
        if not claims_check.result:
            notes.append("Some claims lack evidence spans")

        # Check 3: Missing abstract flag (only for first chunk)
        if chunk.chunk_index == 0 and not parent_doc.abstract:
            checks.append(VerificationCheck(name="abstract-missing", result=False))
            notes.append("abstract-missing")

        # Calculate confidence (same as doc-level for simplicity)
        confidence = self.calculate_confidence(parent_doc, checks)

        status = "passed" if all(check.result for check in checks) else "flagged"

        return ChunkVerification(
            status=status,
            checks=checks,
            confidence=confidence,
            notes=" | ".join(notes) if notes else ""
        )

    # ===== PRIVATE HELPERS =====

    def _verify_year(self, year: int | None) -> VerificationCheck:
        """Verify publication year is in valid range"""
        if year is None:
            return VerificationCheck(name="year-consistency", result=False)
        
        result = self.MIN_YEAR <= year <= self.MAX_YEAR
        return VerificationCheck(name="year-consistency", result=result)

    def _verify_doi(self, doi: str | None) -> VerificationCheck:
        """Verify DOI format (10.xxx/xxx)"""
        if not doi:
            return VerificationCheck(name="doi-format", result=True)  # Optional
        
        result = bool(self.DOI_PATTERN.match(doi))
        return VerificationCheck(name="doi-format", result=result)

    def _verify_abstract(self, abstract: str) -> VerificationCheck:
        """Verify abstract length (50-5000 words)"""
        if not abstract:
            return VerificationCheck(name="abstract-length", result=False)
        
        word_count = len(abstract.split())
        result = 50 <= word_count <= 5000
        return VerificationCheck(name="abstract-length", result=result)

    def _verify_title_match(self, title: str, doc_text: str) -> VerificationCheck:
        """Verify title appears in document text"""
        if not title:
            return VerificationCheck(name="title-match", result=False)
        
        # Simple substring check (normalized)
        normalized_title = self._normalize_text(title)
        normalized_text = self._normalize_text(doc_text[:500])  # Check first 500 chars
        
        result = normalized_title in normalized_text
        return VerificationCheck(name="title-match", result=result)

    def _verify_url(self, url: str) -> VerificationCheck:
        """Verify URL has valid scheme"""
        result = url.startswith(("http://", "https://"))
        return VerificationCheck(name="url-valid", result=result)

    def _verify_section_balance(self, text: str) -> VerificationCheck:
        """Verify chunk is not 80% references/tables"""
        lower_text = text.lower()
        
        # Count reference-like patterns
        ref_patterns = [
            r"\[\d+\]",  # [1], [23], etc.
            r"\bet al\.",
            r"\bdoi:",
            r"references",
            "bibliography",
        ]
        
        ref_count = sum(len(re.findall(p, lower_text)) for p in ref_patterns)
        total_words = len(text.split())
        
        if total_words == 0:
            return VerificationCheck(name="section-balance", result=False)
        
        # If more than 80% appears to be references
        ratio = ref_count / total_words
        result = ratio < 0.8
        
        return VerificationCheck(name="section-balance", result=result)

    def _verify_claims(self, chunk: DocumentChunk) -> VerificationCheck:
        """Verify all claims have evidence spans that exist in text"""
        for claim_obj in chunk.synthesis.claims:
            evidence = claim_obj.evidence_span
            # Check if evidence span exists in chunk text
            if evidence not in chunk.text:
                return VerificationCheck(name="claims-evidence", result=False)
        
        return VerificationCheck(name="claims-evidence", result=True)

    def _title_similarity(self, title: str, text: str) -> float:
        """Calculate similarity between title and document text"""
        normalized_title = self._normalize_text(title)
        normalized_text = self._normalize_text(text[:500])
        
        return SequenceMatcher(None, normalized_title, normalized_text).ratio()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison"""
        import unicodedata
        
        # NFKC normalization
        text = unicodedata.normalize("NFKC", text)
        # Lowercase
        text = text.lower()
        # Remove extra whitespace
        text = " ".join(text.split())
        
        return text
