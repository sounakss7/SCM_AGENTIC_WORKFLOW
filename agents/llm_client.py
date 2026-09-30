"""Explicit Multi-Model LLM Routing Client (Gemini 2.5 Flash vs Groq LPU).

Routes tasks dynamically based on latency vs reasoning requirements:
- Gemini 2.5 Flash / 3.5 Flash: Reasoning-heavy steps (Risk Assessment, Operational Briefing)
- Groq LPU (Qwen 3.8 27B / GPT-OSS 20B): Latency-sensitive validation steps (Feasibility Constraint Checking)

Integrates live Google Gemini and Groq Cloud APIs with robust fallback and exact telemetry.
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel, Field

# Load environment keys from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("llm_client")


def get_gemini_key() -> Optional[str]:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def get_groq_key() -> Optional[str]:
    return os.environ.get("GROQ_API_KEY")


class LLMCallRecord(BaseModel):
    agent_name: str
    target_provider: str  # "Google DeepMind / Gemini" or "Groq LPU Inference"
    model_name: str
    prompt_snippet: str
    response_snippet: str
    latency_sec: float
    simulated: bool = False


class HybridLLMClient:
    """Manages explicit model routing between Google Gemini and Groq LPU."""

    def __init__(self):
        self.call_history: List[LLMCallRecord] = []

    def call_gemini_reasoning(self, agent_name: str, prompt: str, mock_fallback: str) -> Tuple[str, LLMCallRecord]:
        """Call Google Gemini (2.5 Flash / 3.5 Flash Lite) for high-reasoning operational assessment or briefing."""
        t0 = time.perf_counter()
        gemini_key = get_gemini_key()
        response_text = mock_fallback
        chosen_model = "gemini-2.5-flash"
        is_sim = True

        if gemini_key:
            candidate_models = ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
            for model_id in candidate_models:
                try:
                    from google import genai
                    client = genai.Client(api_key=gemini_key)
                    resp = client.models.generate_content(
                        model=model_id,
                        contents=prompt
                    )
                    if resp and resp.text:
                        response_text = resp.text
                        chosen_model = model_id
                        is_sim = False
                        break
                except Exception as e:
                    logger.warning(f"Gemini call to {model_id} failed: {e}. Trying next candidate...")
                    continue

        if is_sim:
            # Deterministic local latency simulation for reasoning (~40ms)
            time.sleep(0.040)

        elapsed = time.perf_counter() - t0
        record = LLMCallRecord(
            agent_name=agent_name,
            target_provider="Google DeepMind / Gemini",
            model_name=chosen_model,
            prompt_snippet=prompt[:80] + "...",
            response_snippet=response_text[:80] + "...",
            latency_sec=round(elapsed, 4),
            simulated=is_sim
        )
        self.call_history.append(record)
        return response_text, record

    def call_groq_fast_validator(self, agent_name: str, prompt: str, mock_fallback: str) -> Tuple[str, LLMCallRecord]:
        """Call Groq (Qwen 3.8 27B / GPT-OSS 20B) for ultra-low latency plan constraint validation."""
        t0 = time.perf_counter()
        groq_key = get_groq_key()
        response_text = mock_fallback
        chosen_model = "qwen/qwen3.8-27b"
        is_sim = True

        if groq_key:
            candidate_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
            for model_id in candidate_models:
                try:
                    from groq import Groq
                    client = Groq(api_key=groq_key)
                    chat = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=model_id,
                        max_tokens=256
                    )
                    if chat.choices and chat.choices[0].message.content:
                        response_text = chat.choices[0].message.content
                        chosen_model = model_id
                        is_sim = False
                        break
                except Exception as e:
                    logger.warning(f"Groq call to {model_id} failed: {e}. Trying next candidate...")
                    continue

        if is_sim:
            # Low latency simulation for Groq (~12ms)
            time.sleep(0.012)

        elapsed = time.perf_counter() - t0
        record = LLMCallRecord(
            agent_name=agent_name,
            target_provider="Groq LPU Inference",
            model_name=chosen_model,
            prompt_snippet=prompt[:80] + "...",
            response_snippet=response_text[:80] + "...",
            latency_sec=round(elapsed, 4),
            simulated=is_sim
        )
        self.call_history.append(record)
        return response_text, record


llm_router = HybridLLMClient()
