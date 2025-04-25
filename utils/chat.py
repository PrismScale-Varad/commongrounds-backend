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

def prepare_messages(chat, extra_user_message=None):
    """
    Prepare messages list for OpenAI calls, including system prompt, chat messages, and optional extra user message.
    Converts 'tool' sender to 'function' role.
    """
    messages = []
    system_prompt = settings.SYSTEM_PROMPT
    messages.append({'role': 'system', 'content': system_prompt})

    for message in chat.messages:
        role = message.sender
        if role == "tool":
            role = "function"
        messages.append({'role': role, 'content': message.message})

    if extra_user_message:
        messages.append({'role': 'user', 'content': extra_user_message})

    return messages

def generate_chat_title(text: str) -> str:
    try:
        prompt = f"Create a concise and descriptive title for the following conversation text:\n\n{text}\n\nTitle:" 
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=15,
            temperature=0.5,
            n=1
        )
        choice = response['choices'][0]
        title = choice['message']['content'].strip().strip('"')
        return title
    except Exception as e:
        logger.error(f'Error generating chat title: {str(e)}')
        return "New Chat"

def generate_llm_response(chat):
    try:
        session = SessionLocal()

        messages = prepare_messages(chat)

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            functions=[user_search_function],
            function_call='auto',
            max_tokens=150
        )

        choice = response['choices'][0]
        message = choice['message']

        if 'function_call' in message:
            function_name = message['function_call']['name']
            arguments_json = message['function_call'].get('arguments', '{}')
            arguments = json.loads(arguments_json)

            if function_name == 'user_search':
                query = arguments.get('query', '')
                if not query:
                    raise ValueError('User search query argument missing')

                tool_msg = user_search_tool(session, chat, query)
                session.commit()

                messages.append({'role': 'function', 'name': function_name, 'content': tool_msg.message})

                second_response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=messages,
                    max_tokens=150
                )
                second_message = second_response['choices'][0]['message']['content'].strip()

                return second_message

        return message['content'].strip()

    except Exception as e:
        logger.error(f'Error while calling OpenAI API: {str(e)}')
        return "I'm sorry, I couldn't generate a response at the moment."


def stream_llm_response(chat, user_message):
    """
    Stream response from OpenAI API with support for function calls.
    """
    try:
        session = SessionLocal()

        messages = prepare_messages(chat, extra_user_message=user_message)

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            functions=[user_search_function],
            function_call='auto',
            max_tokens=150,
            stream=True
        )

        function_call = None
        collecting_function_args = False
        function_name = None
        function_args_str = ''
        collected_content = ''

        for chunk in response:
            if 'choices' in chunk:
                choice = chunk['choices'][0]
                delta = choice.get('delta', {})

                if 'content' in delta:
                    content_piece = delta['content']
                    collected_content += content_piece
                    yield content_piece

                if 'function_call' in delta:
                    fc = delta['function_call']
                    if 'name' in fc:
                        function_name = fc['name']
                        collecting_function_args = True
                        function_args_str = ''
                    if 'arguments' in fc and fc['arguments'] is not None:
                        function_args_str += fc['arguments']

                elif collecting_function_args and 'arguments' in delta:
                    function_args_str += delta['arguments']

                if collecting_function_args and function_name and function_args_str:
                    try:
                        args_json = json.loads(function_args_str)
                        if function_name == 'user_search':
                            query = args_json.get('query', '')
                            tool_msg = user_search_tool(session, chat, query)
                            session.commit()

                            messages.append({'role': 'function', 'name': function_name, 'content': tool_msg.message})

                            followup_response = openai.ChatCompletion.create(
                                model='gpt-3.5-turbo',
                                messages=messages,
                                max_tokens=150,
                                stream=True
                            )

                            for fchunk in followup_response:
                                if 'choices' in fchunk:
                                    fchoice = fchunk['choices'][0]
                                    fdelta = fchoice.get('delta', {})
                                    if 'content' in fdelta:
                                        yield fdelta['content']
                            break
                    except json.JSONDecodeError:
                        pass

    except Exception as e:
        logger.error(f'Error while streaming OpenAI API: {str(e)}')
        yield ""
