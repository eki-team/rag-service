"""
Example usage of the Scientific Document Ingestion Pipeline
"""

from app.services.ingestion import IngestionPipeline, ingest_from_file


def example_basic_ingestion():
    """Basic example: ingest a single document"""
    
    # Sample document text (would come from scraper)
    raw_text = """
    # Effects of Microgravity on Bone Density in Mice
    
    Authors: John Smith, Jane Doe, Robert Johnson
    
    Published: 2023
    
    DOI: 10.1234/example.2023.001
    
    ## Abstract
    
    This study investigates the effects of prolonged microgravity exposure on bone density 
    in laboratory mice aboard the International Space Station. We observed a significant 
    reduction in bone mineral density (BMD) of approximately 15% over a 30-day period. 
    The findings suggest that microgravity-induced bone loss occurs rapidly and may have 
    implications for long-duration spaceflight missions. Our results indicate that 
    countermeasures such as mechanical loading or pharmacological interventions may be 
    necessary to mitigate bone loss in astronauts during extended space missions.
    
    ## Introduction
    
    Bone loss during spaceflight has been a concern since the early days of human space 
    exploration. Previous studies have shown that astronauts can lose 1-2% of bone mass 
    per month in microgravity conditions. Understanding the mechanisms underlying this 
    bone loss is crucial for developing effective countermeasures.
    
    ## Methods
    
    We conducted a 30-day spaceflight experiment aboard the ISS with 20 C57BL/6 mice 
    (10 flight, 10 ground controls). Bone density was measured using micro-CT scanning 
    before and after the mission. Blood samples were collected to analyze bone turnover 
    markers including CTX-I and P1NP.
    
    ## Results
    
    Flight animals showed a 15% reduction in femoral BMD compared to ground controls 
    (p < 0.001). Serum CTX-I levels were elevated by 40% in flight mice, indicating 
    increased bone resorption. P1NP levels showed no significant change, suggesting 
    that bone formation was not upregulated to compensate for increased resorption.
    
    ## Discussion
    
    Our findings demonstrate that microgravity rapidly induces bone loss in mice through 
    increased bone resorption without compensatory increases in bone formation. This 
    imbalance in bone remodeling could lead to significant skeletal deterioration during 
    long-duration missions. Future studies should investigate the molecular mechanisms 
    driving this imbalance and test potential countermeasures.
    
    ## Conclusion
    
    Microgravity exposure causes rapid bone loss in mice through uncoupled bone remodeling. 
    Countermeasures targeting bone resorption may be necessary to protect skeletal health 
    during spaceflight.
    
    ## References
    
    1. Lang T, et al. (2004) Cortical and trabecular bone mineral loss from the spine and 
       hip in long-duration spaceflight. J Bone Miner Res 19(6):1006-12. 
       DOI: 10.1359/JBMR.040307
    2. Smith SM, et al. (2012) Benefits for bone from resistance exercise and nutrition 
       in long-duration spaceflight. J Bone Miner Res 27(9):1896-906.
    """
    
    # Initialize pipeline
    pipeline = IngestionPipeline(use_spacy=False)  # Use simple synthesizer for demo
    
    # Ingest document
    result = pipeline.ingest_document(
        raw_text=raw_text,
        source_url="https://example.com/articles/microgravity-bone-density-2023",
        title="Effects of Microgravity on Bone Density in Mice",
        source_type="article",
        additional_metadata={
            "authors": ["John Smith", "Jane Doe", "Robert Johnson"],
            "doi_year": 2023,
        }
    )
    
    # Check result
    if result.success:
        print(f"✅ SUCCESS!")
        print(f"   Document PK: {result.document_pk}")
        print(f"   Chunks created: {result.chunks_created}")
        print(f"   Verification: {result.verification_status}")
        if result.warnings:
            print(f"   ⚠️  Warnings: {', '.join(result.warnings)}")
    else:
        print(f"❌ FAILED!")
        print(f"   Errors: {', '.join(result.errors)}")
    
    return result


def example_batch_ingestion():
    """Example: ingest multiple documents"""
    
    documents = [
        {
            "raw_text": "Sample document 1...",
            "source_url": "https://example.com/doc1",
            "title": "Document 1 Title",
            "source_type": "article",
        },
        {
            "raw_text": "Sample document 2...",
            "source_url": "https://example.com/doc2",
            "title": "Document 2 Title",
            "source_type": "preprint",
        },
    ]
    
    pipeline = IngestionPipeline(use_spacy=False)
    
    results = []
    for doc_data in documents:
        result = pipeline.ingest_document(
            raw_text=doc_data["raw_text"],
            source_url=doc_data["source_url"],
            title=doc_data["title"],
            source_type=doc_data["source_type"],
        )
        results.append(result)
        
        # Progress
        status = "✅" if result.success else "❌"
        print(f"{status} {doc_data['title']}: {result.document_pk or 'FAILED'}")
    
    # Summary
    successful = sum(1 for r in results if r.success)
    print(f"\n📊 Batch Summary: {successful}/{len(results)} successful")
    
    return results


def example_query_documents():
    """Example: query ingested documents"""
    from app.services.ingestion import get_documents_collection, get_chunks_collection
    
    # Get collections
    docs_col = get_documents_collection()
    chunks_col = get_chunks_collection()
    
    # Query 1: Find all documents from 2023
    docs_2023 = docs_col.find({"publication_year": 2023})
    print(f"📚 Documents from 2023: {docs_col.count_documents({'publication_year': 2023})}")
    
    # Query 2: Find all flagged chunks
    flagged_chunks = chunks_col.find({"verification.status": "flagged"})
    print(f"⚠️  Flagged chunks: {chunks_col.count_documents({'verification.status': 'flagged'})}")
    
    # Query 3: Find documents by category
    space_docs = docs_col.find({"metadata.category": "space"})
    print(f"🚀 Space-related documents: {docs_col.count_documents({'metadata.category': 'space'})}")
    
    # Query 4: Get a specific document with its chunks
    doc = docs_col.find_one({}, sort=[("created_at", -1)])  # Most recent
    if doc:
        print(f"\n📄 Latest document: {doc['metadata']['article_metadata']['title']}")
        print(f"   PK: {doc['pk']}")
        print(f"   Chunks: {doc['total_chunks']}")
        print(f"   Year: {doc['publication_year']}")
        print(f"   Category: {doc['metadata']['category']}")
        print(f"   Tags: {', '.join(doc['metadata']['tags'][:5])}")
        
        # Get first chunk
        chunk = chunks_col.find_one({"pk": f"{doc['pk']}-0"})
        if chunk:
            print(f"\n   First chunk synthesis:")
            print(f"   - Bullets: {len(chunk['synthesis']['bullets'])}")
            print(f"   - Key terms: {', '.join(chunk['synthesis']['key_terms'][:3])}")
            print(f"   - Claims: {len(chunk['synthesis']['claims'])}")


if __name__ == "__main__":
    print("=" * 60)
    print("Scientific Document Ingestion Pipeline - Examples")
    print("=" * 60)
    
    print("\n1️⃣  Basic Ingestion Example")
    print("-" * 60)
    result = example_basic_ingestion()
    
    print("\n\n2️⃣  Query Documents Example")
    print("-" * 60)
    if result.success:
        example_query_documents()
    else:
        print("⚠️  Skipping (ingestion failed)")
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
