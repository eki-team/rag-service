"""
Test simple de RAGAS para verificar que funciona correctamente
"""
import os
from dotenv import load_dotenv
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness
from datasets import Dataset

# Cargar variables de entorno
load_dotenv()

# Verificar API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in environment")
    exit(1)
else:
    print(f"✅ API Key loaded: {api_key[:10]}...")

# Dataset de prueba con 2 queries
data = {
    "question": [
        "What is the capital of France?",
        "What causes seasons on Earth?"
    ],
    "answer": [
        "The capital of France is Paris. Paris is known for the Eiffel Tower.",
        "Seasons are caused by the tilt of Earth's axis as it orbits the Sun."
    ],
    "contexts": [
        ["Paris is the capital and most populous city of France.", "The Eiffel Tower is in Paris."],
        ["Earth's axis is tilted at 23.5 degrees.", "This tilt causes different amounts of sunlight."]
    ]
}

dataset = Dataset.from_dict(data)

print("\n📊 Dataset creado:")
print(f"  - {len(data['question'])} queries")
print(f"  - Métricas: answer_relevancy, faithfulness")

# Ejecutar RAGAS
print("\n🔄 Ejecutando RAGAS...")
metrics = [answer_relevancy, faithfulness]
result = evaluate(dataset, metrics=metrics)

print("\n✅ RAGAS completado!")
print(f"\nTipo de resultado: {type(result)}")
print(f"Atributos: {dir(result)}")

# Convertir a pandas para inspección
df = result.to_pandas()
print("\n📊 Resultados (DataFrame):")
print(df)

# Convertir a dict
result_dict = df.to_dict('list')
print("\n📊 Resultados (Dict):")
for key, values in result_dict.items():
    print(f"  {key}: {values}")
