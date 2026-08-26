# WHAT DOES THIS FILE DO: Sample code snippets used across the benchmark suite — some intentionally broken, some clean.


# =========== VARIABLES : intentionally faulty code, one distinct issue type per sample ===========
BROKEN_SAMPLES = [
    # Sample 1: runtime error (division by zero)
    """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)  # Fails if len = 0

result = calculate_average([])
print(result)
""",

    # Sample 2: import error
    """
import nonexistent_library
result = nonexistent_library.function()
""",

    # Sample 3: type mismatch
    """
def process_data(data: dict) -> str:
    return data.get("key") + 10  # Can't add string + int

result = process_data({"key": "value"})
""",

    # Sample 4: infinite loop
    """
def wait_for_condition():
    while True:
        if some_condition:
            break
        # Missing update to some_condition — infinite loop
    return "done"
""",

    # Sample 5: unsafe subprocess (command injection)
    """
import os
def run_command(user_input):
    os.system(f"ls {user_input}")  # Command injection risk
""",

    # Sample 6: hardcoded secret
    """
API_KEY = "sk-proj-abc123xyz789"
def fetch_data():
    return requests.get("https://api.example.com", headers={"key": API_KEY})
""",

    # Sample 7: eval() usage
    """
def evaluate_expression(expr: str):
    return eval(expr)  # Dangerous
""",

    # Sample 8: missing error handling
    """
def parse_json(data: str):
    return json.loads(data)  # Fails if invalid JSON, no try-catch
""",
]
# =========== VARIABLES : intentionally faulty code, one distinct issue type per sample ===========


# =========== VARIABLES : known-clean code, used to check we don't flag good code as broken ===========
SECURE_SAMPLES = [
    # Sample 1: safe division
    """
def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
""",

    # Sample 2: safe import
    """
import json
data = json.loads('{"key": "value"}')
print(data)
""",

    # Sample 3: type-safe
    """
def process_data(data: dict) -> str:
    key_value = data.get("key", "")
    return str(key_value)
""",
]
# =========== VARIABLES : known-clean code, used to check we don't flag good code as broken ===========
