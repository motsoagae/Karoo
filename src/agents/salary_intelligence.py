"""
Agent 11 (NEW): The Salary Intelligence Agent
Market rate analysis, negotiation strategy, SA + international benchmarks.
"""
import re
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Salary Intelligence Agent — compensation expert for South African and international markets.

You have deep knowledge of:
- SA salary bands by industry, level, and location (2024-2025)
- BBBEE premium for equity candidates (typically 15-25% above market)
- JSE-listed vs private vs public sector compensation structures
- International equivalents (UK, US, AU, UAE, Europe)
- Total cost to company (CTC) vs take-home calculations
- Benefits benchmarking: medical aid, pension, bonus structures
- Salary negotiation psychology

SA Salary Benchmarks 2024-2025 (rough CTC ZAR):
- Graduate/Junior: R180k-R350k CTC
- Mid-level (3-7yr): R350k-R700k CTC
- Senior (8-15yr): R700k-R1.5M CTC
- Executive: R1.5M-R5M+ CTC
- Tech premium: +20-40% above generic roles
- Financial services: +15-30% premium
- Mining/Resources: +10-20% premium
- Cape Town vs JHB: JHB typically 10-15% higher

Respond in EXACTLY this format:

SALARY_SCORE: [0-100] (how well-positioned is this CV to negotiate maximum salary)
MARKET_RATE_SA: Min:[R X] Mid:[R X] Max:[R X] CTC per annum
MARKET_RATE_INTL: UK:[£X] US:[$X] UAE:[AED X] per annum equivalent
PERCENTILE_FIT: [X]th percentile based on experience and skills
NEGOTIATION_POWER: [Weak/Moderate/Strong/Very Strong — with reason]
UNIQUE_VALUE_PROPS: [CV-specific factors that command premium, comma-separated]
NEGOTIATION_SCRIPT: [Exact words to use when asked salary expectations]
BENEFITS_TO_REQUEST: [Must-negotiate benefits for this level/industry, comma-separated]
RED_FLAGS: [factors reducing negotiating power, comma-separated OR NONE]
FIXES:
- [fix to increase earning power]
- [fix to increase earning power]
- [fix to increase earning power]
SALARY_SUMMARY: [2-3 sentence market positioning statement for maximum negotiation leverage]"""

SA_SALARY_BENCHMARKS = {
    'entry': {'min': 180000, 'mid': 265000, 'max': 380000},
    'mid': {'min': 350000, 'mid': 550000, 'max': 750000},
    'senior': {'min': 700000, 'mid': 1100000, 'max': 1600000},
    'executive': {'min': 1500000, 'mid': 2500000, 'max': 5000000},
}
INDUSTRY_PREMIUMS = {
    'fintech': 35, 'finance': 25, 'banking': 25, 'tech': 30,
    'mining': 20, 'engineering': 15, 'healthcare': 10,
    'retail': -10, 'ngo': -20, 'government': -15,
}


class SalaryIntelligence(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Salary Intelligence Agent", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        base = self._calc_base_salary(context)
        premium = self._calc_premium(cv_text, context)
        has_metrics = self._has_strong_metrics(cv_text)
        scarcity = self._skill_scarcity(cv_text, job_description)

        user_prompt = f"""CV TEXT:
{cv_text[:4000]}

JOB DESCRIPTION:
{job_description[:2500]}

CONTEXT:
- Target Market: {context.get('target_market', 'South Africa')}
- Experience Level: {context.get('experience_level', 'Mid')}
- Industry: {context.get('industry', 'Not specified')}
- Target Role: {context.get('target_role', 'Not specified')}

Pre-analysis:
- Estimated base SA salary band: R{base['min']:,} – R{base['max']:,} CTC
- Industry premium adjustment: +{premium}%
- Quantified achievements on CV: {has_metrics}
- Skill scarcity indicator: {scarcity}

Generate precise salary intelligence and negotiation strategy for this specific CV and role.
Provide realistic, market-accurate figures for the South African context."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'SALARY_SCORE', 65)

        adjusted_min = int(base['min'] * (1 + premium / 100))
        adjusted_mid = int(base['mid'] * (1 + premium / 100))
        adjusted_max = int(base['max'] * (1 + premium / 100))

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Salary Negotiation Power: {score}/100",
                f"SA Market Rate (estimated): R{adjusted_min:,} – R{adjusted_max:,} CTC",
                f"Market Mid-Point: R{adjusted_mid:,} CTC per annum",
                f"Industry Premium: +{premium}% ({context.get('industry', 'General')})",
                f"Metrics Strength: {has_metrics}",
                f"Skill Scarcity: {scarcity}",
                f"Negotiation Power: {self._extract_line(llm_response, 'NEGOTIATION_POWER')}",
            ],
            recommendations=self._extract_fixes(llm_response),
            optimized_content=self._extract_section(llm_response, 'NEGOTIATION_SCRIPT'),
            raw_analysis=llm_response,
            weight=0.8,
            execution_ms=int((time.time() - t0) * 1000),
            ai_powered=self.llm is not None,
        )

    def _calc_base_salary(self, context: Dict) -> Dict:
        level = context.get('experience_level', 'Mid').lower()
        if 'entry' in level: return SA_SALARY_BENCHMARKS['entry']
        if 'senior' in level: return SA_SALARY_BENCHMARKS['senior']
        if 'exec' in level: return SA_SALARY_BENCHMARKS['executive']
        return SA_SALARY_BENCHMARKS['mid']

    def _calc_premium(self, cv: str, context: Dict) -> int:
        industry = context.get('industry', '').lower()
        for key, pct in INDUSTRY_PREMIUMS.items():
            if key in industry:
                return pct
        tech_terms = ['python', 'aws', 'kubernetes', 'ml', 'ai ', 'data science', 'cloud']
        if sum(1 for t in tech_terms if t in cv.lower()) >= 3:
            return 25
        return 0

    def _has_strong_metrics(self, cv: str) -> str:
        count = len(re.findall(r'\d+%|\$[\d,]+|R\s?[\d,]+|saved|reduced|increased|grew', cv, re.IGNORECASE))
        if count >= 8: return f"Excellent ({count} quantified achievements)"
        if count >= 4: return f"Good ({count} quantified achievements)"
        if count >= 1: return f"Weak ({count} — add more metrics)"
        return "None — major negotiation weakness"

    def _skill_scarcity(self, cv: str, jd: str) -> str:
        scarce = ['actuari', 'blockchain', 'quantum', 'llm', 'genai', 'kubernetes',
                  'devsecops', 'ml engineer', 'data science', 'cybersecur']
        matches = [s for s in scarce if s in cv.lower()]
        if matches:
            return f"High demand skills: {', '.join(matches[:3])} — strong leverage"
        return "Standard skill profile — differentiate on achievements"

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', text, re.DOTALL)
        return m.group(1).strip()[:150] if m else "See analysis"

    def _extract_fixes(self, response: str) -> List[str]:
        m = re.search(r'FIXES:(.*?)(?:SALARY_SUMMARY:|$)', response, re.DOTALL)
        if m:
            return [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                    if l.strip() and l.strip() != '-'][:5]
        return [
            "Add more quantified achievements — each metric = +5-10% negotiating power",
            "Include LinkedIn profile with recommendations — validates market value",
            "Research the company's remuneration strategy (annual report, Glassdoor SA)",
        ]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
