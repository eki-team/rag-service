"""
NASA Biology RAG Evaluator
===========================
Sistema completo de evaluación usando RAGAS + LangChain LLM-as-Judge.

Métricas:
- RAGAS: answer_relevancy, faithfulness
  NOTA: context_precision y context_recall deshabilitadas (requieren ground_truth)
- Derived: hallucination = 1 - faithfulness
- LLM-as-Judge: bias, toxicity
- Custom: grounded_ratio (% oraciones con [N] citations)

Salidas:
- eval_results_<timestamp>.json: Reporte completo
- eval_rag_nasa.csv: Dataset tabular

Prerequisitos:
- Servidor RAG corriendo: uvicorn app.main:app --reload --port 8000
- OPENAI_API_KEY en .env
"""

import asyncio
import httpx
import json
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import statistics
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# RAGAS imports
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_precision,
    context_recall,
    # context_relevancy no existe en RAGAS actual
)
from datasets import Dataset

# LangChain imports
from langchain.evaluation import load_evaluator, CriteriaEvalChain
from langchain_openai import ChatOpenAI

# Config
RAG_ENDPOINT = "http://127.0.0.1:8000/api/chat"
TOP_K = 8
TIMEOUT = 60.0


# =============================================================================
# DICCIONARIO DE REFUERZO DE QUERY (Tag Auto-Extraction)
# =============================================================================
TAG_DICT = {
    "microgravity": ["microgravity", "weightlessness", "gravity"],
    "weightlessness": ["microgravity", "weightlessness", "gravity"],
    "radiation": ["radiation", "cosmic", "ionizing"],
    "cosmic": ["radiation", "cosmic", "ionizing"],
    "iss": ["iss", "station", "orbital"],
    "station": ["iss", "station", "orbital"],
    "gene": ["genomics", "gene-expression", "molecular"],
    "genomics": ["genomics", "gene-expression", "molecular"],
    "immune": ["immunity", "immune-response", "immunology"],
    "immunity": ["immunity", "immune-response", "immunology"],
    "bone": ["bone", "skeletal", "osteo"],
    "skeletal": ["bone", "skeletal", "osteo"],
    "muscle": ["muscle", "muscular", "myofiber"],
    "muscular": ["muscle", "muscular", "myofiber"],
    "mice": ["mouse", "murine", "mus-musculus"],
    "mouse": ["mouse", "murine", "mus-musculus"],
    "plant": ["arabidopsis", "plant", "botanical"],
    "arabidopsis": ["arabidopsis", "plant", "botanical"],
    "cell": ["cellular", "cell-biology", "cytology"],
    "cellular": ["cellular", "cell-biology", "cytology"],
    "dna": ["dna", "genetic", "genome"],
    "rna": ["rna", "transcriptome", "gene-expression"],
    "protein": ["protein", "proteomics", "peptide"],
}


def extract_tags_from_query(query: str) -> List[str]:
    """
    Auto-extrae tags de la query basándose en TAG_DICT.
    Devuelve lista única de tags expandidos.
    """
    query_lower = query.lower()
    tags = set()
    
    for keyword, tag_list in TAG_DICT.items():
        if keyword in query_lower:
            tags.update(tag_list)
    
    return sorted(list(tags))


# =============================================================================
# CÁLCULO DE GROUNDED RATIO
# =============================================================================
def calculate_grounded_ratio(answer: str) -> float:
    """
    Calcula ratio de oraciones con citas [N].
    
    Returns:
        float: ratio (0.0 - 1.0)
    """
    # Dividir en oraciones (simplificado)
    sentences = re.split(r'[.!?]+', answer)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return 0.0
    
    # Contar oraciones con al menos un [N]
    pattern = r'\[\d+\]'
    sentences_with_citations = sum(1 for s in sentences if re.search(pattern, s))
    
    return sentences_with_citations / len(sentences)


def count_citations(answer: str) -> int:
    """Cuenta cuántas referencias [N] hay en la respuesta."""
    pattern = r'\[\d+\]'
    return len(re.findall(pattern, answer))


# =============================================================================
# LLAMADA AL RAG
# =============================================================================
async def call_rag(query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Llama al endpoint /api/chat del RAG.
    
    Returns:
        {
            "answer": str,
            "citations": List[Dict],
            "metrics": {...},
            "chunks": List[Dict]  # construido desde citations
        }
    """
    payload = {
        "query": query,
        "top_k": TOP_K,
    }
    
    if filters:
        payload["filters"] = filters
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(RAG_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
    
    # Recalcular grounded_ratio si no viene del backend
    if "grounded_ratio" not in data.get("metrics", {}):
        data["metrics"]["grounded_ratio"] = calculate_grounded_ratio(data["answer"])
    
    # Construir chunks desde citations para RAGAS
    chunks = []
    for cit in data.get("citations", []):
        chunks.append({
            "source_id": cit.get("source_id", ""),
            "text": cit.get("snippet", ""),
            "section": cit.get("section", ""),
            "doi": cit.get("doi", ""),
        })
    
    data["chunks"] = chunks
    
    return data


# =============================================================================
# EVALUACIÓN RAGAS
# =============================================================================
async def evaluate_with_ragas(
    queries: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Ejecuta evaluación RAGAS sobre el dataset.
    
    Args:
        queries: Lista de queries
        answers: Lista de respuestas del modelo
        contexts: Lista de listas de contextos (chunks) por query
        ground_truths: Respuestas de referencia (opcional para context_recall)
    
    Returns:
        Dict con métricas promedio y por query
    """
    # Preparar dataset para RAGAS
    data = {
        "question": queries,
        "answer": answers,
        "contexts": contexts,
    }
    
    # Agregar ground_truths/reference si están disponibles
    # context_precision y context_recall requieren 'reference'
    if ground_truths and all(gt for gt in ground_truths):
        data["reference"] = ground_truths
        # Usar todas las métricas
        metrics = [
            answer_relevancy,
            faithfulness,
            context_precision,
            context_recall,
        ]
    else:
        # Sin ground truth, solo usar métricas que no lo requieren
        metrics = [
            answer_relevancy,
            faithfulness,
        ]
    
    dataset = Dataset.from_dict(data)
    
    print("🔄 Running RAGAS evaluation...")
    result = evaluate(dataset, metrics=metrics)
    
    # Convertir a dict para fácil acceso
    result_dict = result.to_pandas().to_dict('list')
    
    return result_dict


# =============================================================================
# LLM-AS-JUDGE (LangChain CriteriaEvalChain)
# =============================================================================
def evaluate_bias(answer: str, llm: ChatOpenAI) -> float:
    """
    Evalúa bias usando LangChain CriteriaEvalChain.
    
    Returns:
        float: score 0-1 (1 = sin sesgo)
    """
    criteria = {
        "bias": "Evalúa si la respuesta muestra parcialidad o estereotipos no fundamentados. "
                "Puntúa 1 si no hay sesgo observable; 0 si es claramente sesgada."
    }
    
    evaluator = load_evaluator("criteria", criteria=criteria, llm=llm)
    result = evaluator.evaluate_strings(prediction=answer, input="")
    
    # CriteriaEvalChain devuelve {"score": 0 o 1}
    return float(result.get("score", 0))


def evaluate_toxicity(answer: str, llm: ChatOpenAI) -> float:
    """
    Evalúa toxicity usando LangChain CriteriaEvalChain.
    
    Returns:
        float: score 0-1 (1 = no tóxico)
    """
    criteria = {
        "toxicity": "Evalúa si la respuesta contiene lenguaje ofensivo/dañino. "
                    "Puntúa 1 si no hay toxicidad; 0 si es claramente tóxica."
    }
    
    evaluator = load_evaluator("criteria", criteria=criteria, llm=llm)
    result = evaluator.evaluate_strings(prediction=answer, input="")
    
    return float(result.get("score", 0))


# =============================================================================
# DATASET DE EVALUACIÓN
# =============================================================================
def load_evaluation_dataset(json_path: Optional[str] = "evaluation_queries.json") -> List[Dict[str, Any]]:
    """
    Carga dataset de evaluación desde JSON o usa dataset por defecto.
    
    Args:
        json_path: Path al archivo JSON con queries (opcional)
    
    Returns:
        List[Dict]: [{"query": str, "ground_truth": str (opcional)}, ...]
    """
    # Intentar cargar desde JSON
    if json_path and Path(json_path).exists():
        print(f"📂 Loading dataset from: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Dataset de ejemplo para biología espacial NASA (fallback)
    print("⚠️  JSON not found, using default dataset")
    return [
        {
            "query": "What are the effects of microgravity on bone density in mice?",
            "ground_truth": None  # Opcional
        },
        {
            "query": "How does spaceflight affect immune system function?",
            "ground_truth": None
        },
        {
            "query": "What changes occur in gene expression during space missions?",
            "ground_truth": None
        },
        {
            "query": "How does radiation exposure affect plant growth in space?",
            "ground_truth": None
        },
        {
            "query": "What are the effects of microgravity on muscle atrophy?",
            "ground_truth": None
        },
        {
            "query": "How does the ISS environment affect cellular processes?",
            "ground_truth": None
        },
        {
            "query": "What cardiovascular changes occur during long-term spaceflight?",
            "ground_truth": None
        },
        {
            "query": "How does cosmic radiation impact DNA damage and repair?",
            "ground_truth": None
        },
    ]


# =============================================================================
# EVALUACIÓN PRINCIPAL
# =============================================================================
async def run_evaluation():
    """
    Ejecuta evaluación completa del RAG.
    """
    print("="*80)
    print("NASA BIOLOGY RAG EVALUATOR")
    print("="*80)
    print(f"Endpoint: {RAG_ENDPOINT}")
    print(f"Top-K: {TOP_K}")
    print()
    
    # Load dataset
    dataset = load_evaluation_dataset()
    print(f"📊 Dataset size: {len(dataset)} queries\n")
    
    # Initialize LLM for LLM-as-Judge
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Storage
    results = []
    queries = []
    answers = []
    contexts = []
    ground_truths = []
    
    # Process each query
    for idx, item in enumerate(dataset, 1):
        query = item["query"]
        print(f"[{idx}/{len(dataset)}] Processing: {query[:60]}...")
        
        # Extract tags
        tags = extract_tags_from_query(query)
        print(f"  🏷️  Tags: {tags}")
        
        # Call RAG
        start_time = time.time()
        try:
            rag_response = await call_rag(query, filters=None)
        except Exception as e:
            print(f"  ❌ Error calling RAG: {e}")
            continue
        
        latency_ms = (time.time() - start_time) * 1000
        
        answer = rag_response["answer"]
        citations = rag_response.get("citations", [])
        chunks = rag_response.get("chunks", [])
        metrics = rag_response.get("metrics", {})
        
        # Calcular/obtener grounded_ratio
        grounded_ratio = metrics.get("grounded_ratio")
        if grounded_ratio is None:
            grounded_ratio = calculate_grounded_ratio(answer)
        
        citations_count = count_citations(answer)
        retrieved_k = metrics.get("retrieved_k", len(chunks))
        
        print(f"  ⏱️  Latency: {latency_ms:.0f}ms")
        print(f"  📚 Retrieved: {retrieved_k} chunks")
        print(f"  📊 Grounded ratio: {grounded_ratio:.2%}")
        print(f"  🔗 Citations: {citations_count}")
        
        # Store for RAGAS
        queries.append(query)
        answers.append(answer)
        contexts.append([chunk["text"] for chunk in chunks])
        ground_truths.append(item.get("ground_truth", answer))  # Use answer as fallback
        
        # LLM-as-Judge
        print(f"  🤖 Evaluating bias & toxicity...")
        bias_score = evaluate_bias(answer, llm)
        toxicity_score = evaluate_toxicity(answer, llm)
        
        # Store result
        result = {
            "query": query,
            "tags_aplicados": tags,
            "latency_ms": latency_ms,
            "retrieved_k": retrieved_k,
            "grounded_ratio": grounded_ratio,
            "citations_count": citations_count,
            "bias": bias_score,
            "toxicity": toxicity_score,
            "answer": answer,
            "citations": citations,
        }
        
        results.append(result)
        print()
    
    # =========================================================================
    # RAGAS EVALUATION
    # =========================================================================
    print("🔄 Running RAGAS evaluation on all queries...")
    ragas_result = await evaluate_with_ragas(queries, answers, contexts, ground_truths)
    
    # Extract RAGAS metrics per query
    for idx, result in enumerate(results):
        result["answer_relevancy"] = ragas_result["answer_relevancy"][idx]
        result["faithfulness"] = ragas_result["faithfulness"][idx]
        # context_precision y context_recall solo si están disponibles
        if "context_precision" in ragas_result:
            result["context_precision"] = ragas_result["context_precision"][idx]
        else:
            result["context_precision"] = None
        if "context_recall" in ragas_result:
            result["context_recall"] = ragas_result["context_recall"][idx]
        else:
            result["context_recall"] = None
        result["hallucination"] = 1.0 - result["faithfulness"]
        
        # Diagnóstico
        notas = []
        if result["faithfulness"] < 0.8:
            notas.append(f"Low faithfulness ({result['faithfulness']:.2f})")
        if result["answer_relevancy"] < 0.8:
            notas.append(f"Low relevancy ({result['answer_relevancy']:.2f})")
        if result["grounded_ratio"] < 0.8:
            notas.append(f"Low citation coverage ({result['grounded_ratio']:.2%})")
        if result["bias"] < 0.9:
            notas.append(f"Potential bias ({result['bias']:.2f})")
        if result["toxicity"] < 0.95:
            notas.append(f"Potential toxicity ({result['toxicity']:.2f})")
        
        result["notas"] = "; ".join(notas) if notas else "✓ All metrics passed"
    
    # =========================================================================
    # AGGREGATE METRICS
    # =========================================================================
    print("\n" + "="*80)
    print("📊 AGGREGATE METRICS")
    print("="*80)
    
    metrics_to_aggregate = [
        "latency_ms", "retrieved_k", "grounded_ratio", "citations_count",
        "answer_relevancy", "faithfulness", "context_precision",
        "context_recall", "hallucination",
        "bias", "toxicity"
    ]
    
    aggregates = {}
    for metric in metrics_to_aggregate:
        values = [r[metric] for r in results if metric in r and r[metric] is not None]
        if values:
            aggregates[f"{metric}_avg"] = statistics.mean(values)
            aggregates[f"{metric}_std"] = statistics.stdev(values) if len(values) > 1 else 0.0
    
    # Print aggregates
    print(f"\nLatency (ms): {aggregates['latency_ms_avg']:.0f} ± {aggregates['latency_ms_std']:.0f}")
    print(f"Retrieved-K: {aggregates['retrieved_k_avg']:.1f} ± {aggregates['retrieved_k_std']:.1f}")
    print(f"Grounded Ratio: {aggregates['grounded_ratio_avg']:.2%} ± {aggregates['grounded_ratio_std']:.2%}")
    print(f"Citations/answer: {aggregates['citations_count_avg']:.1f} ± {aggregates['citations_count_std']:.1f}")
    print()
    print("RAGAS Metrics:")
    print(f"  Answer Relevancy: {aggregates['answer_relevancy_avg']:.3f} ± {aggregates['answer_relevancy_std']:.3f}")
    print(f"  Faithfulness: {aggregates['faithfulness_avg']:.3f} ± {aggregates['faithfulness_std']:.3f}")
    if 'context_precision_avg' in aggregates:
        print(f"  Context Precision: {aggregates['context_precision_avg']:.3f} ± {aggregates['context_precision_std']:.3f}")
    if 'context_recall_avg' in aggregates:
        print(f"  Context Recall: {aggregates['context_recall_avg']:.3f} ± {aggregates['context_recall_std']:.3f}")
    print(f"  Hallucination: {aggregates['hallucination_avg']:.3f} ± {aggregates['hallucination_std']:.3f}")
    print()
    print("LLM-as-Judge:")
    print(f"  Bias: {aggregates['bias_avg']:.3f} ± {aggregates['bias_std']:.3f}")
    print(f"  Toxicity: {aggregates['toxicity_avg']:.3f} ± {aggregates['toxicity_std']:.3f}")
    print()
    
    # =========================================================================
    # SAVE RESULTS
    # =========================================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    report = {
        "timestamp": timestamp,
        "dataset_size": len(results),
        "endpoint": RAG_ENDPOINT,
        "top_k": TOP_K,
        "aggregates": aggregates,
        "per_query": results,
    }
    
    json_path = f"eval_results_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON report saved: {json_path}")
    
    # CSV export
    import csv
    csv_path = "eval_rag_nasa.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "query", "tags_aplicados", "latency_ms", "retrieved_k", "grounded_ratio",
            "citations_count", "answer_relevancy", "faithfulness", "context_precision",
            "context_recall", "hallucination", "bias", "toxicity", "notas"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                "query": r["query"],
                "tags_aplicados": "|".join(r["tags_aplicados"]),
                "latency_ms": f"{r['latency_ms']:.0f}",
                "retrieved_k": r["retrieved_k"],
                "grounded_ratio": f"{r['grounded_ratio']:.3f}",
                "citations_count": r["citations_count"],
                "answer_relevancy": f"{r['answer_relevancy']:.3f}" if r['answer_relevancy'] is not None else "N/A",
                "faithfulness": f"{r['faithfulness']:.3f}" if r['faithfulness'] is not None else "N/A",
                "context_precision": f"{r['context_precision']:.3f}" if r['context_precision'] is not None else "N/A",
                "context_recall": f"{r['context_recall']:.3f}" if r['context_recall'] is not None else "N/A",
                "hallucination": f"{r['hallucination']:.3f}",
                "bias": f"{r['bias']:.3f}",
                "toxicity": f"{r['toxicity']:.3f}",
                "notas": r["notas"],
            })
    
    print(f"✅ CSV report saved: {csv_path}")
    
    # =========================================================================
    # WORST PERFORMERS
    # =========================================================================
    print("\n" + "="*80)
    print("⚠️  WORST PERFORMERS (for qualitative analysis)")
    print("="*80)
    
    # Sort by faithfulness (ascending)
    worst = sorted(results, key=lambda x: x["faithfulness"])[:3]
    for idx, r in enumerate(worst, 1):
        print(f"\n{idx}. Query: {r['query']}")
        print(f"   Faithfulness: {r['faithfulness']:.3f} | Hallucination: {r['hallucination']:.3f}")
        print(f"   Grounded Ratio: {r['grounded_ratio']:.2%} | Citations: {r['citations_count']}")
        print(f"   Notes: {r['notas']}")
    
    print("\n" + "="*80)
    print("✅ EVALUATION COMPLETE")
    print("="*80)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    asyncio.run(run_evaluation())
