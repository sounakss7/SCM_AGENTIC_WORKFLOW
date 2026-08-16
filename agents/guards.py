import re
from typing import List

class SecurityGuards:
    @staticmethod
    def InputGuard(order_id: str, customer_id: str, disruptions: List[str]) -> bool:
        """Inspect context for prompt injections or SQL injection keywords."""
        malicious_patterns = [
            r"ignore\s+(?:all\s+)?previous\s+instructions",
            r"drop\s+table",
            r"system\s+prompt",
            r"union\s+(?:all\s+)?select",
            r"or\s+1\s*=\s*1",
            r"or\s+'1'\s*=\s*'1'",
            r"--\s*$",
            r"exec\s*\(",
            r"<script.*?>"
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
        if cleaned.startswith("Error:") or cleaned.startswith("Exception:") or "malicious injection" in cleaned.lower():
            return False
        return True

