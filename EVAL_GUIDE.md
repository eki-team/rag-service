# 🧪 NASA RAG Evaluator - Guía de Uso

## 📋 Descripción

**Evaluador automático** del sistema RAG de biología espacial NASA usando:
- **RAGAS**: answer_relevancy, faithfulness, context_precision, context_recall, context_relevancy
- **LangChain LLM-as-Judge**: bias, toxicity
- **Custom metrics**: grounded_ratio (cobertura de citas [N])

---

## 🚀 Quick Start

### 1. Instalar dependencias

```bash
pip install -r requirements_eval.txt
```

### 2. Configurar variables de entorno

Asegúrate de que `.env` tenga tu `OPENAI_API_KEY` (necesaria para RAGAS y LLM-as-Judge):

```bash
OPENAI_API_KEY=sk-...
```

### 3. Iniciar el servidor RAG

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Ejecutar evaluación

```bash
python eval_rag_nasa.py
```

---

## 📊 Métricas Evaluadas

### RAGAS (0-1, mayor = mejor)

| Métrica | Descripción | Umbral |
|---------|-------------|--------|
| **answer_relevancy** | Relevancia de la respuesta a la pregunta | ≥ 0.8 |
| **faithfulness** | Fidelidad al contexto (sin alucinaciones) | ≥ 0.8 |
| **context_precision** | Precisión del contexto recuperado | ≥ 0.7 |
| **context_recall** | Completitud del contexto recuperado | ≥ 0.7 |

### Derivadas

| Métrica | Fórmula | Umbral |
|---------|---------|--------|
| **hallucination** | `1 - faithfulness` | ≤ 0.2 |

### LLM-as-Judge (0-1, mayor = mejor)

| Métrica | Descripción | Umbral |
|---------|-------------|--------|
| **bias** | Ausencia de sesgos/estereotipos | ≥ 0.9 |
| **toxicity** | Ausencia de lenguaje ofensivo | ≥ 0.95 |

### Custom

| Métrica | Descripción | Umbral |
|---------|-------------|--------|
| **grounded_ratio** | % oraciones con citas [N] | ≥ 0.8 |
| **citations_count** | Nº total de [N] en respuesta | - |

---

## 📁 Salidas

### 1. JSON Report (`eval_results_<timestamp>.json`)

```json
{
  "timestamp": "20250105_143022",
  "dataset_size": 8,
  "endpoint": "http://127.0.0.1:8000/api/chat",
  "top_k": 8,
  "aggregates": {
    "latency_ms_avg": 2341.5,
    "grounded_ratio_avg": 0.7234,
    "answer_relevancy_avg": 0.8512,
    "faithfulness_avg": 0.8923,
    "hallucination_avg": 0.1077,
    "bias_avg": 0.9500,
    "toxicity_avg": 1.0000
  },
  "per_query": [
    {
      "query": "What are the effects of microgravity on bone density?",
      "tags_aplicados": ["bone", "microgravity", "skeletal", "weightlessness"],
      "latency_ms": 2150.3,
      "retrieved_k": 8,
      "grounded_ratio": 0.7500,
      "citations_count": 12,
      "answer_relevancy": 0.8723,
      "faithfulness": 0.9012,
      "context_precision": 0.8500,
      "context_recall": 0.8234,
      "context_relevancy": 0.8912,
      "hallucination": 0.0988,
      "bias": 1.0000,
      "toxicity": 1.0000,
      "notas": "✓ All metrics passed"
    }
  ]
}
```

### 2. CSV Report (`eval_rag_nasa.csv`)

Columnas:
- `query`: Pregunta evaluada
- `tags_aplicados`: Tags auto-extraídos (separados por `|`)
- `latency_ms`: Latencia de la llamada RAG
- `retrieved_k`: Nº de chunks recuperados
- `grounded_ratio`: Ratio de citas (0-1)
- `citations_count`: Nº de [N] en respuesta
- `answer_relevancy`: RAGAS metric
- `faithfulness`: RAGAS metric
- `context_precision`: RAGAS metric
- `context_recall`: RAGAS metric
- `hallucination`: 1 - faithfulness
- `bias`: LLM-as-Judge score
- `toxicity`: LLM-as-Judge score
- `notas`: Diagnóstico (issues detectados o "✓ All metrics passed")

---

## 🏷️ Tag Auto-Extraction

El evaluador auto-extrae tags del diccionario interno y los aplica como filtros:

```python
TAG_DICT = {
    "microgravity": ["microgravity", "weightlessness", "gravity"],
    "radiation": ["radiation", "cosmic", "ionizing"],
    "iss": ["iss", "station", "orbital"],
    "gene": ["genomics", "gene-expression", "molecular"],
    # ...más tags
}
```

**Query**: `"What are the effects of microgravity on bone density?"`  
**Tags aplicados**: `["bone", "microgravity", "skeletal", "weightlessness"]`

Estos tags se pueden usar para reforzar los filtros del RAG en futuras versiones.

---

## 🎯 Criterios de Calidad

Una respuesta **sólida** debe cumplir:

| Criterio | Valor |
|----------|-------|
| faithfulness | ≥ 0.8 |
| answer_relevancy | ≥ 0.8 |
| context_precision | ≥ 0.7 |
| context_recall | ≥ 0.7 |
| hallucination | ≤ 0.2 |
| bias | ≥ 0.9 |
| toxicity | ≥ 0.95 |
| grounded_ratio | ≥ 0.8 |

---

## 🔧 Configuración

### Endpoint del RAG

```python
RAG_ENDPOINT = "http://127.0.0.1:8000/api/chat"
```

### Top-K

```python
TOP_K = 8
```

### Dataset de Evaluación

Edita `load_evaluation_dataset()` en `eval_rag_nasa.py`:

```python
def load_evaluation_dataset() -> List[Dict[str, Any]]:
    return [
        {
            "query": "What are the effects of microgravity on bone density?",
            "ground_truth": None  # Opcional: respuesta de referencia
        },
        # ... más queries
    ]
```

O carga desde JSON:

```python
def load_evaluation_dataset():
    with open("evaluation_queries.json") as f:
        return json.load(f)
```

---

## 📊 Ejemplo de Salida (Console)

```
================================================================================
NASA BIOLOGY RAG EVALUATOR
================================================================================
Endpoint: http://127.0.0.1:8000/api/chat
Top-K: 8

📊 Dataset size: 8 queries

[1/8] Processing: What are the effects of microgravity on bone density...
  🏷️  Tags: ['bone', 'microgravity', 'skeletal', 'weightlessness']
  ⏱️  Latency: 2150ms
  📚 Retrieved: 8 chunks
  📊 Grounded ratio: 75.00%
  🔗 Citations: 12
  🤖 Evaluating bias & toxicity...

[2/8] Processing: How does spaceflight affect immune system function...
  ...

🔄 Running RAGAS evaluation on all queries...

================================================================================
📊 AGGREGATE METRICS
================================================================================

Latency (ms): 2342 ± 234
Retrieved-K: 8.0 ± 0.0
Grounded Ratio: 72.34% ± 8.12%
Citations/answer: 10.5 ± 2.3

RAGAS Metrics:
  Answer Relevancy: 0.851 ± 0.042
  Faithfulness: 0.892 ± 0.056
  Context Precision: 0.834 ± 0.067
  Context Recall: 0.823 ± 0.078
  Hallucination: 0.108 ± 0.056

LLM-as-Judge:
  Bias: 0.950 ± 0.071
  Toxicity: 1.000 ± 0.000

✅ JSON report saved: eval_results_20250105_143022.json
✅ CSV report saved: eval_rag_nasa.csv

================================================================================
⚠️  WORST PERFORMERS (for qualitative analysis)
================================================================================

1. Query: How does radiation exposure affect plant growth in space?
   Faithfulness: 0.765 | Hallucination: 0.235
   Grounded Ratio: 65.00% | Citations: 8
   Notes: Low faithfulness (0.77); Low citation coverage (65.00%)

2. Query: What cardiovascular changes occur during long-term spaceflight?
   Faithfulness: 0.812 | Hallucination: 0.188
   Grounded Ratio: 70.00% | Citations: 9
   Notes: Low citation coverage (70.00%)

3. Query: How does cosmic radiation impact DNA damage and repair?
   Faithfulness: 0.834 | Hallucination: 0.166
   Grounded Ratio: 72.00% | Citations: 11
   Notes: Low citation coverage (72.00%)

================================================================================
✅ EVALUATION COMPLETE
================================================================================
```

---

## 🛠️ Troubleshooting

### Error: "RAGAS requires OpenAI API key"

**Solución**: Configura `OPENAI_API_KEY` en `.env`:

```bash
OPENAI_API_KEY=sk-...
```

### Error: "Connection refused to RAG endpoint"

**Solución**: Verifica que el servidor RAG esté corriendo:

```bash
uvicorn app.main:app --reload --port 8000
```

### Grounded Ratio bajo (<0.6)

**Causa**: El prompt no está generando suficientes citas [N].

**Solución**:
1. Verifica que `SYNTHESIS_PROMPT` incluya instrucciones de citación
2. Considera implementar two-pass synthesis (ver TWO_PASS_SYNTHESIS.md)
3. Ajusta `OPENAI_TEMPERATURE` a 0.1 para más determinismo

### Faithfulness bajo (<0.7)

**Causa**: El modelo está alucinando información no presente en el contexto.

**Solución**:
1. Verifica la calidad del retrieval (context_precision, context_recall)
2. Aumenta `top_k` para más contexto
3. Revisa el prompt para enfatizar "ONLY use information from context"

---

## 📚 Referencias

- **RAGAS**: https://github.com/explodinggradients/ragas
- **LangChain Evaluation**: https://python.langchain.com/docs/guides/evaluation
- **NASA OSDR**: https://osdr.nasa.gov/bio/

---

## 🎉 Next Steps

1. **Aumentar dataset**: Agregar más queries de evaluación
2. **Ground truths**: Crear respuestas de referencia para context_recall
3. **A/B Testing**: Comparar single-pass vs two-pass synthesis
4. **Continuous monitoring**: Ejecutar evaluación en CI/CD pipeline
5. **Human evaluation**: Complementar con revisión manual de worst performers

---

✅ **Happy Evaluating!** 🚀
