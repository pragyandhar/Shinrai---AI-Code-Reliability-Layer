# WHAT DOES THIS FILE DO: Measures how well reliability checks separate broken code from clean code.

# ================== IMPORTS ==================
from app.core.reliability.runner import run_reliability_checks
from benchmarks.test_datasets.broken_code_samples import BROKEN_SAMPLES, SECURE_SAMPLES
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: runs reliability checks against both sample sets and reports detection/validation rates
class ReliabilityAccuracy:
    ''' two tests — do we flag broken code, and do we leave clean code alone '''

    # FLOW-1: broken code should score low enough to count as "detected" — threshold of 80 matches the spec's own cutoff
    @staticmethod
    def test_broken_code_detection() -> dict:
        ''' runs every BROKEN_SAMPLES entry through run_reliability_checks, expects score < 80 on most of them '''

        detected = 0
        total = len(BROKEN_SAMPLES)
        results = []

        for i, code in enumerate(BROKEN_SAMPLES):
            report = run_reliability_checks(code)
            score = report.get("score", 100)

            is_detected = score < 80
            detected += int(is_detected)

            results.append({
                "sample": i + 1,
                "code_snippet": code[:50] + "...",
                "score": score,
                "detected": is_detected,
            })

        detection_rate = detected / total

        return {
            "test": "broken_code_detection",
            "total_samples": total,
            "detected": detected,
            "detection_rate": f"{detection_rate:.2%}",
            "results": results,
        }

    # FLOW-2: clean code should score high enough to count as "validated" — 80+ means we didn't cry wolf
    @staticmethod
    def test_secure_code_validation() -> dict:
        ''' runs every SECURE_SAMPLES entry through run_reliability_checks, expects score >= 80 on most of them '''

        passed = 0
        total = len(SECURE_SAMPLES)
        results = []

        for i, code in enumerate(SECURE_SAMPLES):
            report = run_reliability_checks(code)
            score = report.get("score", 0)

            is_valid = score >= 80
            passed += int(is_valid)

            results.append({
                "sample": i + 1,
                "code_snippet": code[:50] + "...",
                "score": score,
                "validated": is_valid,
            })

        validation_rate = passed / total

        return {
            "test": "secure_code_validation",
            "total_samples": total,
            "validated": passed,
            "validation_rate": f"{validation_rate:.2%}",
            "results": results,
        }
# =========== FUNCTION ===========
