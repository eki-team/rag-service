"""
Document Processor Module
Extracts metadata, abstract, publication year, etc. from raw documents
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import hashlib


class DocumentProcessor:
    """Processes raw documents and extracts metadata"""

    def __init__(self):
        self.current_year = datetime.now().year

    def create_document_pk(self, title: str, existing_pks: set = None) -> str:
        """
        Create unique document PK from title
        
        Strategy:
        1. Slugify title (lowercase, ascii-safe, hyphens)
        2. Check for collisions
        3. Add hash suffix if collision detected
        
        Args:
            title: Document title
            existing_pks: Set of existing PKs to check for collisions
            
        Returns:
            Unique PK string
        """
        # Slugify
        slug = self._slugify(title)
        
        # Check collision
        if existing_pks and slug in existing_pks:
            # Add short hash suffix
            hash_suffix = hashlib.md5(title.encode()).hexdigest()[:6]
            slug = f"{slug}-{hash_suffix}"
        
        return slug

    def extract_publication_year(
        self,
        raw_text: str,
        metadata: Dict,
        doi: Optional[str] = None
    ) -> Optional[int]:
        """
        Extract publication year from multiple sources
        
        Priority:
        1. DOI metadata
        2. Explicit publication date in text
        3. Copyright year
        4. Date patterns in text
        
        Returns:
            Publication year (YYYY) or None if not found
        """
        # Try DOI metadata first (if provided externally)
        if doi and 'doi_year' in metadata:
            year = metadata.get('doi_year')
            if self._validate_year(year):
                return int(year)
        
        # Try explicit publication patterns
        pub_patterns = [
            r'Published:?\s+(\d{4})',
            r'Publication\s+date:?\s+(\d{4})',
            r'©\s*(\d{4})',
            r'Copyright\s+©?\s*(\d{4})',
        ]
        
        for pattern in pub_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if self._validate_year(year):
                    return year
        
        # Try date patterns (YYYY-MM-DD, DD/MM/YYYY, etc.)
        date_patterns = [
            r'\b(19\d{2}|20\d{2})-\d{2}-\d{2}\b',  # ISO format
            r'\b\d{1,2}/\d{1,2}/(19\d{2}|20\d{2})\b',  # US format
            r'\b(19\d{2}|20\d{2})\b',  # Just year
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, raw_text)
            if match:
                year_str = match.group(1) if match.lastindex else match.group(0)
                year = int(year_str)
                if self._validate_year(year):
                    return year
        
        return None

    def extract_abstract(self, raw_text: str) -> str:
        """
        Extract abstract from document text
        
        Strategy:
        1. Find "Abstract" section
        2. Extract text until next section or ~500 words
        3. Clean up (remove headers, legal notes)
        """
        # Pattern to find abstract section
        abstract_patterns = [
            r'(?i)^##?\s*Abstract\s*\n+(.*?)(?=^##?\s*\w+|\Z)',
            r'(?i)^Abstract\s*\n+(.*?)(?=^[A-Z][a-z]+\s*\n|\Z)',
            r'(?i)Abstract[:\s]+(.*?)(?=\n\n[A-Z][a-z]+:|\Z)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, raw_text, re.MULTILINE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                
                # Clean up
                abstract = self._clean_abstract(abstract)
                
                # Validate length (50-5000 words)
                word_count = len(abstract.split())
                if 50 <= word_count <= 5000:
                    return abstract
        
        return ""

    def extract_authors(self, raw_text: str, metadata: Dict) -> List[str]:
        """
        Extract author names from text or metadata
        
        Returns:
            List of "FirstName LastName" strings
        """
        authors = []
        
        # Try metadata first
        if 'authors' in metadata and isinstance(metadata['authors'], list):
            return metadata['authors']
        
        # Try to extract from text (common patterns)
        # Pattern: "Authors: Name1, Name2, Name3"
        author_patterns = [
            r'Authors?:\s*((?:[A-Z][a-z]+\s+[A-Z][a-z]+(?:,\s*)?)+)',
            r'By\s+((?:[A-Z][a-z]+\s+[A-Z][a-z]+(?:,\s*)?)+)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, raw_text)
            if match:
                author_str = match.group(1)
                # Split by comma
                authors = [a.strip() for a in author_str.split(',')]
                if authors:
                    return authors
        
        return authors

    def extract_doi(self, raw_text: str) -> Optional[str]:
        """
        Extract DOI from text
        
        Returns:
            DOI string (10.xxxx/xxxx) or None
        """
        doi_pattern = r'\b(10\.\S+/\S+)\b'
        match = re.search(doi_pattern, raw_text)
        
        if match:
            doi = match.group(1)
            # Clean up trailing punctuation
            doi = re.sub(r'[.,;]$', '', doi)
            return doi
        
        return None

    def extract_pmc_id(self, raw_text: str, source_url: str = "") -> Optional[str]:
        """
        Extract PMC ID from text or URL
        
        Returns:
            PMC ID (e.g., "PMC1234567") or None
        """
        # Check URL first
        if 'pmc' in source_url.lower():
            pmc_match = re.search(r'PMC\d+', source_url, re.IGNORECASE)
            if pmc_match:
                return pmc_match.group(0).upper()
        
        # Check text
        pmc_pattern = r'\b(PMC\d+)\b'
        match = re.search(pmc_pattern, raw_text, re.IGNORECASE)
        
        if match:
            return match.group(1).upper()
        
        return None

    def calculate_statistics(
        self,
        raw_text: str,
        abstract: str,
        authors: List[str],
        references: List[Dict]
    ) -> Dict:
        """
        Calculate document statistics
        
        Returns:
            Dict with total_authors, abstract_words, total_words, references_count, sections_found
        """
        # Detect sections
        sections = self._detect_sections(raw_text)
        
        # Word counts
        total_words = len(raw_text.split())
        abstract_words = len(abstract.split()) if abstract else 0
        
        return {
            "total_authors": len(authors),
            "abstract_words": abstract_words,
            "total_words": total_words,
            "references_count": len(references),
            "sections_found": sections,
        }

    def extract_references(self, raw_text: str) -> List[Dict]:
        """
        Extract references from text
        
        Returns:
            List of reference dicts with title, year, doi, source_url
        """
        references = []
        
        # Find references section
        ref_pattern = r'(?i)^##?\s*References?\s*\n+(.*?)(?=^##?\s*\w+|\Z)'
        match = re.search(ref_pattern, raw_text, re.MULTILINE | re.DOTALL)
        
        if not match:
            return references
        
        ref_text = match.group(1)
        
        # Split by lines (each line is a reference)
        ref_lines = ref_text.split('\n')
        
        for line in ref_lines:
            line = line.strip()
            if not line or len(line) < 20:
                continue
            
            # Extract year
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', line)
            year = int(year_match.group(1)) if year_match else None
            
            # Extract DOI
            doi_match = re.search(r'\b(10\.\S+/\S+)\b', line)
            doi = doi_match.group(1) if doi_match else None
            
            # Extract URL
            url_match = re.search(r'https?://\S+', line)
            source_url = url_match.group(0) if url_match else None
            
            # Title is the line itself (cleaned)
            title = re.sub(r'\[\d+\]', '', line).strip()
            title = re.sub(r'https?://\S+', '', title).strip()
            
            references.append({
                "title": title[:200],  # Limit length
                "year": year,
                "doi": doi,
                "source_url": source_url,
            })
        
        return references[:100]  # Limit to 100 references

    def infer_category(self, text: str, tags: List[str]) -> str:
        """
        Infer document category from text and tags
        
        Simple heuristic-based categorization
        """
        text_lower = text.lower()
        tags_lower = [t.lower() for t in tags]
        
        # Category keywords
        categories = {
            "space": ["space", "spaceflight", "microgravity", "iss", "orbital", "astronaut"],
            "biomedical": ["medical", "clinical", "patient", "disease", "therapy", "drug"],
            "molecular": ["molecular", "gene", "protein", "dna", "rna", "genome"],
            "neuroscience": ["brain", "neural", "cognitive", "neuron", "synapse"],
            "immunology": ["immune", "antibody", "antigen", "lymphocyte", "cytokine"],
            "physics": ["physics", "quantum", "particle", "energy", "force"],
            "chemistry": ["chemical", "reaction", "molecule", "compound", "synthesis"],
            "biology": ["biology", "cell", "organism", "species", "evolution"],
        }
        
        # Count matches
        category_scores = {}
        for cat, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in text_lower or kw in tags_lower)
            if score > 0:
                category_scores[cat] = score
        
        # Return top category or "other"
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return "other"

    # ===== PRIVATE HELPERS =====

    def _slugify(self, text: str) -> str:
        """Convert text to slug (lowercase, hyphens, ascii-safe)"""
        import unicodedata
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Lowercase and replace spaces with hyphens
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        
        # Trim hyphens
        text = text.strip('-')
        
        # Limit length
        return text[:100]

    def _validate_year(self, year: Optional[int]) -> bool:
        """Validate year is in reasonable range"""
        if year is None:
            return False
        return 1900 <= year <= self.current_year

    def _clean_abstract(self, abstract: str) -> str:
        """Clean abstract text"""
        # Remove common boilerplate
        abstract = re.sub(r'(?i)This article is distributed.*?license\.?', '', abstract)
        abstract = re.sub(r'(?i)©.*?All rights reserved\.?', '', abstract)
        
        # Remove excessive whitespace
        abstract = ' '.join(abstract.split())
        
        return abstract.strip()

    def _detect_sections(self, text: str) -> List[str]:
        """Detect section names in document"""
        section_patterns = [
            r'^##?\s*(Abstract|Introduction|Methods?|Results?|Discussion|Conclusion|References?)',
        ]
        
        sections = []
        for pattern in section_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            sections.extend([m.capitalize() for m in matches])
        
        return list(set(sections))
