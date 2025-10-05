"""
TAG_DICT Extraction from nasa.txt
Parses the nasa.txt file to extract all unique tags from chunks
"""
import json
import re
from typing import Set, Dict, List
from pathlib import Path
import unicodedata
import logging

logger = logging.getLogger(__name__)


def normalize_term(term: str) -> str:
    """
    Normalize a term: lowercase, remove accents, stem basic forms
    """
    # Lowercase
    term = term.lower().strip()
    
    # Remove accents/tildes
    term = unicodedata.normalize('NFKD', term)
    term = ''.join([c for c in term if not unicodedata.combining(c)])
    
    # Basic stemming (remove common suffixes)
    # Simple rule-based for scientific terms
    if term.endswith('ies'):
        term = term[:-3] + 'y'
    elif term.endswith('es') and len(term) > 3:
        term = term[:-2]
    elif term.endswith('s') and len(term) > 3:
        term = term[:-1]
    
    return term


def extract_tags_from_nasa_txt(file_path: str = "contexts/nasa.txt") -> Dict[str, List[str]]:
    """
    Extract all unique tags from nasa.txt chunks and create TAG_DICT
    
    Returns:
        Dict mapping normalized terms to list of original variants
    """
    logger.info(f"📚 Extracting TAG_DICT from {file_path}")
    
    path = Path(file_path)
    if not path.exists():
        logger.error(f"❌ File not found: {file_path}")
        return {}
    
    content = path.read_text(encoding='utf-8')
    
    # Find all "tags": [...] blocks in the file
    # Pattern to match JSON arrays after "tags": 
    tag_pattern = r'"tags":\s*\[(.*?)\]'
    matches = re.findall(tag_pattern, content, re.DOTALL)
    
    # Parse all tags
    all_tags: Set[str] = set()
    for match in matches:
        # Extract individual tags from the array
        # Pattern: "tag_name"
        tags_in_block = re.findall(r'"([^"]+)"', match)
        all_tags.update(tags_in_block)
    
    logger.info(f"✅ Found {len(all_tags)} unique tags")
    
    # Create TAG_DICT: normalized -> [original variants]
    tag_dict: Dict[str, Set[str]] = {}
    
    for tag in all_tags:
        normalized = normalize_term(tag)
        if normalized not in tag_dict:
            tag_dict[normalized] = set()
        tag_dict[normalized].add(tag)
        # Also add normalized form
        tag_dict[normalized].add(normalized)
    
    # Convert sets to sorted lists
    tag_dict_final = {
        k: sorted(list(v)) for k, v in tag_dict.items()
    }
    
    # Sort by key for readability
    tag_dict_final = dict(sorted(tag_dict_final.items()))
    
    logger.info(f"✅ Created TAG_DICT with {len(tag_dict_final)} normalized terms")
    logger.info(f"   Example terms: {list(tag_dict_final.keys())[:10]}")
    
    return tag_dict_final


def save_tag_dict_to_json(tag_dict: Dict[str, List[str]], output_path: str = "app/services/rag/tag_dict_extracted.json"):
    """
    Save TAG_DICT to JSON file for inspection
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(tag_dict, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 TAG_DICT saved to {output_path}")


def get_expanded_terms(tag_dict: Dict[str, List[str]], query_term: str) -> List[str]:
    """
    Get all variants for a term from TAG_DICT
    """
    normalized = normalize_term(query_term)
    return tag_dict.get(normalized, [])


def expand_query_with_tag_dict(tag_dict: Dict[str, List[str]], query: str, max_terms: int = 50) -> List[str]:
    """
    Expand query using TAG_DICT
    
    Args:
        tag_dict: Extracted TAG_DICT
        query: User query
        max_terms: Maximum number of expansion terms
    
    Returns:
        List of expansion terms
    """
    query_lower = query.lower()
    query_words = re.findall(r'\b\w+\b', query_lower)
    
    # Match keys in TAG_DICT
    matched_expansions = []
    
    for word in query_words:
        normalized = normalize_term(word)
        if normalized in tag_dict:
            matched_expansions.extend(tag_dict[normalized])
    
    # Also check for multi-word matches
    for key in tag_dict.keys():
        if len(key.split()) > 1:  # Multi-word term
            if key in query_lower:
                matched_expansions.extend(tag_dict[key])
    
    # Deduplicate and limit
    unique_expansions = list(set(matched_expansions))
    return unique_expansions[:max_terms]


if __name__ == "__main__":
    # Extract TAG_DICT from nasa.txt
    logging.basicConfig(level=logging.INFO)
    
    tag_dict = extract_tags_from_nasa_txt("contexts/nasa.txt")
    
    # Save to JSON
    save_tag_dict_to_json(tag_dict)
    
    # Test expansion
    test_query = "How does microgravity affect bone density in mice?"
    expansions = expand_query_with_tag_dict(tag_dict, test_query)
    
    print(f"\n🧪 Test Query: {test_query}")
    print(f"📊 Expansions ({len(expansions)}): {expansions[:20]}")
