# chat/services/json_ai.py

import os
import json
import re
import yaml
from datetime import datetime
from groq import Groq

from sentence_transformers import SentenceTransformer
from pgvector.django import L2Distance
from django.conf import settings

from chat.models import MetadataVector
from chat.services.memory import build_memory_context
from .json_prompt import JSON_QUERY_PROMPT

# Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load embedding model ONCE
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# VECTOR SEARCH
def get_relevant_metadata(question: str) -> str:
    query_embedding = embedding_model.encode(question).tolist()

    results = (
        MetadataVector.objects
        .annotate(distance=L2Distance("embedding", query_embedding))
        .order_by("distance")[:10]
    )

    table_map = {}

    for res in results:
        key = res.metadata_key
        if "." in key:
            table, column = key.split(".", 1)
        else:
            table = key
            column = None

        table_map.setdefault(table, set())
        if column:
            table_map[table].add(column)


    structured_results = [
        {"table": t, "columns": sorted(list(cols))}
        for t, cols in table_map.items()
    ]

    return json.dumps(structured_results, indent=2)


def generate_json_plan(question: str, user_context: dict = None) -> dict:
    # ✅ Correct YAML path
    metadata_path = os.path.join(settings.BASE_DIR, "schema_metadata.yaml")
    with open(metadata_path, "r") as f:
        metadata = yaml.safe_load(f)

    current_date = datetime.now().strftime("%Y-%m-%d")
    vector_results = get_relevant_metadata(question)
    memory_context = build_memory_context()

    # ✅ CORRECT prompt injection
    prompt = JSON_QUERY_PROMPT.format(
        user_context=json.dumps(user_context or {}, indent=2),
        memory=memory_context,
        metadata=json.dumps(metadata, indent=2),
        vector_results=vector_results,
        current_date=current_date,
    )


    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",

        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )

    raw_output = response.choices[0].message.content.strip()

    match = re.search(r"\{[\s\S]*\}", raw_output)
    if not match:
        raise ValueError("AI did not return valid JSON")

    json_text = match.group(0)

    return json.loads(json_text)
