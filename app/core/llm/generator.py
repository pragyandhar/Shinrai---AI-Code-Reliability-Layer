# WHAT DOES THIS FILE DO: Connects to OpenAI and generates Python code from a given prompt.

# ================== IMPORTS ==================
from openai import OpenAI

from app.config import settings
# ================== IMPORTS ==================


# =========== VARIABLES : OpenAI client — one instance reused across all calls ===========
client = OpenAI(api_key=settings.openai_api_key)
# =========== VARIABLES : OpenAI client — one instance reused across all calls ===========


# =========== FUNCTION ===========
# ROLE: takes a prompt, sends it to GPT-5.4, returns only the raw generated code
def generate_code(prompt: str) -> str:
    ''' sends user prompt to GPT-5.4 and gets back clean Python code — no markdown, no explanation '''

    # FLOW-1: build the messages — system tells GPT-4o to return raw code only
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Python code generator. "
                "Return only raw Python code with no markdown, no triple backticks, no explanation. "
                "The output must be directly executable Python."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    # FLOW-2: send to GPT and get response
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
    )

    # FLOW-3: extract the code string and strip any accidental whitespace
    generated_code = response.choices[0].message.content.strip()

    return generated_code
# =========== FUNCTION ===========
