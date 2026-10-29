import re
from typing import List, Any, Tuple, Optional

class SecurityGuards:
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"disregard\s+(?:all\s+)?(?:previous|prior|your)\s+(?:instructions|rules)",
        r"bypass\s+(?:all\s+)?(?:security|guardrails|safety)",
        r"system\s+(?:prompt|instructions)",
        r"reveal\s+(?:your\s+)?(?:system\s+)?prompt",
        r"you\s+are\s+now\s+(?:a|an)?\b",
        r"switch\s+to\s+(?:developer|unrestricted|god|dan)\s+mode",
        r"\bdan\s+mode\b",
        r"do\s+anything\s+now",
    ]

    SQL_INJECTION_PATTERNS = [
        r"\bdrop\s+table\b",
        r";\s*(?:drop|delete|insert|update|alter|truncate|create)\b",
        r"\bunion\s+(?:all\s+)?select\b",
        r"\bor\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?",
        r"--(?:\s|$)",
        r"/\*.*?\*/",
        r"\bexec\s*\(",
        r"\bxp_cmdshell\b",
        r"'\s*or\s*'\w+'\s*=\s*'\w+",
    ]

    XSS_PATTERNS = [
        r"<script.*?>",
        r"javascript\s*:",
        r"on(?:error|load|click|mouseover)\s*=",
    ]

    ALL_PATTERNS = PROMPT_INJECTION_PATTERNS + SQL_INJECTION_PATTERNS + XSS_PATTERNS

    @classmethod
    def validate_input(cls, item: Any) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates a single string or recursive container.
        Returns:
            Tuple of (is_safe: bool, threat_type: Optional[str], matched_pattern: Optional[str])
        """
        if item is None:
            return True, None, None

        if isinstance(item, (list, tuple, set)):
            for sub_item in item:
                safe, threat, pat = cls.validate_input(sub_item)
                if not safe:
                    return False, threat, pat
            return True, None, None

        if isinstance(item, dict):
            for k, v in item.items():
                safe, threat, pat = cls.validate_input(k)
                if not safe:
                    return False, threat, pat
                safe, threat, pat = cls.validate_input(v)
                if not safe:
                    return False, threat, pat
            return True, None, None

        text = str(item)
        if not text.strip():
            return True, None, None

        # 1. SQL Injection check
        for pat in cls.SQL_INJECTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return False, "SQL_INJECTION", pat

        # 2. Prompt Injection check
        for pat in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return False, "PROMPT_INJECTION", pat

        # 3. XSS check
        for pat in cls.XSS_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return False, "XSS_ATTACK", pat

        return True, None, None

    @classmethod
    def InputGuard(cls, *args, **kwargs) -> bool:
        """
        Inspect all inputs for prompt injections, stacked SQL injections, or XSS vectors.
        Backwards-compatible with InputGuard(order_id, customer_id, disruptions).
        """
        for arg in args:
            safe, _, _ = cls.validate_input(arg)
            if not safe:
                return False

        for k, v in kwargs.items():
            safe, _, _ = cls.validate_input(v)
            if not safe:
                return False

        return True

    @staticmethod
    def OutputGuard(response_text: str) -> bool:
        """Sanitize LLM output. Reject hazardous, empty, or error structures."""
        if not response_text or not isinstance(response_text, str):
            return False
        cleaned = response_text.strip()
        if not cleaned:
            return False

        # Check error prefixes
        error_prefixes = ("error:", "exception:", "traceback", "fatal:", "[error]", "[exception]")
        cleaned_lower = cleaned.lower()
        if any(cleaned_lower.startswith(prefix) for prefix in error_prefixes):
            return False

        # Check for leaked threat injection tokens or leaked system prompt
        leak_markers = (
            "malicious injection",
            "ignore all previous instructions",
            "<script",
            "system prompt",
            "system instructions",
            "internal instructions",
            "reveal prompt"
        )
        if any(marker in cleaned_lower for marker in leak_markers):
            return False

        return True
