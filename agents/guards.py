import re
from typing import List

class SecurityGuards:
    @staticmethod
    def InputGuard(order_id: str, customer_id: str, disruptions: List[str]) -> bool:
        """Inspect context for prompt injections or SQL injection keywords."""
        malicious_patterns = [r"ignore all previous instructions", r"drop table", r"system prompt", r"UNION SELECT", r"OR 1=1"]
        for item in [order_id, customer_id] + disruptions:
            if not item: continue
            item_lower = item.lower()
            if any(re.search(pat, item_lower) for pat in malicious_patterns):
                return False
        return True

    @staticmethod
    def OutputGuard(response_text: str) -> bool:
        """Sanitize LLM output. Reject hazardous or error structures."""
        if not response_text or "Error" in response_text[:10] or "malicious" in response_text.lower():
            return False
        return True
