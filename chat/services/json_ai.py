import os
import json
import re
import yaml
from datetime import datetime
from groq import Groq

from sentence_transformers import SentenceTransformer
from pgvector.django import L2Distance

from chat.models import MetadataVector
from .json_prompt import JSON_QUERY_PROMPT

# Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load embedding model ONCE (important for performance)
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# VECTOR SEARCH: Find relevant schema elements
def get_relevant_metadata(question: str) -> str:
    """
    Performs vector similarity search on MetadataVector
    to identify relevant tables and columns.
    Returns JSON string for prompt injection.
    """

    query_embedding = embedding_model.encode(question).tolist()

    results = (
        MetadataVector.objects
        .annotate(distance=L2Distance("embedding", query_embedding))
        .order_by("distance")[:10]
    )

    table_map: dict[str, set] = {}

    for res in results:
        key = res.metadata_key
        if "." in key:
            table, column = key.split(".", 1)
        else:
            table, column = key, None

        table_map.setdefault(table, set())
        if column:
            table_map[table].add(column)

    structured_results = [
        {
            "table": table,
            "columns": sorted(list(columns))
        }
        for table, columns in table_map.items()
    ]

    return json.dumps(structured_results, indent=2)


# AI → JSON QUERY PLAN
def generate_json_plan(question: str) -> dict:
    """
    Generates a STRICT JSON query plan using:
    - YAML schema metadata
    - Vector search results
    - Deterministic AI generation
    """

    # Load schema metadata
    metadata_path = os.path.join(os.getcwd(), "schema_metadata.yaml")
    with open(metadata_path, "r") as f:
        metadata = yaml.safe_load(f)

    current_date = datetime.now().strftime("%Y-%m-%d")
    vector_results = get_relevant_metadata(question)

    prompt = JSON_QUERY_PROMPT.format(
        metadata=yaml.dump(metadata, sort_keys=False),
        vector_results=vector_results,
        current_date=current_date,
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )

    raw_output = response.choices[0].message.content.strip()
    print("RAW AI OUTPUT:\n", raw_output)

    # STRICT JSON EXTRACTION
    match = re.search(r"\{[\s\S]*\}", raw_output)
    if not match:
        raise ValueError("AI did not return valid JSON")

    json_text = match.group(0)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        # Minimal fallback for single-quote issues
        try:
            return json.loads(json_text.replace("'", '"'))
        except Exception as e:
            raise ValueError(f"Invalid JSON from AI: {e}")


# DB RESULT → NATURAL LANGUAGE
def generate_natural_answer(question: str, data: list) -> str:
    """
    Converts raw database rows into a natural,
    user-friendly answer.
    """

    if not data:
        return "No records found matching your request."

    prompt = f"""
You are a helpful HR assistant.

Answer the user's question using ONLY the provided database records.
Do NOT invent information.
Do NOT mention database field names unless required for clarity.

User Question:
{question}

Database Records:
{json.dumps(data, default=str, indent=2)}

Natural language answer:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()
