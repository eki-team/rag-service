"""
Main Ingestion Pipeline
Orchestrates document processing, chunking, synthesis, verification, and persistence
"""

from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter
import re

from .models import (
    ScientificDocument,
    DocumentChunk,
    ArticleMetadata,
    DocumentMetadata,
    IngestionResult,
)
from .document_processor import DocumentProcessor
from .chunk_processor import ChunkProcessor
from .synthesizer import ChunkSynthesizer, SimpleSynthesizer
from .verifier import DocumentVerifier
from .mongo_config import get_documents_collection, get_chunks_collection


class IngestionPipeline:
    """Main pipeline for scientific document ingestion"""

    def __init__(
        self,
        use_spacy: bool = True,
        target_chunk_tokens: int = 1000,
        overlap_tokens: int = 100,
    ):
        """
        Initialize ingestion pipeline
        
        Args:
            use_spacy: Whether to use spaCy for synthesis (requires spaCy installed)
            target_chunk_tokens: Target chunk size in tokens
            overlap_tokens: Overlap between chunks in tokens
        """
        self.doc_processor = DocumentProcessor()
        self.chunk_processor = ChunkProcessor(
            target_tokens=target_chunk_tokens,
            overlap_tokens=overlap_tokens
        )
        
        # Use spaCy synthesizer if available, otherwise fallback
        if use_spacy:
            try:
                self.synthesizer = ChunkSynthesizer()
            except Exception:
                print("⚠️  SpaCy not available. Using simple synthesizer.")
                self.synthesizer = SimpleSynthesizer()
        else:
            self.synthesizer = SimpleSynthesizer()
        
        self.verifier = DocumentVerifier()

    def ingest_document(
        self,
        raw_text: str,
        source_url: str,
        title: str,
        source_type: str = "article",
        additional_metadata: Optional[Dict] = None,
    ) -> IngestionResult:
        """
        Main ingestion method
        
        Steps:
        1. Extract metadata (year, abstract, authors, DOI, etc.)
        2. Verify metadata quality
        3. Create document record
        4. Chunk document
        5. Synthesize each chunk
        6. Verify each chunk
        7. Persist to MongoDB
        
        Args:
            raw_text: Full document text
            source_url: Source URL
            title: Document title
            source_type: Type of document (article, preprint, etc.)
            additional_metadata: Extra metadata from scraper
            
        Returns:
            IngestionResult with success status and details
        """
        result = IngestionResult(success=False)
        additional_metadata = additional_metadata or {}
        
        try:
            # === STEP 1: Extract metadata ===
            print(f"📄 Processing document: {title[:50]}...")
            
            abstract = self.doc_processor.extract_abstract(raw_text)
            if not abstract:
                result.warnings.append("abstract-missing")
            
            publication_year = self.doc_processor.extract_publication_year(
                raw_text, additional_metadata
            )
            if not publication_year:
                result.warnings.append("publication_year-missing")
            
            authors = self.doc_processor.extract_authors(raw_text, additional_metadata)
            if not authors:
                result.warnings.append("authors-missing")
            
            doi = self.doc_processor.extract_doi(raw_text)
            pmc_id = self.doc_processor.extract_pmc_id(raw_text, source_url)
            
            references = self.doc_processor.extract_references(raw_text)
            
            # === STEP 2: Create document PK ===
            docs_col = get_documents_collection()
            existing_pks = set(doc["pk"] for doc in docs_col.find({}, {"pk": 1}))
            doc_pk = self.doc_processor.create_document_pk(title, existing_pks)
            
            # === STEP 3: Check for duplicates ===
            duplicate = self._check_duplicate(doc_pk, doi, pmc_id, title)
            if duplicate:
                result.errors.append(f"Duplicate document found: {duplicate}")
                return result
            
            # === STEP 4: Build document record ===
            statistics = self.doc_processor.calculate_statistics(
                raw_text, abstract, authors, references
            )
            
            # Extract tags from text (top-8 n-grams)
            tags = self._extract_tags(raw_text, abstract)
            
            # Infer category
            category = self.doc_processor.infer_category(raw_text, tags)
            
            # Build article metadata
            article_meta = ArticleMetadata(
                url=source_url,
                title=title,
                authors=authors,
                scraped_at=datetime.utcnow(),
                pmc_id=pmc_id,
                doi=doi,
                statistics=statistics,
            )
            
            # Build document metadata
            doc_metadata = DocumentMetadata(
                article_metadata=article_meta,
                references=references,
                char_count=len(raw_text),
                word_count=len(raw_text.split()),
                sentences_count=len(re.split(r'[.!?]+', raw_text)),
                tags=tags,
                category=category,
            )
            
            # Create document
            doc = ScientificDocument(
                pk=doc_pk,
                text=raw_text[:2000],  # Store title + authors + abstract + first lines
                abstract=abstract,
                publication_year=publication_year,
                source_type=source_type,
                source_url=source_url,
                metadata=doc_metadata,
            )
            
            # === STEP 5: Verify document ===
            is_valid, warnings = self.verifier.verify_document(doc)
            result.warnings.extend(warnings)
            
            if not is_valid:
                result.verification_status = "flagged"
            
            # === STEP 6: Chunk document ===
            print(f"✂️  Chunking document...")
            chunk_texts = self.chunk_processor.chunk_document(raw_text)
            doc.total_chunks = len(chunk_texts)
            
            # === STEP 7: Process chunks ===
            print(f"🔍 Processing {len(chunk_texts)} chunks...")
            chunks = []
            
            for idx, chunk_text in enumerate(chunk_texts):
                # Synthesize
                synthesis = self.synthesizer.synthesize_chunk(chunk_text)
                
                # Verify
                chunk = DocumentChunk(
                    pk=f"{doc_pk}-{idx}",
                    chunk_index=idx,
                    total_chunks=len(chunk_texts),
                    text=chunk_text,
                    synthesis=synthesis,
                    verification=self.verifier.verify_chunk(
                        DocumentChunk(
                            pk=f"{doc_pk}-{idx}",
                            chunk_index=idx,
                            total_chunks=len(chunk_texts),
                            text=chunk_text,
                            synthesis=synthesis,
                            verification=None,
                        ),
                        doc
                    ),
                    section="unknown",  # Section detection not available in DB per requirements
                )
                
                chunks.append(chunk)
            
            # === STEP 8: Persist to MongoDB ===
            print(f"💾 Saving to MongoDB...")
            
            # Save document
            doc_dict = doc.model_dump(by_alias=True)
            docs_col.insert_one(doc_dict)
            
            # Save chunks
            chunks_col = get_chunks_collection()
            chunk_dicts = [c.model_dump(by_alias=True) for c in chunks]
            chunks_col.insert_many(chunk_dicts)
            
            # === STEP 9: Return result ===
            result.success = True
            result.document_pk = doc_pk
            result.chunks_created = len(chunks)
            result.verification_status = (
                "flagged" if not is_valid else "passed"
            )
            
            print(f"✅ Ingestion complete: {doc_pk} ({len(chunks)} chunks)")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Ingestion failed: {str(e)}")
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return result

    def _check_duplicate(
        self,
        pk: str,
        doi: Optional[str],
        pmc_id: Optional[str],
        title: str
    ) -> Optional[str]:
        """
        Check for duplicate documents
        
        Returns:
            Duplicate identifier if found, None otherwise
        """
        docs_col = get_documents_collection()
        
        # Check by PK
        if docs_col.find_one({"pk": pk}):
            return f"pk:{pk}"
        
        # Check by DOI
        if doi:
            if docs_col.find_one({"metadata.article_metadata.doi": doi}):
                return f"doi:{doi}"
        
        # Check by PMC ID
        if pmc_id:
            if docs_col.find_one({"metadata.article_metadata.pmc_id": pmc_id}):
                return f"pmc_id:{pmc_id}"
        
        # Check by title similarity (threshold 0.97)
        # This would require fetching all titles and comparing, which is expensive
        # Skip for now (can be added with better indexing)
        
        return None

    def _extract_tags(self, text: str, abstract: str) -> List[str]:
        """
        Extract top-8 n-grams as tags (without stopwords)
        
        Returns:
            List of up to 8 tags
        """
        # Combine text sources
        combined = (abstract or "") + " " + text[:2000]
        combined = combined.lower()
        
        # Remove stopwords (simple list)
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "can", "this", "that", "these",
            "those", "it", "its", "we", "our", "they", "their"
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', combined)
        words = [w for w in words if w not in stopwords]
        
        # Count frequencies
        word_counts = Counter(words)
        
        # Get top 8
        tags = [word for word, _ in word_counts.most_common(8)]
        
        return tags


# === CONVENIENCE FUNCTIONS ===

def ingest_from_dict(data: Dict) -> IngestionResult:
    """
    Ingest document from dictionary
    
    Required keys: raw_text, source_url, title
    Optional keys: source_type, metadata
    """
    pipeline = IngestionPipeline()
    
    return pipeline.ingest_document(
        raw_text=data["raw_text"],
        source_url=data["source_url"],
        title=data["title"],
        source_type=data.get("source_type", "article"),
        additional_metadata=data.get("metadata", {}),
    )


def ingest_from_file(file_path: str, source_url: str, title: str) -> IngestionResult:
    """
    Ingest document from text file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    pipeline = IngestionPipeline()
    
    return pipeline.ingest_document(
        raw_text=raw_text,
        source_url=source_url,
        title=title,
    )
