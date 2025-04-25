import openai
from core.config import settings
import logging

logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

def generate_llm_response(message: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',  # or any other model you prefer
            messages=[{'role': 'user', 'content': message}],
            max_tokens=150  # adjust as per your needs
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f'Error while calling OpenAI API: {str(e)}')
        return "I'm sorry, I couldn't generate a response at the moment."
