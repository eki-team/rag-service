"""
Document Chunking Module
Splits documents into chunks with overlap, respecting section boundaries
"""

import re
from typing import List, Tuple
import tiktoken


class ChunkProcessor:
    """Handles document chunking with smart boundaries"""

    def __init__(
        self,
        target_tokens: int = 1000,
        overlap_tokens: int = 100,
        min_chunk_tokens: int = 300,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize chunker
        
        Args:
            target_tokens: Target chunk size (900-1200 tokens recommended)
            overlap_tokens: Overlap between chunks (80-120 tokens recommended)
            min_chunk_tokens: Minimum chunk size (avoid micro-chunks)
            encoding_name: tiktoken encoding to use
        """
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.min_chunk_tokens = min_chunk_tokens
        
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            # Fallback: estimate 1 token ≈ 4 characters
            self.encoding = None

    def chunk_document(self, text: str) -> List[str]:
        """
        Split document into chunks with overlap
        
        Strategy:
        1. Detect section boundaries
        2. Split by sections first
        3. Further split large sections
        4. Merge tiny sections
        5. Add overlap between chunks
        
        Returns:
            List of chunk texts
        """
        # Normalize text first
        text = self._normalize_text(text)
        
        # Detect sections
        sections = self._detect_sections(text)
        
        # Process sections into chunks
        chunks = []
        for section_text in sections:
            section_chunks = self._chunk_section(section_text)
            chunks.extend(section_chunks)
        
        # Add overlap
        chunks = self._add_overlap(chunks)
        
        return chunks

    def _normalize_text(self, text: str) -> str:
        """Normalize text (unicode, whitespace, etc.)"""
        import unicodedata
        
        # NFKC normalization
        text = unicodedata.normalize("NFKC", text)
        
        # Remove excessive whitespace but preserve paragraph breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove navigation/legal boilerplate patterns
        boilerplate_patterns = [
            r'(?i)copyright\s+©.*?rights reserved',
            r'(?i)this article is distributed.*?license',
            r'(?i)click here for additional data file',
            r'(?i)supplementary materials?',
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        return text.strip()

    def _detect_sections(self, text: str) -> List[str]:
        """
        Detect document sections based on headers
        
        Common patterns:
        - Abstract
        - Introduction
        - Methods / Materials and Methods
        - Results
        - Discussion
        - Conclusion
        - References
        """
        # Section header patterns
        section_patterns = [
            r'^(?:#+\s+)?(?:Abstract|ABSTRACT)\s*$',
            r'^(?:#+\s+)?(?:Introduction|INTRODUCTION)\s*$',
            r'^(?:#+\s+)?(?:Methods?|METHODS?|Materials and Methods)\s*$',
            r'^(?:#+\s+)?(?:Results?|RESULTS?)\s*$',
            r'^(?:#+\s+)?(?:Discussion|DISCUSSION)\s*$',
            r'^(?:#+\s+)?(?:Conclusion|CONCLUSION)\s*$',
            r'^(?:#+\s+)?(?:References?|REFERENCES?|Bibliography)\s*$',
        ]
        
        # Find section boundaries
        lines = text.split('\n')
        section_indices = [0]  # Start of document
        
        for i, line in enumerate(lines):
            line = line.strip()
            for pattern in section_patterns:
                if re.match(pattern, line, re.MULTILINE):
                    section_indices.append(i)
                    break
        
        section_indices.append(len(lines))  # End of document
        
        # Extract sections
        sections = []
        for i in range(len(section_indices) - 1):
            start = section_indices[i]
            end = section_indices[i + 1]
            section_text = '\n'.join(lines[start:end]).strip()
            
            if section_text:
                sections.append(section_text)
        
        # If no sections detected, treat entire document as one section
        if not sections:
            sections = [text]
        
        return sections

    def _chunk_section(self, section_text: str) -> List[str]:
        """
        Chunk a single section, respecting sentence boundaries
        """
        # Get token count
        token_count = self._count_tokens(section_text)
        
        # If section fits in target, return as-is
        if token_count <= self.target_tokens:
            return [section_text]
        
        # Split by paragraphs first
        paragraphs = section_text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self._count_tokens(para)
            
            # If paragraph is too large, split by sentences
            if para_tokens > self.target_tokens:
                # Flush current chunk
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                
                # Split large paragraph
                sentences = self._split_sentences(para)
                for sent in sentences:
                    sent_tokens = self._count_tokens(sent)
                    
                    if current_tokens + sent_tokens > self.target_tokens:
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                        current_chunk = [sent]
                        current_tokens = sent_tokens
                    else:
                        current_chunk.append(sent)
                        current_tokens += sent_tokens
            
            # Regular paragraph
            elif current_tokens + para_tokens > self.target_tokens:
                # Flush current chunk
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Flush remaining
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """
        Add overlap between consecutive chunks
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk: no prepend, but append overlap from next
                overlapped.append(chunk)
            else:
                # Get overlap from previous chunk (last N tokens)
                prev_chunk = chunks[i - 1]
                overlap_text = self._get_last_n_tokens(prev_chunk, self.overlap_tokens)
                
                # Prepend overlap
                new_chunk = overlap_text + "\n\n" + chunk
                overlapped.append(new_chunk)
        
        return overlapped

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitter (can be improved with spaCy)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: estimate 1 token ≈ 4 characters
            return len(text) // 4

    def _get_last_n_tokens(self, text: str, n_tokens: int) -> str:
        """Get last N tokens from text"""
        if self.encoding:
            tokens = self.encoding.encode(text)
            if len(tokens) <= n_tokens:
                return text
            overlap_tokens = tokens[-n_tokens:]
            return self.encoding.decode(overlap_tokens)
        else:
            # Fallback: get last N*4 characters
            char_count = n_tokens * 4
            return text[-char_count:]
