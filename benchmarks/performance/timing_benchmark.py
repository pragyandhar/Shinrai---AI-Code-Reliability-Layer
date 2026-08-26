# WHAT DOES THIS FILE DO: Measures execution time for each pipeline component — generation, reliability, security, confidence.

# ================== IMPORTS ==================
import statistics
import time
from typing import Callable

from app.core.llm.generator import generate_code
from app.core.reliability.runner import run_reliability_checks
from app.core.security.runner import run_security
from app.core.confidence.aggregator import aggregate_report
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: times component functions and rolls the raw times into avg/median/min/max/stdev stats
class TimingBenchmark:
    ''' one static method per pipeline component, all sharing the same measure-and-summarize shape '''

    # FLOW-1: timer wraps a single call — everything else in this class is just "call this N times and summarize"
    @staticmethod
    def measure_function(func: Callable, *args, **kwargs) -> tuple:
        ''' runs func once, returns (elapsed_seconds, result) '''

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        return end - start, result

    # FLOW-2: shared summary builder — every benchmark_* method below just supplies the component name and the raw times
    @staticmethod
    def _summarize(component: str, times: list) -> dict:
        ''' turns a list of elapsed-seconds readings into the avg/median/min/max/stdev report every caller needs '''

        times_ms = [t * 1000 for t in times]

        return {
            "component": component,
            "iterations": len(times),
            "times_ms": times_ms,
            "avg_ms": statistics.mean(times_ms),
            "median_ms": statistics.median(times_ms),
            "min_ms": min(times_ms),
            "max_ms": max(times_ms),
            "stdev_ms": statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
        }

    # FLOW-3: code generation — this one hits Azure AI Foundry for real, each iteration is a billed API call
    @staticmethod
    def benchmark_generation(prompt: str, iterations: int = 5) -> dict:
        ''' times generate_code() across iterations, one live GPT-4o call per iteration '''

        times = []
        for _ in range(iterations):
            elapsed, _ = TimingBenchmark.measure_function(generate_code, prompt)
            times.append(elapsed)

        return TimingBenchmark._summarize("code_generation", times)

    # FLOW-4: reliability checks — needs ruff + mypy actually installed to run cleanly
    @staticmethod
    def benchmark_reliability(code: str, iterations: int = 10) -> dict:
        ''' times run_reliability_checks() across iterations on the same code string '''

        times = []
        for _ in range(iterations):
            elapsed, _ = TimingBenchmark.measure_function(run_reliability_checks, code)
            times.append(elapsed)

        return TimingBenchmark._summarize("reliability_checks", times)

    # FLOW-5: security checks — self-contained, degrades gracefully even without bandit/pip-audit installed
    @staticmethod
    def benchmark_security(code: str, iterations: int = 10) -> dict:
        ''' times run_security() across iterations on the same code string '''

        times = []
        for _ in range(iterations):
            elapsed, _ = TimingBenchmark.measure_function(run_security, code)
            times.append(elapsed)

        return TimingBenchmark._summarize("security_checks", times)

    # FLOW-6: confidence aggregation — pure Python, no subprocess or network involved, expect sub-millisecond times
    @staticmethod
    def benchmark_confidence(reliability: dict, security: dict, iterations: int = 50) -> dict:
        ''' times aggregate_report() across iterations on the same pair of reports '''

        times = []
        for _ in range(iterations):
            elapsed, _ = TimingBenchmark.measure_function(aggregate_report, reliability, security)
            times.append(elapsed)

        return TimingBenchmark._summarize("confidence_aggregation", times)
# =========== FUNCTION ===========
