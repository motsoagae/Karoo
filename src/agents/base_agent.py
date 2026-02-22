"""
Karoo v2.0 — Base Agent
Enhanced with retry logic, structured output validation, and telemetry.
"""
import os
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentOutput(BaseModel):
    agent_name: str = ""
    score: int = 0
    findings: List[str] = []
    recommendations: List[str] = []
    optimized_content: str = ""
    raw_analysis: str = ""
    weight: float = 1.0
    execution_ms: int = 0
    ai_powered: bool = False


class BaseAgent(ABC):
    MAX_RETRIES = 2

    def __init__(self, name: str, llm=None):
        self.name = name
        self.llm = llm

    def _get_llm_response(self, system_prompt: str, user_prompt: str) -> str:
        if not self.llm:
            return self._rule_based_fallback(user_prompt)

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                if attempt < self.MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.warning(f"[{self.name}] LLM attempt {attempt+1} failed ({e}). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"[{self.name}] All LLM retries exhausted: {e}")
                    return self._rule_based_fallback(user_prompt)

    def _rule_based_fallback(self, prompt: str) -> str:
        return (
            f"[Rule-based mode — add GROQ_API_KEY for AI analysis]\n"
            f"Agent: {self.name}\n"
            f"Status: Running keyword and pattern analysis only."
        )

    @abstractmethod
    async def analyze(
        self,
        cv_text: str,
        job_description: str,
        context: Dict[str, Any]
    ) -> AgentOutput:
        pass
