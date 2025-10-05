# 🚀 Advanced RAG System - NASA Biology

## Sistema RAG Avanzado con Expansión de Query y Reranking Multi-Señal

Este sistema implementa un pipeline RAG sofisticado con las siguientes características:

---

## 🎯 Características Principales

### 1. **Query Expansion con TAG_DICT**
Expande automáticamente las consultas del usuario con términos relacionados, sinónimos y acrónimos.

**Ejemplo:**
```
Query original: "How does microgravity affect mouse bone?"

Términos detectados: microgravity, mouse, bone

Expansión automática:
- microgravity → weightlessness, zero gravity, μg, reduced gravity
- mouse → mice, mus musculus, murine, rodent  
- bone → skeletal, osseous, osteoblast, osteo

Query expandida: "How does microgravity affect mouse bone? weightlessness zero gravity mus musculus skeletal osseous..."
```

### 2. **Advanced Reranking con Múltiples Señales**

El reranker calcula un score final ponderado con 8 señales diferentes:

| Señal | Peso | Descripción |
|-------|------|-------------|
| **sim** | 0.36 | Similitud semántica (vector cosine) |
| **bm25** | 0.18 | Score BM25 léxico (si disponible) |
| **keyword_overlap** | 0.14 | Solapamiento query + expanded terms |
| **sec_boost** | 0.12 | Boost por sección (Abstract/Results > Methods/Intro) |
| **recency** | 0.08 | Preferencia por papers recientes |
| **authority** | 0.07 | Boost para fuentes confiables (.nasa.gov, Nature, etc.) |
| **length_fit** | 0.05 | Penaliza chunks muy cortos/largos |
| **duplicate_penalty** | -0.10 | Penaliza duplicados semánticos (>95% similares) |

**Fórmula:**
```
final_score = 0.36*sim + 0.18*bm25 + 0.14*keyword_overlap + 0.12*sec_boost 
              + 0.08*recency + 0.07*authority + 0.05*length_fit 
              - 0.10*duplicate_penalty
```

### 3. **Section Priority Boost**

El sistema da prioridad a secciones más relevantes:

| Sección | Boost |
|---------|-------|
| Abstract | +0.10 |
| Results | +0.10 |
| Discussion | +0.07 |
| Conclusion | +0.07 |
| Methods | +0.03 |
| Introduction | +0.03 |
| Appendix | 0.00 |
| References | 0.00 |

### 4. **Authority Domains**

Boost para fuentes confiables:

| Dominio | Boost |
|---------|-------|
| nasa.gov | +0.07 |
| nature.com | +0.06 |
| science.org | +0.06 |
| nih.gov | +0.05 |
| cell.com | +0.05 |
| plos.org | +0.04 |

### 5. **Diversity Enforcement**

- Máximo **2 chunks por documento**
- Intenta cubrir **≥3 fuentes distintas**
- Penaliza duplicados semánticos (similitud >95%)

### 6. **Síntesis Estricta con Citas Obligatorias**

El prompt de síntesis enforcea:

✅ **Citas obligatorias**: Cada claim debe tener `[N]`  
✅ **Faithfulness**: Solo información del contexto  
✅ **No hallucinations**: No knowledge externo  
✅ **Conflicts handling**: Señala desacuerdos entre fuentes  

**Ejemplo de respuesta:**
```
Microgravity exposure leads to significant bone density loss in mice [1][3]. 
RNA-seq analysis revealed upregulation of osteoclast-related genes [2]. 
While study [1] reports 10% bone loss after 30 days, study [3] found 15% 
loss under similar conditions. Limited evidence suggests that resistance 
exercise may mitigate these effects [4].
```

---

## 📊 Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. QUERY EXPANSION                                              │
│    - Detectar términos en TAG_DICT                              │
│    - Expandir con sinónimos y acrónimos                         │
│    - Construir query_expanded                                   │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. EMBEDDING                                                     │
│    - OpenAI text-embedding-3-small (1536 dims)                  │
│    - Query expandida → vector                                   │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. RETRIEVAL (TOP_K = 40)                                       │
│    - Vector search en MongoDB Atlas                             │
│    - Recuperar candidate set amplio                             │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. ADVANCED RERANKING                                           │
│    - Calcular 8 señales por chunk                               │
│    - Ordenar por final_score                                    │
│    - Tomar TOP_RERANK = 12                                      │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. DIVERSITY ENFORCEMENT                                        │
│    - Máx 2 chunks por documento                                 │
│    - Cubrir ≥3 fuentes                                          │
│    - Seleccionar TOP_SYNTHESIS = 6                              │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. CONTEXT BUILDING                                             │
│    - Consolidar chunks (max 4000 tokens)                        │
│    - Numerar pasajes [1], [2], ...                              │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. LLM SYNTHESIS (GPT-4o-mini)                                  │
│    - Prompt estricto con reglas de citación                     │
│    - System: "You MUST cite sources"                            │
│    - Temperature: 0.2 (determinístico)                          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. METRICS & RESPONSE                                           │
│    - Grounding ratio (% sentences con citas)                    │
│    - Citations con scoring signals                              │
│    - Section distribution                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuración

### Parámetros del Pipeline

Editables en `pipeline_advanced.py`:

```python
self.TOP_K = 40          # Candidate set inicial (retrieval)
self.TOP_RERANK = 12     # Pasajes para reranking detallado
self.TOP_SYNTHESIS = 6   # Pasajes finales para síntesis
```

### Pesos del Reranker

Editables en `reranker.py`:

```python
WEIGHTS = {
    "sim": 0.36,
    "bm25": 0.18,
    "keyword_overlap": 0.14,
    "sec_boost": 0.12,
    "recency": 0.08,
    "authority": 0.07,
    "length_fit": 0.05,
    "duplicate_penalty": -0.10,
}
```

### TAG_DICT

Expandible en `tag_dict.py`. Agregar nuevas entradas:

```python
TAG_DICT = {
    "nuevo_concepto": ["sinónimo1", "sinónimo2", "acrónimo"],
    ...
}
```

---

## 📝 Uso

### API Request

```json
POST /api/chat
{
  "query": "How does microgravity affect mouse bone density?",
  "filters": {
    "organism": ["Mus musculus"],
    "mission_env": ["ISS"]
  },
  "top_k": 8
}
```

### Response con Métricas Avanzadas

```json
{
  "answer": "Microgravity exposure leads to significant bone density loss...[1][3]",
  "citations": [
    {
      "source_id": "GLDS-123_chunk_5",
      "section": "Results",
      "snippet": "RNA-seq analysis revealed...",
      "doi": "10.1038/...",
      "similarity_score": 0.8234,
      "section_boost": 0.10,
      "final_score": 0.9145,
      "relevance_reason": "Sim: 0.823 | Sec: 0.100 | Keyword: 0.654 | Authority: 0.070 | Final: 0.915"
    }
  ],
  "metrics": {
    "latency_ms": 2345.67,
    "retrieved_k": 6,
    "grounded_ratio": 0.92,
    "section_distribution": {
      "Results": 3,
      "Discussion": 2,
      "Abstract": 1
    }
  }
}
```

---

## 🎓 TAG_DICT - Categorías

### Misiones y Ubicaciones
- ISS, LEO, Space Shuttle, Ground Control

### Condiciones de Exposición  
- Microgravity, Radiation, Spaceflight

### Organismos Modelo
- Mouse, Rat, Arabidopsis, Drosophila, C. elegans, Human

### Sistemas Biológicos
- Immune, Bone, Muscle, Cardiovascular, Neural, Metabolic

### Métodos y Técnicas
- RNA-seq, Proteomics, Genomics, Microscopy, PCR

### Fenómenos y Procesos
- Gene Expression, DNA Damage, Apoptosis, Inflammation

### Bases de Datos NASA
- OSDR, GLDS, Taskbook, LSL

### Conceptos Moleculares
- Protein, DNA, RNA, Pathway

**Total: 80+ entradas con 300+ términos expandidos**

---

## 📊 Métricas de Calidad

### Grounding Ratio
Porcentaje de sentences con citas `[N]`.

**Target: ≥80%**

```
Grounding = (sentences_con_citas / total_sentences)
```

### Section Distribution
Distribución de secciones en los chunks seleccionados.

**Ideal: Mayoría Abstract/Results/Discussion**

### Latency
Tiempo total del pipeline.

**Target: <5 segundos**

---

## 🔍 Debugging

### Ver señales del reranker

Cada citation incluye `relevance_reason` con todas las señales:

```json
"relevance_reason": "Sim: 0.823 | Sec: 0.100 | Keyword: 0.654 | Authority: 0.070 | Final: 0.915"
```

### Logs detallados

```
🔍 Original query: How does microgravity affect mouse bone?
🏷️  TAG_DICT matches: ['microgravity', 'mouse', 'bone']
📝 Expanded terms: ['weightlessness', 'zero gravity', 'mus musculus', 'skeletal', ...]
📚 Retrieved 40 initial candidates
🔄 Reranked to 6 chunks for synthesis
🤖 Generating answer with strict citations...
✅ Pipeline completed in 2345ms (grounding: 92.0%)
```

---

## 🚦 Políticas de Calidad

### Faithfulness
✅ Solo información del contexto  
❌ No external knowledge  
❌ No assumptions  

### Answer Relevancy
✅ Responder directamente la pregunta  
✅ Usar lenguaje técnico apropiado  
✅ Incluir detalles (especies, condiciones, mediciones)  

### Contextual Precision
✅ Priorizar Abstract, Results, Discussion  
✅ Usar fuentes confiables (.nasa.gov, journals reconocidos)  
✅ Preferir papers recientes cuando relevante  

### Contextual Recall
✅ Cubrir múltiples aspectos de la pregunta  
✅ Diversidad de fuentes (≥3 documentos)  
✅ Balance entre profundidad y cobertura  

---

## 🛠️ Próximos Pasos

### Mejoras Potenciales

1. **BM25 Integration**: Agregar búsqueda léxica con Elasticsearch
2. **Query Disambiguation**: Detectar queries ambiguas y pedir clarificación
3. **Multi-hop Reasoning**: Encadenar múltiples queries para respuestas complejas
4. **Feedback Loop**: Usar clicks/ratings para mejorar ranking
5. **Embeddings Fine-tuning**: Fine-tune embeddings en corpus NASA

### A/B Testing

Comparar con pipeline anterior:
- Grounding ratio
- Answer relevancy (RAGAS)
- Faithfulness (RAGAS)
- User satisfaction

---

## 📚 Referencias

- **RAGAS**: Framework de evaluación de RAG
- **TAG_DICT**: Inspirado en ontologías biomédicas (MeSH, Gene Ontology)
- **Reranking**: Basado en RankGPT y multi-stage retrieval
- **Citas estrictas**: Inspirado en WebGPT y GopherCite

---

## 📞 Soporte

Para dudas o mejoras, contactar al equipo de desarrollo.

**Versión**: 2.0.0 (Advanced Pipeline)  
**Última actualización**: Octubre 2025
