# WHAT DOES THIS FILE DO: Centralized settings for the benchmark suite — sample sizes, timeouts, output paths.

# ================== IMPORTS ==================
import os
# ================== IMPORTS ==================


# =========== VARIABLES : benchmark settings, all in one place so runner.py and the individual benchmark files stay in sync ===========
class BenchmarkConfig:
    ''' every benchmark file reads its iteration count / timeout / output path from here instead of hardcoding it '''

    # sample sizes
    PERFORMANCE_ITERATIONS = 50        # full pipeline runs
    COMPONENT_ITERATIONS = 20          # per-component runs
    ACCURACY_ITERATIONS = 100          # detection rate tests

    # timeouts, in seconds
    GENERATION_TIMEOUT = 30
    RELIABILITY_TIMEOUT = 10
    SECURITY_TIMEOUT = 10

    # output paths
    RESULTS_DIR = "benchmarks/results"
    REPORT_FILE = os.path.join(RESULTS_DIR, "benchmark_report.json")
    CSV_FILE = os.path.join(RESULTS_DIR, "benchmark_data.csv")

    # test environment
    USE_MOCK_LLM = False       # USE: set True to use cached responses instead of live GPT-4o calls, for repeatable runs
    CACHE_DIR = "benchmarks/cache"

    # accuracy thresholds
    ACCEPTABLE_DETECTION_RATE = 0.75   # 75%+ detection rate counts as good
# =========== VARIABLES : benchmark settings, all in one place so runner.py and the individual benchmark files stay in sync ===========
