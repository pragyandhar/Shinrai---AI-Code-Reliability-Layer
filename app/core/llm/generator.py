# WHAT DOES THIS FILE DO: Connects to Azure AI Foundry and generates Python code from a given prompt.

# ================== IMPORTS ==================
from openai import AzureOpenAI

from app.config import settings
# ================== IMPORTS ==================


# =========== VARIABLES : Azure AI Foundry client — one instance reused across all calls ===========
client = AzureOpenAI(
    azure_endpoint=settings.foundry_endpoint,
    api_key=settings.foundry_api_key,
    api_version=settings.azure_openai_api_version,
)
# =========== VARIABLES : Azure AI Foundry client — one instance reused across all calls ===========


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

    # FLOW-2: send to GPT-5.4 and get response
    response = client.chat.completions.create(
        model=settings.foundry_deployment,
        messages=messages,
    )

    # FLOW-3: extract the code string and strip any accidental whitespace
    generated_code = response.choices[0].message.content.strip()

    return generated_code
# =========== FUNCTION ===========
