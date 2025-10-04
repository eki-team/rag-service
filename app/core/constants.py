"""
NASA Biology RAG - Constants
Constantes para facets, secciones y prioridades.
"""

# Prioridad de secciones en papers (Results > Conclusion > Methods > Intro)
SECTION_PRIORITY = {
    "Results": 4,
    "Conclusion": 3,
    "Methods": 2,
    "Introduction": 1,
    "Abstract": 0,
}

# Nombres canónicos de secciones
SECTION_NAMES = [
    "Introduction",
    "Methods",
    "Results",
    "Conclusion",
    "Abstract",
    "Discussion",
]

# Facets disponibles para filtrado
AVAILABLE_FACETS = [
    "organism",
    "system",
    "mission_env",
    "exposure",
    "assay",
    "tissue",
    "year",
]

# Mapeo de organismos comunes
ORGANISM_ALIASES = {
    "mouse": "Mus musculus",
    "rat": "Rattus norvegicus",
    "arabidopsis": "Arabidopsis thaliana",
    "human": "Homo sapiens",
    "yeast": "Saccharomyces cerevisiae",
}

# Sistemas biológicos
BIOLOGICAL_SYSTEMS = [
    "human",
    "plant",
    "microbe",
    "rodent",
    "other",
]

# Entornos de misión
MISSION_ENVIRONMENTS = [
    "LEO",      # Low Earth Orbit
    "Lunar",
    "Martian",
    "ISS",
    "Analog",   # Simulación terrestre
    "Parabolic",
]

# Tipos de exposición
EXPOSURE_TYPES = [
    "microgravity",
    "radiation",
    "combined",
    "partial-gravity",
    "hypergravity",
]
