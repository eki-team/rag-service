"""
NASA Biology RAG - Chunk Schema
Modelo de datos para chunks de papers científicos.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Entity(BaseModel):
    """Entidad normalizada (organismo, gen, proceso)"""
    id: str
    type: str  # organism, gene, process, tissue, etc.
    name: str
    aliases: Optional[List[str]] = []


class Chunk(BaseModel):
    """
    Chunk de paper científico indexado en vector store.
    Compatible con Cosmos DB y pgvector.
    """
    # === Identificadores ===
    source_id: str = Field(..., description="ID único del chunk (paper_id + chunk_idx)")
    pk: str = Field(default="nasa", description="Partition key (orgId)")
    
    # === Metadata del paper ===
    title: str
    year: Optional[int] = None
    venue: Optional[str] = None  # journal o conference
    doi: Optional[str] = None
    osdr_id: Optional[str] = None  # NASA Open Science Data Repository ID
    
    # === Facets NASA ===
    organism: Optional[str] = None  # "Mus musculus", "Arabidopsis thaliana"
    system: Optional[str] = None    # "human", "plant", "microbe"
    mission_env: Optional[str] = None  # "LEO", "Lunar", "Martian", "Analog"
    exposure: Optional[str] = None     # "microgravity", "radiation", "combined"
    assay: Optional[str] = None        # "RNA-seq", "proteomics", "imaging"
    tissue: Optional[str] = None       # "muscle", "root", "bone"
    
    # === Sección del paper ===
    section: Optional[str] = None  # "Introduction", "Methods", "Results", "Conclusion"
    
    # === Contenido ===
    text: str = Field(..., description="Texto del chunk")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    
    # === Entidades extraídas ===
    entities: Optional[List[Entity]] = []
    
    # === URL/Source ===
    url: Optional[str] = None
    source_type: Optional[str] = "OSDR"  # OSDR, LSL, TASKBOOK
    
    # === Timestamps ===
    indexed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "GLDS-123_chunk_5",
                "pk": "nasa",
                "title": "Microgravity effects on immune response in mice",
                "year": 2023,
                "venue": "npj Microgravity",
                "doi": "10.1038/s41526-023-00123-4",
                "osdr_id": "GLDS-123",
                "organism": "Mus musculus",
                "system": "rodent",
                "mission_env": "ISS",
                "exposure": "microgravity",
                "assay": "RNA-seq",
                "tissue": "spleen",
                "section": "Results",
                "text": "RNA-seq analysis revealed significant upregulation of inflammatory genes...",
                "url": "https://osdr.nasa.gov/bio/repo/data/studies/GLDS-123",
                "source_type": "OSDR",
            }
        }
