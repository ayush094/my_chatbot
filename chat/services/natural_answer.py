# chat/services/natural_answer.py

import json
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_natural_answer(question: str, data: list) -> str:
    """
    Converts DB rows into a natural language answer
    """

    if not data:
        return "No records found matching your request."

    prompt = f"""
You are a helpful HR assistant.

Answer the user's question using ONLY the provided database records.
Do NOT invent information.
Do NOT mention database field names unless required.

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
