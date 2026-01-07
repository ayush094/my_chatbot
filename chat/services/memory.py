# chat/services/memory.py

from chat.models import ChatMessage

SHORT_MEMORY_LIMIT = 10

def get_short_memory():
    """
    Fetch last N chat messages (short-term memory)
    """
    return ChatMessage.objects.order_by("-timestamp")[:SHORT_MEMORY_LIMIT]


def build_memory_context():
    """
    Convert memory into AI-readable conversation context
    """
    messages = get_short_memory()
    context = ""

    for msg in reversed(messages):
        context += f"User: {msg.user_message}\n"
        context += f"Assistant: {msg.ai_response}\n"

    return context.strip()
