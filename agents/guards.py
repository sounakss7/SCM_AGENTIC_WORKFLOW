import re
from typing import List

class SecurityGuards:
    @staticmethod
    def InputGuard(order_id: str, customer_id: str, disruptions: List[str]) -> bool:
        """Inspect context for prompt injections, stacked SQL injections, or XSS vectors."""
        malicious_patterns = [
            r"ignore\s+(?:all\s+)?previous\s+instructions",
            r"disregard\s+(?:all\s+)?previous",
            r"bypass\s+(?:all\s+)?(?:security|guardrails)",
            r"system\s+(?:prompt|instructions)",
            r"reveal\s+(?:your\s+)?(?:system\s+)?prompt",
            r"drop\s+table",
            r";\s*(?:drop|delete|insert|update|alter|truncate)\b",
            r"union\s+(?:all\s+)?select",
            r"or\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?",
            r"--(?:\s|$)",
            r"/\*.*?\*/",
            r"exec\s*\(",
            r"<script.*?>",
            r"javascript\s*:",
            r"on(?:error|load|click|mouseover)\s*="
        ]
        items_to_check = [order_id, customer_id] + (disruptions if disruptions else [])
        for item in items_to_check:
            if not item or not isinstance(item, str):
                continue
            for pat in malicious_patterns:
                if re.search(pat, item, re.IGNORECASE):
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
            
        # Check for leaked threat injection tokens
        leak_markers = ("malicious injection", "ignore all previous instructions", "<script")
        if any(marker in cleaned_lower for marker in leak_markers):
            return False
            
        return True


