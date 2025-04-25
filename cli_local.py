#!/usr/bin/env python3
import os
import subprocess
import json
import re
import math
import tempfile
import time
from openai import OpenAI

# --- LM Studio client init ---
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
MODEL = "lmstudio-community/qwen2.5-7b-instruct"

# --- Helper to build tool specs ---
def mk_tool(name, desc, params_schema):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": params_schema
        }
    }

# --- Tool definitions ---
TOOLS = [
    mk_tool("shell", "Run a PowerShell command", {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"]
    }),
    mk_tool("read_codebase", "List files in the git codebase", {
        "type": "object", "properties": {}, "required": []
    }),
    mk_tool("read_files", "Read contents of multiple files", {
        "type": "object",
        "properties": {"file_list": {"type": "string"}},
        "required": ["file_list"]
    }),
    mk_tool("edit_file", "Edit an existing file by replacing its content", {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content":  {"type": "string"}
        },
        "required": ["filename", "content"]
    }),
    mk_tool("create_file", "Create any text-based file", {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content":  {"type": "string"}
        },
        "required": ["filename", "content"]
    }),
    mk_tool("calculate", "Evaluate a mathematical expression", {
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"]
    }),
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time, only if asked",
            "parameters": {"type": "object", "properties": {}},
        }
    }
]

# --- Tool implementations ---
def shell(command: str) -> str:
    proc = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True, text=True
    )
    out = proc.stdout + proc.stderr
    return out or f"Command `{command}` executed successfully."

def read_codebase() -> str:
    proc = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True
    )
    return proc.stdout

def read_files(file_list: str) -> str:
    files = [f.strip() for f in file_list.split(",")]
    outputs = []
    for fname in files:
        if not os.path.isfile(fname):
            outputs.append(f"**Error:** '{fname}' not found.")
            continue
        try:
            with open(fname, "r", encoding="utf-8") as fh:
                content = fh.read()
            outputs.append(f"----- {fname} -----\n{content}")
        except Exception as e:
            outputs.append(f"**Error reading {fname}:** {e}")
    return "\n\n".join(outputs)

def edit_file(filename: str, content: str) -> str:
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error updating {filename}: {e}"

def create_file(filename: str, content: str) -> str:
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(filename, 0o755)
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error creating {filename}: {e}"

def calculate(expression: str) -> str:
    try:
        expression = re.sub(r'sin\((.*?)\)', r'sin(radians(\1))', expression)
        safe_env = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        safe_env.update({'abs': abs, 'max': max, 'min': min, 'pow': pow,
                         'round': round, 'sum': sum, 'len': len})
        result = eval(expression, {"__builtins__": {}}, safe_env)
        return f"Result: {result}"
    except Exception as e:
        return f"Error in calculation: {e}"

def get_current_time():
    return {"time": time.strftime("%H:%M:%S")}

# --- Streaming helper with guards ---
def process_stream(stream, add_assistant_label=True):
    collected = ""
    tool_calls = []
    first = True

    for chunk in stream:
        if chunk is None or not hasattr(chunk, "choices") or not chunk.choices:
            continue
        choice = chunk.choices[0]
        if choice is None or not hasattr(choice, "delta"):
            continue

        delta = choice.delta

        if getattr(delta, "content", None):
            if first:
                print()
                if add_assistant_label:
                    print("Assistant:", end=" ", flush=True)
                first = False
            print(delta.content, end="", flush=True)
            collected += delta.content

        if getattr(delta, "tool_calls", None):
            for tc in delta.tool_calls:
                idx = tc.index
                if len(tool_calls) <= idx:
                    tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                tool_calls[idx]["id"]        += (tc.id or "")
                tool_calls[idx]["function"]["name"]      += (tc.function.name      or "")
                tool_calls[idx]["function"]["arguments"] += (tc.function.arguments or "")

    return collected, tool_calls

# --- Chat loop ---
def chat_loop():
    messages = []
    print("Assistant: Hi! I am an AI agent empowered with tools (type 'quit' to exit).")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "quit":
            break
        messages.append({"role": "user", "content": user_input})

        # 1) Initial LM Studio streaming call
        response_text, tool_calls = process_stream(
            client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                stream=True,
                temperature=0.2
            )
        )

        # 2) Record assistant text if any
        if response_text:
            print()
            messages.append({"role": "assistant", "content": response_text})

        # 3) If the model requested tools...
        if tool_calls:
            print()
            # Emit proper function_call messages
            for tc in tool_calls:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                print(f"**Calling tool: {name}**")
                messages.append({
                    "role": "assistant",
                    "function_call": {"name": name, "arguments": args}
                })

            # 4) Execute each tool, print its output, and append to messages
            for tc in tool_calls:
                fn = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                if fn == "get_current_time":
                    result = get_current_time()
                elif fn == "shell":
                    result = shell(**args)
                elif fn == "read_codebase":
                    result = read_codebase()
                elif fn == "read_files":
                    result = read_files(**args)
                elif fn == "edit_file":
                    result = edit_file(**args)
                elif fn == "create_file":
                    result = create_file(**args)
                elif fn == "calculate":
                    result = calculate(**args)
                else:
                    result = f"Unknown tool: {fn}"

                # <-- NEW: print the tool result immediately -->
                if isinstance(result, str):
                    print(result)
                else:
                    print(json.dumps(result, indent=2))

                messages.append({
                    "role": "tool",
                    "name": fn,
                    "content": json.dumps(result)
                })

            # 5) Final LM Studio response after tool execution
            final_text, _ = process_stream(
                client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    stream=True
                ),
                add_assistant_label=False
            )
            if final_text:
                print()
                messages.append({"role": "assistant", "content": final_text})

    print("Goodbye!")

if __name__ == "__main__":
    chat_loop()
