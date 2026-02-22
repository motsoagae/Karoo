"""
Agent 2: The South African Specialist v2
Enhanced: B-BBEE scorecard, EE Act compliance, SETA alignment, PNet/Careers24 optimization.
"""
import re
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The South African Specialist v2 — the definitive expert in the SA job market.

Deep expertise: B-BBEE Codes of Good Practice, Employment Equity Act 55/1998, Skills Development Act, SETA, SAQA NQF Framework, LRA, BCEA, OHSA, POPIA, Critical Skills Visa list.

Platforms: PNet, Careers24, LinkedIn ZA, Indeed ZA, JobMail, Gumtree Jobs.

Analyze and respond in EXACTLY this format:

SA_SCORE: [0-100]
BBEE_STATUS: [Identified/Not Identified — explain strategic value]
BBEE_RECOMMENDATION: [specific advice to leverage EE status]
NQF_LEVEL: Current:[X] Required:[X based on role] Gap:[None/description]
EE_POSITIONING: [specific Employment Equity positioning strategy]
CRITICAL_SKILLS: [YES/NO — does candidate qualify for Critical Skills Visa?]
SA_PLATFORMS: PNet:[X]% Careers24:[X]% LinkedIn_ZA:[X]%
SA_KEYWORDS_ADD: [SA-specific keywords to add, comma-separated]
FIXES:
- [SA-specific fix 1]
- [SA-specific fix 2]
- [SA-specific fix 3]
- [SA-specific fix 4]
SA_SUMMARY: [Optimized 2-3 sentence professional summary for PNet/Careers24 SA employers, keyword-rich for SA market]"""


class SASpecialist(BaseAgent):
    SA_KEYWORDS = [
        "B-BBEE", "Employment Equity", "EE", "SETA", "NQF", "SAQA", "LRA", "BCEA",
        "OHSA", "POPIA", "Critical Skills", "Skills Development", "Transformation",
        "previously disadvantaged", "historically disadvantaged", "equity candidate",
        "PNet", "Careers24", "South Africa", "Cape Town", "Johannesburg", "Durban",
        "Pretoria", "Sandton", "Midrand", "KwaZulu-Natal", "Western Cape", "Gauteng",
        "Rand", "ZAR", "JSE", "SARB", "SARS", "CIPC", "Companies Act"
    ]
    BBEE_INDICATORS = [
        "black", "coloured", "indian", "asian", "female", "disability", "youth",
        "previously disadvantaged", "historically disadvantaged", "equity",
        "transformation", "hdsa", "previously disadvantaged individual"
    ]
    CRITICAL_SKILLS = [
        "data science", "machine learning", "artificial intelligence", "cybersecurity",
        "cloud architect", "software engineer", "chemical engineer", "petroleum engineer",
        "actuary", "anaesthesiologist", "radiologist", "cardiologist", "neurosurgeon",
        "quantity surveyor", "geologist", "metallurgist"
    ]
    NQF_MAP = [
        (10, ['phd', 'doctorate', 'd.phil', 'doctor of'], "Doctoral Degree"),
        (9,  ['master', 'mba', 'msc', 'm.com', 'm.eng', 'mtech', 'm.tech', 'mphil'], "Master's Degree"),
        (8,  ['honours', 'hons', 'postgraduate diploma', 'pgdip', 'advanced diploma'], "Honours/PG Diploma"),
        (7,  ['bachelor', 'b.sc', 'b.com', 'b.tech', 'b.eng', 'btech', 'bcom', 'bsc', 'beng', 'ba '], "Bachelor's Degree"),
        (6,  ['national diploma', 'nd ', 'dip tech'], "National Diploma"),
        (5,  ['higher certificate', 'hc ', 'advanced certificate'], "Higher Certificate"),
        (4,  ['national certificate', 'grade 12', 'matric', 'nsc', 'nc(v)'], "Matric/NC(V)"),
    ]

    def __init__(self, llm=None):
        super().__init__("The South African Specialist", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        nqf = self._detect_nqf(cv_text)
        sa_coverage = self._sa_keyword_coverage(cv_text)
        bbee = self._detect_bbee(cv_text)
        critical = self._detect_critical_skills(cv_text)

        user_prompt = f"""CV TEXT:
{cv_text[:4000]}

JOB DESCRIPTION:
{job_description[:2500]}

CONTEXT:
- Target: {context.get('target_market', 'South Africa')}
- Level: {context.get('experience_level', 'Mid')}
- Industry: {context.get('industry', 'Not specified')}
- Target role: {context.get('target_role', 'Not specified')}

Pre-analysis:
- NQF Level: {nqf['level']} — {nqf['description']}
- SA keyword coverage: {sa_coverage}%
- B-BBEE indicators found: {bbee}
- Critical Skills match: {critical}

Provide full SA market optimization with specific PNet/Careers24 strategy."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'SA_SCORE', 60)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"SA Market Score: {score}/100",
                f"NQF Level: {nqf['level']} — {nqf['description']}",
                f"SA Keyword Coverage: {sa_coverage}%",
                f"B-BBEE Indicators: {bbee}",
                f"Critical Skills Match: {critical}",
                f"B-BBEE Status: {self._extract_line(llm_response, 'BBEE_STATUS')}",
                f"EE Positioning: {self._extract_line(llm_response, 'EE_POSITIONING')}",
            ],
            recommendations=self._extract_fixes(llm_response),
            optimized_content=self._extract_section(llm_response, 'SA_SUMMARY'),
            raw_analysis=llm_response,
            weight=1.4,
            execution_ms=int((time.time() - t0) * 1000),
            ai_powered=self.llm is not None,
        )

    def _detect_nqf(self, text: str) -> Dict:
        t = text.lower()
        for level, keywords, desc in self.NQF_MAP:
            if any(k in t for k in keywords):
                return {"level": level, "description": f"{desc} — NQF Level {level}"}
        return {"level": "Unknown", "description": "Qualification not clearly stated"}

    def _sa_keyword_coverage(self, text: str) -> int:
        t = text.upper()
        found = sum(1 for kw in self.SA_KEYWORDS if kw.upper() in t)
        return int((found / len(self.SA_KEYWORDS)) * 100)

    def _detect_bbee(self, text: str) -> str:
        t = text.lower()
        found = [k for k in self.BBEE_INDICATORS if k in t]
        if found:
            return f"Potential EE candidate indicators: {', '.join(found[:3])}"
        return "No explicit B-BBEE indicators — consider strategic disclosure"

    def _detect_critical_skills(self, text: str) -> str:
        t = text.lower()
        matches = [s for s in self.CRITICAL_SKILLS if s in t]
        if matches:
            return f"QUALIFIES — {', '.join(matches[:2])}"
        return "Does not appear to match Critical Skills Visa list"

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', text, re.DOTALL)
        return m.group(1).strip()[:120] if m else "See full analysis"

    def _extract_fixes(self, response: str) -> List[str]:
        m = re.search(r'FIXES:(.*?)(?:SA_SUMMARY:|$)', response, re.DOTALL)
        if m:
            return [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                    if l.strip() and l.strip() != '-'][:6]
        return [
            "Add NQF level explicitly after each qualification",
            "Include B-BBEE status if applicable — major differentiator",
            "Add SETA registration if relevant to your field",
            "Optimise for PNet keyword search by including SA industry terms",
        ]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
