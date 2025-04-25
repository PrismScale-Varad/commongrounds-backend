from openai import OpenAI 
from core.config import settings
import logging
import json
from services.chat_service import user_search_tool
from core.database import SessionLocal

logger = logging.getLogger(__name__)

api_key = settings.OPENAI_API_KEY
openai = OpenAI(api_key)

user_search_function = {
    "name": "user_search",
    "description": "Search for users based on a text query using embeddings similarity.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string to find users."
            }
        },
        "required": ["query"]
    }
}

def generate_llm_response(chat):
    """
    Calls OpenAI's GPT-3.5-turbo model with function calling support to generate a response based on the chat's messages.
    Constructs a messages list including a system prompt, user, assistant, and tool messages.
    Handles LLM function call requests by calling the appropriate backend tool and appending the tool response to the chat.
    Returns the final assistant reply.
    """
    try:
        session = SessionLocal()

        # Prepare messages in the format expected by OpenAI
        messages = []
        # Add system prompt from config
        system_prompt = settings.SYSTEM_PROMPT
        messages.append({'role': 'system', 'content': system_prompt})

        for message in chat.messages:
            # Use role "tool" as function_call message role
            role = message.sender
            if role == "tool":
                role = "function"
            messages.append({'role': role, 'content': message.message})

        # Call OpenAI API with function calling enabled
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            functions=[user_search_function],
            function_call='auto',
            max_tokens=150
        )

        choice = response['choices'][0]
        message = choice['message']

        # Check if model wants to call a function
        if 'function_call' in message:
            function_name = message['function_call']['name']
            arguments_json = message['function_call'].get('arguments', '{}')
            arguments = json.loads(arguments_json)

            if function_name == 'user_search':
                query = arguments.get('query', '')
                if not query:
                    raise ValueError('User search query argument missing')

                # Call the tool function and save message to DB
                tool_msg = user_search_tool(session, chat, query)
                session.commit()

                # Append the tool message to messages for the follow-up LLM call
                messages.append({'role': 'function', 'name': function_name, 'content': tool_msg.message})

                # Call LLM again with tool response appended
                second_response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=messages,
                    max_tokens=150
                )
                second_message = second_response['choices'][0]['message']['content'].strip()

                return second_message

        # Normal assistant message
        return message['content'].strip()

    except Exception as e:
        logger.error(f'Error while calling OpenAI API: {str(e)}')
        return "I'm sorry, I couldn't generate a response at the moment."
