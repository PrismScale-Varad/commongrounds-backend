def generate_chat_title(message: str) -> str:
    """
    Generate a chat title using the first few words of the first message.
    """
    words = message.split()
    title = " ".join(words[:5]) if len(words) >= 5 else message
    return title

def generate_llm_response(chat) -> str:
    """
    Generate a placeholder LLM response.
    In production, integrate with an LLM API.
    """
    return "This is a placeholder LLM response."
