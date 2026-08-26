# WHAT DOES THIS FILE DO: Measures how often the auto-repair loop actually fixes low-confidence code in one attempt.

# ================== IMPORTS ==================
import statistics

from app.core.reliability.runner import run_reliability_checks
from app.core.security.runner import run_security
from app.core.confidence.aggregator import aggregate_report
from app.core.repair.repairer import repair_code
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: scores code before and after a single repair attempt, reports how many of the fixable cases actually got fixed
class RepairSuccess:
    ''' only codes that started below 40 count as "fixable" — the rest just pass through untouched for comparison '''

    # FLOW-1: two hand-picked broken snippets, each with an obviously fixable issue
    @staticmethod
    def test_repair_success() -> dict:
        ''' scores each snippet, repairs it once if it started below 40, then scores it again '''

        test_cases = [
            ('def divide(a, b):\n    return a / b', "Missing zero check"),
            ('import fake_lib\nprint(fake_lib.func())', "Fake import"),
        ]

        results = []

        for i, (code, description) in enumerate(test_cases):
            # FLOW-2: baseline score before any repair attempt
            rel_before = run_reliability_checks(code)
            sec_before = run_security(code)
            conf_before = aggregate_report(rel_before, sec_before)

            before_score = conf_before.get("confidence_score", 100)

            # FLOW-3: only attempt a repair if the baseline is genuinely bad — matches the pipeline's own threshold
            repaired_code = code

            if before_score < 40:
                try:
                    repaired_code = repair_code(code, conf_before.get("issues", []))
                except Exception:
                    repaired_code = code

            # FLOW-4: re-score whatever we ended up with — repaired_code equals code if repair wasn't attempted or failed
            rel_after = run_reliability_checks(repaired_code)
            sec_after = run_security(repaired_code)
            conf_after = aggregate_report(rel_after, sec_after)

            after_score = conf_after.get("confidence_score", 100)
            improvement = after_score - before_score

            results.append({
                "test_case": i + 1,
                "description": description,
                "before_score": before_score,
                "after_score": after_score,
                "improvement": improvement,
                "fixed": after_score >= 40 if before_score < 40 else "N/A",
            })

        # FLOW-5: success rate only counts cases that actually needed fixing — an already-fine sample can't count as a "fix"
        fixable = [r for r in results if r["before_score"] < 40]

        if fixable:
            fixed_count = len([r for r in fixable if r["fixed"] is True])
            success_rate = fixed_count / len(fixable)
        else:
            fixed_count = 0
            success_rate = 1.0

        avg_improvement = statistics.mean([r["improvement"] for r in results])

        return {
            "test": "repair_success",
            "total_samples": len(results),
            "fixable_samples": len(fixable),
            "fixed_samples": fixed_count,
            "repair_success_rate": f"{success_rate:.2%}",
            "avg_score_improvement": round(avg_improvement, 2),
            "results": results,
        }
# =========== FUNCTION ===========
