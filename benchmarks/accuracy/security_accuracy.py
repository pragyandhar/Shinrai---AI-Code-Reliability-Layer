# WHAT DOES THIS FILE DO: Measures how well the security layer detects hardcoded secrets and dangerous call patterns.

# ================== IMPORTS ==================
from app.core.security.runner import run_security
# ================== IMPORTS ==================


# =========== FUNCTION ===========
# ROLE: runs small labeled sample sets through run_security and checks whether the right sub-score reacted
class SecurityAccuracy:
    ''' each sample is labeled with whether it should trigger a detection, then we check the matching breakdown score '''

    # =========== VARIABLES : known-vulnerable package pins, kept here for a future CVE-detection test against cve_checker ===========
    VULNERABLE_PACKAGES = [
        "requests==2.2.0",      # old version with known CVEs
        "django==1.6.0",        # old version with CVEs
    ]
    # =========== VARIABLES : known-vulnerable package pins, kept here for a future CVE-detection test against cve_checker ===========

    # FLOW-1: secret present should tank secret_detection's score, secret absent should leave it near 100
    @staticmethod
    def test_secret_detection() -> dict:
        ''' four samples, half with a real hardcoded secret and half reading from env vars instead '''

        secret_samples = [
            ('API_KEY = "sk-proj-abc123xyz"', True),
            ('PASSWORD = "admin123"', True),
            ('api_key = get_from_env("API_KEY")', False),
            ('secret = os.environ.get("SECRET")', False),
        ]

        detected = 0
        total = len(secret_samples)

        for code, has_secret in secret_samples:
            report = run_security(code)
            secret_score = report.get("breakdown", {}).get("secret_detection", {}).get("score", 100)

            if has_secret and secret_score < 50:
                detected += 1
            elif not has_secret and secret_score >= 90:
                detected += 1

        return {
            "test": "secret_detection",
            "total_samples": total,
            "detected": detected,
            "detection_rate": f"{detected / total:.2%}",
        }

    # FLOW-2: same idea for dangerous_patterns — os.system/eval/Popen should score low, a safe subprocess.run call shouldn't
    @staticmethod
    def test_dangerous_pattern_detection() -> dict:
        ''' four samples, three dangerous calls and one safe equivalent '''

        pattern_samples = [
            ('os.system("ls")', True),
            ('subprocess.Popen(cmd)', True),
            ('eval(user_input)', True),
            ('subprocess.run(cmd, shell=False)', False),
        ]

        detected = 0
        total = len(pattern_samples)

        for code, has_pattern in pattern_samples:
            report = run_security(code)
            pattern_score = report.get("breakdown", {}).get("dangerous_patterns", {}).get("score", 100)

            if has_pattern and pattern_score < 50:
                detected += 1
            elif not has_pattern and pattern_score >= 90:
                detected += 1

        return {
            "test": "dangerous_pattern_detection",
            "total_samples": total,
            "detected": detected,
            "detection_rate": f"{detected / total:.2%}",
        }
# =========== FUNCTION ===========
