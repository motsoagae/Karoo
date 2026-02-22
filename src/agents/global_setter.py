"""Agent 3: Global Standard Setter v2"""
import re, time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Global Standard Setter v2 — international ATS expert for US, UK, EU, APAC, Middle East.

Platforms: Taleo Oracle, iCIMS, Workday, Jobvite, Greenhouse (US); Civil Service Jobs, NHS Jobs (UK); SAP SuccessFactors, XING (EU/DE); SEEK, Seek NZ (APAC); Bayt, GulfTalent (ME).

Respond in EXACTLY this format:

GLOBAL_SCORE: [0-100]
US_SCORE: [0-100] [key issue or strength]
UK_SCORE: [0-100] [key issue]
EU_SCORE: [0-100] [GDPR status]
APAC_SCORE: [0-100] [notes]
ME_SCORE: [0-100] [Gulf market notes]
LINKEDIN_SCORE: [0-100] [profile optimization status]
GDPR_RISKS: [comma-separated risks OR NONE]
MISSING_SECTIONS: [comma-separated missing CV sections OR NONE]
VISA_ELIGIBILITY: [any notable visa/work-right considerations]
FIXES:
- [fix 1]
- [fix 2]
- [fix 3]
- [fix 4]
GLOBAL_SUMMARY: [2-3 sentence international summary — GDPR compliant, ATS-optimized for Workday/Greenhouse]"""

GDPR_PATTERNS = {
    'marital_status': r'\b(married|single|divorced|widowed|separated)\b',
    'religion': r'\b(christian|muslim|jewish|hindu|buddhist|catholic|protestant|atheist)\b',
    'date_of_birth': r'\bDOB\b|date of birth|born:|\bD\.O\.B\b',
    'id_number': r'\b\d{13}\b',
    'photo': r'\[photo\]|\[image\]|photograph',
    'nationality_explicit': r'\bnationality:\s*\w+',
    'gender_explicit': r'\bgender:\s*(male|female|other)\b',
    'race_explicit': r'\brace:\s*\w+|\bethnicity:\s*\w+',
}
REQUIRED_SECTIONS = {
    'contact_info': r'@|email|phone|tel|\+\d',
    'linkedin': r'linkedin\.com',
    'summary_profile': r'summary|objective|profile|about',
    'work_experience': r'experience|employment|work history|career',
    'education': r'education|qualification|degree|university',
    'skills': r'skills|competencies|expertise|technologies',
}


class GlobalSetter(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Global Standard Setter", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        gdpr_risks = self._check_gdpr(cv_text)
        missing = self._check_sections(cv_text)

        user_prompt = f"""CV TEXT:\n{cv_text[:4000]}\n\nJOB DESCRIPTION:\n{job_description[:2000]}\n\nTARGET MARKET: {context.get('target_market', 'International')}\n\nPre-analysis:\n- GDPR risks: {', '.join(gdpr_risks) if gdpr_risks else 'None'}\n- Missing sections: {', '.join(missing) if missing else 'None'}\n\nFull international analysis."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'GLOBAL_SCORE', 70)

        return AgentOutput(
            agent_name=self.name, score=score,
            findings=[
                f"Global Readiness: {score}/100",
                f"US Fortune 500: {self._extract_line(llm_response, 'US_SCORE')}",
                f"UK Civil Service: {self._extract_line(llm_response, 'UK_SCORE')}",
                f"EU GDPR Compliant: {self._extract_line(llm_response, 'EU_SCORE')}",
                f"APAC Ready: {self._extract_line(llm_response, 'APAC_SCORE')}",
                f"LinkedIn Score: {self._extract_line(llm_response, 'LINKEDIN_SCORE')}",
                f"GDPR Risks: {', '.join(gdpr_risks) if gdpr_risks else 'None ✓'}",
                f"Missing Sections: {', '.join(missing) if missing else 'All present ✓'}",
            ],
            recommendations=self._extract_fixes(llm_response, gdpr_risks, missing),
            optimized_content=self._extract_section(llm_response, 'GLOBAL_SUMMARY'),
            raw_analysis=llm_response, weight=1.2,
            execution_ms=int((time.time()-t0)*1000), ai_powered=self.llm is not None,
        )

    def _check_gdpr(self, t): return [n for n,p in GDPR_PATTERNS.items() if re.search(p,t,re.IGNORECASE)]
    def _check_sections(self, t): return [s for s,p in REQUIRED_SECTIONS.items() if not re.search(p,t,re.IGNORECASE)]
    def _extract_int(self, t, k, d):
        m=re.search(rf'{k}:\s*(\d+)',t); return int(m.group(1)) if m else d
    def _extract_line(self, t, k):
        m=re.search(rf'{k}:\s*(.+?)(?:\n|$)',t); return m.group(1).strip()[:80] if m else "N/A"
    def _extract_fixes(self, r, gdpr, miss):
        fixes=[]
        m=re.search(r'FIXES:(.*?)(?:GLOBAL_SUMMARY:|$)',r,re.DOTALL)
        if m: fixes=[l.strip().lstrip('- ') for l in m.group(1).strip().split('\n') if l.strip() and l.strip()!='-'][:5]
        for risk in gdpr: fixes.insert(0,f"REMOVE: {risk.replace('_',' ')} — illegal to include in UK/EU/US CVs")
        for sec in miss: fixes.append(f"ADD: {sec.replace('_',' ')} section — required for international ATS")
        return fixes[:10]
    def _extract_section(self, r, k):
        m=re.search(rf'{k}:\s*(.+?)(?:\n[A-Z_]+:|$)',r,re.DOTALL); return m.group(1).strip() if m else ""
