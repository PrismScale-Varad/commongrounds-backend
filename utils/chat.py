from openai import OpenAI 
from core.config import settings
import logging

logger = logging.getLogger(__name__)

api_key = settings.OPENAI_API_KEY
openai = OpenAI(api_key)


def generate_llm_response(chat):
    """
    Calls OpenAI's GPT-3.5-turbo model to generate a response based on the chat's messages.
    Constructs a messages list in the expected format, sends it to the API, and returns the assistant's reply.
    Logs and returns a default message if an error occurs.
    """
    try:
        # Prepare messages in the format expected by OpenAI
        messages = []
        # Add system prompt from config
        system_prompt = settings.SYSTEM_PROMPT
        messages.append({'role': 'system', 'content': system_prompt})

        for message in chat.messages:
            role = 'user' if message.sender == 'user' else 'assistant'
            messages.append({'role': role, 'content': message.message})

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            max_tokens=150
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f'Error while calling OpenAI API: {str(e)}')
        return "I'm sorry, I couldn't generate a response at the moment."
