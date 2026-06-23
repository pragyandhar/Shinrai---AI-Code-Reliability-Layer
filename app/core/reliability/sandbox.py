# WHAT DOES THIS FILE DO: Runs LLM-generated code in an isolated subprocess and captures runtime behavior.

# ================== IMPORTS ==================
import os
import shutil
import subprocess
import sys
import tempfile
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: sets a 256MB memory limit — only called on Linux via preexec_fn
def _set_memory_limit() -> None:
    ''' sets process memory limit to 256MB using resource module (Linux only) '''

    import resource     # USE: resource module is Unix-only that's why import is here not at top level
    limit = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

# =========== FUNCTION ===========


# =========== FUNCTION ===========
# ROLE: executes the given code string in an isolated subprocess and returns score + runtime issues
def run_sandbox(code: str) -> dict:
    ''' creates isolated temp dir, runs code inside it, cleans up after — relative path ops stay contained '''

    tmp_dir = None

    try:
        # FLOW-1: create a temp directory — code runs inside here, so any relative file ops stay contained
        tmp_dir = tempfile.mkdtemp()    # USE: isolated working dir so os.remove("file") only hits this dir
        tmp_path = os.path.join(tmp_dir, "code.py")

        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        # FLOW-2: set preexec_fn only on Linux — memory limit via resource module
        pre_exec = _set_memory_limit if sys.platform == "linux" else None

        # FLOW-3: run the code with cwd set to temp dir — subprocess inherits that working directory
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=tmp_dir,            # USE: any relative file operations land inside tmp_dir, not the project root
            preexec_fn=pre_exec,
        )

        # FLOW-4: determine outcome from returncode and stderr
        if result.returncode == 0 and not result.stderr.strip():
            return {
                "score": 100,
                "tier": "CRITICAL",
                "issues": [],
            }

        if result.returncode == 0 and result.stderr.strip():
            return {
                "score": 70,
                "tier": "CRITICAL",
                "issues": [{"type": "warning", "message": result.stderr.strip()}],
            }

        if result.returncode > 0:
            return {
                "score": 30,
                "tier": "CRITICAL",
                "issues": [{"type": "runtime_error", "message": result.stderr.strip()}],
            }

        # returncode < 0 means killed by OS signal — memory limit hit or segfault
        return {
            "score": 0,
            "tier": "CRITICAL",
            "issues": [{"type": "hard_crash", "message": f"process killed by signal {abs(result.returncode)}"}],
        }

    except subprocess.TimeoutExpired:
        return {
            "score": 0,
            "tier": "CRITICAL",
            "issues": [{"type": "timeout", "message": "execution timed out after 10 seconds — possible infinite loop"}],
        }

    finally:
        # wipe the entire temp dir — anything the code created inside is gone too
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)  # USE: rmtree removes the dir + everything inside it

# =========== FUNCTION ===========
