"""
Agent 12 (NEW): The CV Rewriter
Full AI-powered CV rewrite — not just suggestions, actual complete rewritten CVs.
"""
import re
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

ATS_MAX_PROMPT = """You are The CV Rewriter — ATS-MAX mode.
Rewrite this CV optimised for maximum ATS score (95%+ parse rate).

Rules:
- Plain text only. No tables. No columns. No special characters.
- Standard sections: PROFESSIONAL SUMMARY | WORK EXPERIENCE | EDUCATION | SKILLS | CERTIFICATIONS
- First bullet of each role MUST start with a power verb + number
- Integrate ALL missing keywords naturally (do not keyword stuff)
- Remove all "responsible for", "duties included", "worked on"
- Every achievement needs: Action Verb + Context + Metric
- Professional Summary: 2-3 sentences, keyword-dense, ATS-first
- Format dates as: Month YYYY – Month YYYY

Output ONLY the rewritten CV. No preamble. No explanation. Start immediately with candidate name."""

BALANCED_PROMPT = """You are The CV Rewriter — BALANCED mode.
Rewrite this CV for maximum impact with both ATS systems AND human readers.

Rules:
- Clean, scannable formatting. Simple bullet points.  
- Power verbs + metrics on every achievement
- Strong career narrative in the summary
- Keywords from JD integrated naturally throughout
- Show personality and progression, not just duties
- Each role: 3-5 bullets max. Quality > quantity.
- Remove all weak language. Every word must earn its place.

Output ONLY the rewritten CV. No preamble. Start with candidate name."""

CREATIVE_PROMPT = """You are The CV Rewriter — CREATIVE mode.
Rewrite this CV for maximum human appeal — startups, agencies, creative and leadership roles.

Rules:
- Compelling career narrative opening
- Conversational but professional tone
- Lead with impact and story, not just titles
- Showcase personality and unique value proposition
- Results and achievements front and centre
- LinkedIn-style profile section
- Still ATS-friendly (75-85% score target)

Output ONLY the rewritten CV. No preamble. Start with candidate name."""


class CVRewriterAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The CV Rewriter", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        missing_kw = context.get('_missing_keywords', [])
        agent_insights = context.get('_agent_insights', {})

        base_context = f"""CANDIDATE CV:
{cv_text[:5000]}

JOB DESCRIPTION:
{job_description[:2500]}

OPTIMIZATION CONTEXT:
- Target Market: {context.get('target_market', 'South Africa')}
- Experience Level: {context.get('experience_level', 'Mid')}
- Industry: {context.get('industry', 'Not specified')}
- Missing Keywords to Add: {', '.join(missing_kw[:15])}
- Agent Insights: {agent_insights}

Rewrite the complete CV now:"""

        ats_cv = self._get_llm_response(ATS_MAX_PROMPT, base_context)
        balanced_cv = self._get_llm_response(BALANCED_PROMPT, base_context)
        creative_cv = self._get_llm_response(CREATIVE_PROMPT, base_context)

        return AgentOutput(
            agent_name=self.name,
            score=85 if self.llm else 0,
            findings=[
                f"CV Rewrite: {'AI-Powered ✓' if self.llm else 'Requires API key'}",
                f"ATS-MAX Version: {'Generated' if ats_cv and 'Rule-based' not in ats_cv else 'Requires AI'}",
                f"Balanced Version: {'Generated' if balanced_cv and 'Rule-based' not in balanced_cv else 'Requires AI'}",
                f"Creative Version: {'Generated' if creative_cv and 'Rule-based' not in creative_cv else 'Requires AI'}",
                f"Missing Keywords Integrated: {len(missing_kw)}",
            ],
            recommendations=[
                "Review AI rewrites carefully — verify all facts are accurate",
                "Customize company names, dates, and specific metrics before sending",
                "Add LinkedIn URL and portfolio links if missing",
            ],
            optimized_content=f"ATS_MAX_CV_START\n{ats_cv}\nATS_MAX_CV_END\n\nBALANCED_CV_START\n{balanced_cv}\nBALANCED_CV_END\n\nCREATIVE_CV_START\n{creative_cv}\nCREATIVE_CV_END",
            raw_analysis=f"ats_max={ats_cv}\nbalanced={balanced_cv}\ncreative={creative_cv}",
            weight=2.0,
            execution_ms=int((time.time() - t0) * 1000),
            ai_powered=self.llm is not None,
        )

    def get_variant(self, raw: str, variant: str) -> str:
        markers = {
            'ats_max': ('ATS_MAX_CV_START', 'ATS_MAX_CV_END'),
            'balanced': ('BALANCED_CV_START', 'BALANCED_CV_END'),
            'creative': ('CREATIVE_CV_START', 'CREATIVE_CV_END'),
        }
        start, end = markers.get(variant, ('', ''))
        m = re.search(rf'{start}\n(.*?)\n{end}', raw, re.DOTALL)
        return m.group(1).strip() if m else ""
