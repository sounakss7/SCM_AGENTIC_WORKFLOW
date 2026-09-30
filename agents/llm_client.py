"""Explicit Multi-Model LLM Routing Client (Gemini 2.5 Flash vs Groq Llama-3).

Routes tasks dynamically based on latency vs reasoning requirements:
- Gemini 2.5 Flash: Reasoning-heavy steps (Risk Assessment, Operational Briefing)
- Groq Llama 3.3 / 8B: Latency-sensitive validation steps (Feasibility Constraint Checking)

Provides seamless local emulation if API keys are absent, guaranteeing 100% testable
reproducibility and tracking exact model call telemetry.
"""

import os
import time
import json
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel, Field

# Check environment keys
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_KEY = os.environ.get("GROQ_API_KEY")


class LLMCallRecord(BaseModel):
    agent_name: str
    target_provider: str  # "gemini" or "groq"
    model_name: str
    prompt_snippet: str
    response_snippet: str
    latency_sec: float
    simulated: bool = False


class HybridLLMClient:
    """Manages explicit model routing between Google Gemini 2.5 Flash and Groq."""

    def __init__(self):
        self.call_history: list[LLMCallRecord] = []

    def call_gemini_reasoning(self, agent_name: str, prompt: str, mock_fallback: str) -> Tuple[str, LLMCallRecord]:
        """Call Gemini 2.5 Flash for high-reasoning operational assessment or briefing."""
        t0 = time.perf_counter()
        model_name = "gemini-2.5-flash"
        is_sim = True
        response_text = mock_fallback

        if GEMINI_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_KEY)
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if resp.text:
                    response_text = resp.text
                    is_sim = False
            except Exception:
                response_text = mock_fallback
                is_sim = True
        else:
            # Deterministic local latency simulation for reasoning (~40ms)
            time.sleep(0.040)

        elapsed = time.perf_counter() - t0
        record = LLMCallRecord(
            agent_name=agent_name,
            target_provider="Google DeepMind / Gemini",
            model_name=model_name,
            prompt_snippet=prompt[:80] + "...",
            response_snippet=response_text[:80] + "...",
            latency_sec=round(elapsed, 4),
            simulated=is_sim
        )
        self.call_history.append(record)
        return response_text, record

    def call_groq_fast_validator(self, agent_name: str, prompt: str, mock_fallback: str) -> Tuple[str, LLMCallRecord]:
        """Call Groq (Llama 3.3 70B / 8B) for ultra-low latency plan constraint validation."""
        t0 = time.perf_counter()
        model_name = "llama-3.3-70b-versatile"
        is_sim = True
        response_text = mock_fallback

        if GROQ_KEY:
            try:
                from groq import Groq
                client = Groq(api_key=GROQ_KEY)
                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_name,
                    max_tokens=256
                )
                if chat.choices and chat.choices[0].message.content:
                    response_text = chat.choices[0].message.content
                    is_sim = False
            except Exception:
                response_text = mock_fallback
                is_sim = True
        else:
            # Low latency simulation for Groq (~12ms)
            time.sleep(0.012)

        elapsed = time.perf_counter() - t0
        record = LLMCallRecord(
            agent_name=agent_name,
            target_provider="Groq LPU Inference",
            model_name=model_name,
            prompt_snippet=prompt[:80] + "...",
            response_snippet=response_text[:80] + "...",
            latency_sec=round(elapsed, 4),
            simulated=is_sim
        )
        self.call_history.append(record)
        return response_text, record


llm_router = HybridLLMClient()
