# WHAT DOES THIS FILE DO: Main benchmark orchestrator — runs every performance, accuracy and repair benchmark, saves one combined report.

# ================== IMPORTS ==================
import json
import os
from datetime import datetime

from benchmarks.config import BenchmarkConfig
from benchmarks.performance.timing_benchmark import TimingBenchmark
from benchmarks.accuracy.reliability_accuracy import ReliabilityAccuracy
from benchmarks.accuracy.security_accuracy import SecurityAccuracy
from benchmarks.accuracy.repair_success import RepairSuccess
from benchmarks.test_datasets.broken_code_samples import BROKEN_SAMPLES
from app.core.reliability.runner import run_reliability_checks
from app.core.security.runner import run_security
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: runs the full benchmark suite end to end and returns one combined results dict
def run_all_benchmarks() -> dict:
    ''' performance timings, then accuracy detection rates, then repair success — same order they'd run in the real pipeline '''

    print("Starting Shinrai Benchmarks...\n")

    # ========== PERFORMANCE BENCHMARKS ==========
    print("Performance Benchmarks...\n")

    sample_prompt = "Write a FastAPI endpoint for user registration"
    sample_code = BROKEN_SAMPLES[0]

    gen_bench = TimingBenchmark.benchmark_generation(sample_prompt, iterations=5)
    print(f"  Code Generation: {gen_bench['avg_ms']:.2f}ms (avg)")

    rel_bench = TimingBenchmark.benchmark_reliability(sample_code, iterations=10)
    print(f"  Reliability Checks: {rel_bench['avg_ms']:.2f}ms (avg)")

    sec_bench = TimingBenchmark.benchmark_security(sample_code, iterations=10)
    print(f"  Security Checks: {sec_bench['avg_ms']:.2f}ms (avg)")

    # FLOW-1: confidence aggregation needs one real reliability + security report to time against — reuse the sample code
    rel_sample = run_reliability_checks(sample_code)
    sec_sample = run_security(sample_code)
    conf_bench = TimingBenchmark.benchmark_confidence(rel_sample, sec_sample, iterations=50)
    print(f"  Confidence Aggregation: {conf_bench['avg_ms']:.2f}ms (avg)\n")

    # ========== ACCURACY BENCHMARKS ==========
    print("Accuracy Benchmarks...\n")

    rel_accuracy = ReliabilityAccuracy.test_broken_code_detection()
    print(f"  Reliability Detection Rate: {rel_accuracy['detection_rate']}")

    rel_validation = ReliabilityAccuracy.test_secure_code_validation()
    print(f"  Secure Code Validation Rate: {rel_validation['validation_rate']}")

    sec_secrets = SecurityAccuracy.test_secret_detection()
    print(f"  Secret Detection Rate: {sec_secrets['detection_rate']}")

    sec_patterns = SecurityAccuracy.test_dangerous_pattern_detection()
    print(f"  Dangerous Pattern Detection: {sec_patterns['detection_rate']}\n")

    # ========== REPAIR SUCCESS ==========
    print("Repair Benchmarks...\n")

    repair_bench = RepairSuccess.test_repair_success()
    print(f"  Auto-Repair Success Rate: {repair_bench['repair_success_rate']}")
    print(f"  Avg Score Improvement: {repair_bench['avg_score_improvement']} points\n")

    # ========== COMPILE RESULTS ==========
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "performance": {
            "code_generation": gen_bench,
            "reliability_checks": rel_bench,
            "security_checks": sec_bench,
            "confidence_aggregation": conf_bench,
        },
        "accuracy": {
            "reliability_detection": rel_accuracy,
            "secure_code_validation": rel_validation,
            "secret_detection": sec_secrets,
            "dangerous_pattern_detection": sec_patterns,
        },
        "repair": repair_bench,
        "summary": {
            "pipeline_avg_time_ms": round(
                gen_bench["avg_ms"] + rel_bench["avg_ms"] + sec_bench["avg_ms"] + conf_bench["avg_ms"],
                2,
            ),
            "detection_accuracy": round(
                (
                    float(rel_accuracy["detection_rate"].strip("%"))
                    + float(sec_secrets["detection_rate"].strip("%"))
                    + float(sec_patterns["detection_rate"].strip("%"))
                ) / 3,
                2,
            ),
            "repair_success_rate": repair_bench["repair_success_rate"],
        },
    }

    print("All benchmarks complete!\n")

    return results
# =========== FUNCTION ===========


if __name__ == "__main__":
    results = run_all_benchmarks()

    os.makedirs(BenchmarkConfig.RESULTS_DIR, exist_ok=True)

    with open(BenchmarkConfig.REPORT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Report saved to: {BenchmarkConfig.REPORT_FILE}")
