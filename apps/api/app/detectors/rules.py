import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

from app.schemas.events import EventCreate


@dataclass(frozen=True)
class DetectionContext:
    recent_auth_failures: int = 0
    recent_request_count: int = 0
    recent_sensitive_paths: int = 0


@dataclass(frozen=True)
class DetectionResult:
    rule_id: str
    attack_type: str
    score: int
    evidence: dict[str, Any]


SCANNER_SIGNATURES = ("sqlmap", "nikto", "nmap", "masscan", "acunetix", "nessus", "wpscan")
SENSITIVE_PATHS = ("/admin", "/wp-login.php", "/phpmyadmin", "/.env", "/config")
SUSPICIOUS_COMMANDS: tuple[tuple[str, re.Pattern[str], int], ...] = (
    ("wget", re.compile(r"(^|\s)wget(\s|$)", re.I), 35),
    ("curl", re.compile(r"(^|\s)curl(\s|$)", re.I), 30),
    ("chmod", re.compile(r"chmod\s+[^\n]*\+x|chmod\s+7{3}", re.I), 35),
    ("reverse_shell", re.compile(r"bash\s+-i|nc(?:at)?\s+.*-[elp]|/dev/tcp/", re.I), 60),
    ("script_exec", re.compile(r"(?:python\s+-c|perl\s+-e|ruby\s+-e)", re.I), 45),
)
CREDENTIAL_TERMS = re.compile(r"/etc/(?:passwd|shadow)|(?:^|[/_.-])(?:credentials?|passwords?|\.env|config)(?:$|[/_.-])", re.I)
SQLI = re.compile(r"(?:\bunion\b\s+\bselect\b|\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+|sleep\s*\(|information_schema|--\s*$)", re.I)
COMMAND_INJECTION = re.compile(r"(?:;|&&|\|\||\$\([^)]*\)|`[^`]+`)")


def analyze_event(event: EventCreate, context: DetectionContext) -> list[DetectionResult]:
    results: list[DetectionResult] = []
    event_type = event.event_type.upper()

    if event_type in {"LOGIN_ATTEMPT", "LOGIN_FAILURE", "AUTH_FAILURE"} and context.recent_auth_failures >= 5:
        results.append(
            DetectionResult(
                "AUTH-BRUTE-001",
                "BRUTE_FORCE",
                55,
                {"failed_logins_60s": context.recent_auth_failures},
            )
        )

    command = event.command or ""
    for name, pattern, score in SUSPICIOUS_COMMANDS:
        if pattern.search(command):
            results.append(
                DetectionResult(f"SSH-CMD-{name.upper()}", "SUSPICIOUS_COMMAND", score, {"indicator": name})
            )

    if command and CREDENTIAL_TERMS.search(command):
        results.append(DetectionResult("CRED-ACCESS-001", "CREDENTIAL_ACCESS", 40, {"command": command[:512]}))

    raw_target = str(event.payload.get("raw_target") or event.payload.get("path") or "")
    decoded_target = unquote(raw_target).lower()
    request_text = " ".join(
        [decoded_target, str(event.payload.get("query_string", "")), str(event.payload.get("body_preview", ""))]
    )

    if event.protocol == "HTTP":
        matched_paths = [path for path in SENSITIVE_PATHS if decoded_target.startswith(path)]
        if matched_paths:
            score = 35 if context.recent_sensitive_paths >= 3 else 20
            results.append(
                DetectionResult(
                    "WEB-SCAN-001",
                    "WEB_SCANNING",
                    score,
                    {"path": decoded_target[:1024], "sensitive_requests_60s": context.recent_sensitive_paths},
                )
            )
        if SQLI.search(request_text):
            results.append(DetectionResult("WEB-SQLI-001", "SQL_INJECTION", 55, {"target": raw_target[:1024]}))
        if "../" in decoded_target or "..\\" in decoded_target:
            results.append(DetectionResult("WEB-TRAV-001", "PATH_TRAVERSAL", 50, {"target": raw_target[:1024]}))
        if COMMAND_INJECTION.search(request_text):
            results.append(DetectionResult("WEB-CMDI-001", "COMMAND_INJECTION", 55, {"target": raw_target[:1024]}))

        user_agent = (event.user_agent or "").lower()
        signature = next((sig for sig in SCANNER_SIGNATURES if sig in user_agent), None)
        if signature:
            results.append(DetectionResult("WEB-UA-001", "SCANNER", 25, {"signature": signature}))
        if context.recent_request_count >= 30:
            results.append(
                DetectionResult(
                    "WEB-RATE-001",
                    "HIGH_FREQUENCY_SCANNING",
                    45,
                    {"requests_60s": context.recent_request_count},
                )
            )

    return _deduplicate(results)


def calculate_risk_score(results: list[DetectionResult]) -> int:
    if not results:
        return 0
    ordered = sorted((result.score for result in results), reverse=True)
    score = ordered[0] + sum(round(value * 0.35) for value in ordered[1:])
    return min(100, score)


def severity_for_score(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def _deduplicate(results: list[DetectionResult]) -> list[DetectionResult]:
    seen: set[tuple[str, str]] = set()
    unique: list[DetectionResult] = []
    for result in results:
        key = (result.rule_id, result.attack_type)
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return unique
