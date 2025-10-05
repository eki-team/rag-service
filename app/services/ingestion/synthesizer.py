"""
Chunk Synthesis Module
Generates bullets, key_terms, and claims for each chunk
"""

import re
from typing import List, Tuple
from collections import Counter
import spacy
from .models import ChunkSynthesis, Claim


class ChunkSynthesizer:
    """Generates synthesis metadata for chunks"""

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize synthesizer
        
        Args:
            spacy_model: spaCy model to use for NLP tasks
        """
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            # If model not installed, use blank English model
            print(f"⚠️  SpaCy model '{spacy_model}' not found. Using blank model.")
            self.nlp = spacy.blank("en")

    def synthesize_chunk(self, text: str) -> ChunkSynthesis:
        """
        Generate synthesis for a chunk
        
        Returns:
            ChunkSynthesis with bullets, key_terms, and claims
        """
        # Generate bullets (3-5 factual sentences)
        bullets = self._extract_bullets(text, min_count=3, max_count=5)
        
        # Extract key terms (5-10 domain-specific terms)
        key_terms = self._extract_key_terms(text, min_count=5, max_count=10)
        
        # Extract claims with evidence (1-3 verifiable claims)
        claims = self._extract_claims(text, min_count=1, max_count=3)
        
        return ChunkSynthesis(
            bullets=bullets,
            key_terms=key_terms,
            claims=claims
        )

    def _extract_bullets(self, text: str, min_count: int = 3, max_count: int = 5) -> List[str]:
        """
        Extract 3-5 factual, self-contained sentences as bullets
        
        Strategy:
        1. Split into sentences
        2. Filter short/incomplete sentences
        3. Prioritize sentences with numbers, measurements, results
        4. Return top N
        """
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        # Filter: must have at least 8 words
        valid_sentences = [s for s in sentences if len(s.split()) >= 8]
        
        # Score sentences (prioritize factual content)
        scored = []
        for sent in valid_sentences:
            score = 0
            lower_sent = sent.lower()
            
            # +1 for numbers/measurements
            if re.search(r'\d+', sent):
                score += 1
            
            # +1 for scientific indicators
            if any(word in lower_sent for word in ['observed', 'measured', 'found', 'showed', 'demonstrated', 'indicated']):
                score += 1
            
            # +1 for units
            if re.search(r'\d+\s*(g|mg|kg|m|cm|mm|s|h|min|%|°C)', sent):
                score += 1
            
            # -1 for questions or references
            if sent.strip().endswith('?') or re.search(r'\[\d+\]', sent):
                score -= 1
            
            scored.append((score, sent))
        
        # Sort by score and take top N
        scored.sort(key=lambda x: x[0], reverse=True)
        bullets = [sent for _, sent in scored[:max_count]]
        
        # Ensure we have at least min_count
        if len(bullets) < min_count:
            bullets = valid_sentences[:max_count]
        
        return bullets[:max_count]

    def _extract_key_terms(self, text: str, min_count: int = 5, max_count: int = 10) -> List[str]:
        """
        Extract 5-10 domain-specific key terms
        
        Strategy:
        1. Extract noun phrases and named entities
        2. Filter stopwords and common words
        3. Prioritize multi-word technical terms
        4. Return top N by frequency
        """
        doc = self.nlp(text)
        
        # Extract noun chunks and named entities
        terms = []
        
        # Noun chunks
        for chunk in doc.noun_chunks:
            term = chunk.text.lower().strip()
            # Filter: at least 3 chars, not all stopwords
            if len(term) >= 3 and not all(token.is_stop for token in chunk):
                terms.append(term)
        
        # Named entities (scientific terms)
        for ent in doc.ents:
            term = ent.text.lower().strip()
            if len(term) >= 3:
                terms.append(term)
        
        # Count frequencies
        term_counts = Counter(terms)
        
        # Get top N most common
        top_terms = [term for term, _ in term_counts.most_common(max_count)]
        
        # Ensure we have at least min_count
        if len(top_terms) < min_count:
            # Fallback: extract capitalized words (likely scientific terms)
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            top_terms.extend([t.lower() for t in capitalized[:max_count]])
            top_terms = list(dict.fromkeys(top_terms))  # Remove duplicates
        
        return top_terms[:max_count]

    def _extract_claims(self, text: str, min_count: int = 1, max_count: int = 3) -> List[Claim]:
        """
        Extract 1-3 verifiable claims with evidence spans
        
        Strategy:
        1. Find sentences with strong factual indicators
        2. Extract a short evidence span (10-30 words)
        3. Ensure evidence span exists in text
        """
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        claims = []
        
        # Patterns that indicate factual claims
        factual_patterns = [
            r'\b(observed|measured|found|showed|demonstrated|indicated|revealed)\b',
            r'\b(increase|decrease|reduction|elevation)\b.*\d+',
            r'\b(significant|notable|marked)\b.*\b(change|effect|difference)\b',
            r'\b(results?|data|findings?|evidence)\b.*\b(suggest|indicate|show)\b',
        ]
        
        for sent in sentences:
            lower_sent = sent.lower()
            
            # Check if sentence matches factual patterns
            if any(re.search(pattern, lower_sent) for pattern in factual_patterns):
                # Extract evidence span (first 10-30 words of sentence)
                words = sent.split()
                evidence_length = min(30, max(10, len(words) // 2))
                evidence_span = " ".join(words[:evidence_length])
                
                # Ensure evidence span exists in text (should always be true)
                if evidence_span in text:
                    claim = Claim(
                        claim=sent,
                        evidence_span=evidence_span
                    )
                    claims.append(claim)
                
                # Stop if we have enough
                if len(claims) >= max_count:
                    break
        
        # Ensure we have at least min_count
        if len(claims) < min_count and len(sentences) > 0:
            # Fallback: use first sentence as claim
            first_sent = sentences[0]
            words = first_sent.split()
            evidence_span = " ".join(words[:min(30, len(words))])
            
            if evidence_span in text:
                claims.append(Claim(
                    claim=first_sent,
                    evidence_span=evidence_span
                ))
        
        return claims[:max_count]


class SimpleSynthesizer:
    """
    Fallback synthesizer without spaCy (for resource-constrained environments)
    """

    def synthesize_chunk(self, text: str) -> ChunkSynthesis:
        """Generate basic synthesis without NLP library"""
        # Split by sentence endings
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) >= 40]
        
        # Bullets: first 3-5 sentences with numbers/measurements
        bullets = []
        for sent in sentences:
            if len(bullets) >= 5:
                break
            if re.search(r'\d+', sent):  # Prioritize sentences with numbers
                bullets.append(sent + ".")
        
        # Fallback: just use first 3-5 sentences
        if len(bullets) < 3:
            bullets = [s + "." for s in sentences[:5]]
        
        # Key terms: extract capitalized words
        key_terms = list(set(re.findall(r'\b[A-Z][a-z]+\b', text)))[:10]
        
        # Claims: first sentence with evidence
        claims = []
        if sentences:
            first_sent = sentences[0] + "."
            evidence = " ".join(first_sent.split()[:20])
            claims.append(Claim(claim=first_sent, evidence_span=evidence))
        
        return ChunkSynthesis(
            bullets=bullets[:5],
            key_terms=key_terms if key_terms else ["scientific", "study", "research"],
            claims=claims if claims else [
                Claim(claim="Study findings presented.", evidence_span="Study findings")
            ]
        )
