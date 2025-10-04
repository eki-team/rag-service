"""
NASA Biology RAG - Prompts (GUIDED mode - DESHABILITADO)
Intents estructurados para queries complejas (comparaciones, outcomes).
Feature flag: NASA_GUIDED_ENABLED=false
"""

# TODO: Implementar guided mode cuando se habilite
# Intents posibles:
# - compare_exposures: Comparar efectos de microgravity vs radiation
# - outcomes_by_mission: Outcomes por tipo de misión (ISS/Lunar/etc)
# - temporal_analysis: Cambios a lo largo del tiempo
# - organism_comparison: Comparar respuestas entre especies

COMPARE_EXPOSURES_PROMPT = """
[GUIDED MODE - DISABLED]
Compare biological responses across different exposure conditions.
"""

OUTCOMES_BY_MISSION_PROMPT = """
[GUIDED MODE - DISABLED]
Analyze outcomes by mission environment.
"""

# Cuando se habilite, agregar:
# - Intent detection
# - Structured extraction
# - Multi-step reasoning
