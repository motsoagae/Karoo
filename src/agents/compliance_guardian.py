"""Agent 7: Compliance Guardian v2"""
import re, time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Compliance Guardian v2 — legal ethics enforcer. GDPR, POPIA, SA labour law, truth verification.

Respond in EXACTLY this format:

COMPLIANCE_SCORE: [0-100]
LEGAL_RISKS: [comma-separated OR NONE]
GDPR_STATUS: [COMPLIANT/PARTIAL/NON-COMPLIANT — reason]
POPIA_STATUS: [COMPLIANT/PARTIAL/NON-COMPLIANT — reason]
TRUTH_FLAGS: [suspicious claims OR NONE]
SENSITIVE_DATA: [items to remove OR NONE]
DISCRIMINATION_RISKS: [any content that could expose candidate to bias OR NONE]
FIXES:
- [fix 1]
- [fix 2]
- [fix 3]
SANITIZED_SUMMARY: [Rewrite professional summary removing any legally risky content]"""

SENSITIVE_PATTERNS = {
    'SA ID number': r'\b\d{13}\b',
    'date of birth': r'\bDOB\b|\bdate of birth\b|\bborn:\s*\d',
    'marital status': r'\b(married|single|divorced|widowed|separated)\b',
    'religion': r'\b(christian|muslim|jewish|hindu|buddhist|catholic|protestant|atheist)\b',
    'home address': r'\b\d{1,5}\s+\w+\s+(street|road|avenue|drive|lane|close|crescent)\b',
    'photo reference': r'\[photo\]|\[image\]|photograph enclosed',
    'salary history': r'previous salary|salary history|current salary:\s*R',
    'id/passport explicit': r'\bID\s*number\s*:\s*\d|\bpassport\s*:\s*[A-Z]\d',
    'race/ethnicity explicit': r'\brace:\s*\w+|\bethnicity:\s*\w+',
    'disability explicit': r'\bdisability:\s*\w+',
}
EXAGGERATION_FLAGS = [
    (r'\b(guru|ninja|rockstar|wizard|unicorn|guru)\b', 'Unprofessional buzzword'),
    (r'\b100%\s+(success rate|client satisfaction|accuracy)\b', 'Unverifiable 100% claim'),
    (r'saved\s+\$\s*\d{8,}', 'Implausibly large savings — verify'),
    (r'increased\s+revenue\s+by\s+\d{3,}%', 'Very high % — ensure verifiable'),
    (r'managed\s+budget\s+of\s+[R\$]\s*\d{10,}', 'Unusually large budget claim'),
]


class ComplianceGuardian(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Compliance Guardian", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0=time.time()
        sensitive=self._find_sensitive(cv_text)
        truth_flags=self._flag_exaggerations(cv_text)
        gdpr=self._gdpr_status(sensitive)
        popia=self._popia_status(sensitive)

        user_prompt=f"""CV:\n{cv_text[:4000]}\n\nContext:\n- Market: {context.get('target_market','South Africa')}\n\nPre-analysis:\n- Sensitive data: {', '.join(sensitive) if sensitive else 'None'}\n- Truth flags: {', '.join(truth_flags) if truth_flags else 'None'}\n- GDPR: {gdpr}\n- POPIA: {popia}\n\nFull compliance audit."""

        llm_response=self._get_llm_response(SYSTEM_PROMPT,user_prompt)
        score=self._calc_score(sensitive,truth_flags,llm_response)

        return AgentOutput(
            agent_name=self.name, score=score,
            findings=[
                f"Compliance Score: {score}/100",
                f"GDPR Status: {gdpr}",
                f"POPIA Status: {popia}",
                f"Sensitive Data: {len(sensitive)} items — {', '.join(list(sensitive.keys())[:3]) if sensitive else 'None ✓'}",
                f"Truth/Accuracy Flags: {len(truth_flags)} — {', '.join(truth_flags[:2]) if truth_flags else 'None ✓'}",
            ],
            recommendations=self._extract_fixes(llm_response,sensitive,truth_flags),
            optimized_content=self._extract_section(llm_response,'SANITIZED_SUMMARY'),
            raw_analysis=llm_response, weight=1.0,
            execution_ms=int((time.time()-t0)*1000), ai_powered=self.llm is not None,
        )

    def _find_sensitive(self, t):
        return {l:p for l,p in SENSITIVE_PATTERNS.items() if re.search(p,t,re.IGNORECASE)}
    def _flag_exaggerations(self, t):
        return [l for p,l in EXAGGERATION_FLAGS if re.search(p,t,re.IGNORECASE)]
    def _gdpr_status(self, s):
        risks=[k for k in s if k in ['marital status','religion','date of birth','photo reference','race/ethnicity explicit']]
        if risks: return f"NON-COMPLIANT — {', '.join(risks)}"
        if s: return "PARTIAL — minor concerns"
        return "COMPLIANT ✓"
    def _popia_status(self, s):
        risks=[k for k in s if k in ['SA ID number','home address','id/passport explicit']]
        if risks: return f"NON-COMPLIANT — {', '.join(risks)}"
        return "COMPLIANT ✓"
    def _calc_score(self, s, flags, r):
        m=re.search(r'COMPLIANCE_SCORE:\s*(\d+)',r)
        if m: return int(m.group(1))
        return max(20,min(100,100-(len(s)*10)-(len(flags)*5)))
    def _extract_fixes(self, r, s, flags):
        fixes=[]
        m=re.search(r'FIXES:(.*?)(?:SANITIZED_SUMMARY:|$)',r,re.DOTALL)
        if m: fixes=[l.strip().lstrip('- ') for l in m.group(1).strip().split('\n') if l.strip() and l.strip()!='-'][:4]
        for label in list(s.keys())[:3]: fixes.insert(0,f"REMOVE immediately: {label} — never required on a CV")
        for flag in flags[:2]: fixes.append(f"Review accuracy: {flag}")
        return fixes[:8]
    def _extract_section(self, r, k): m=re.search(rf'{k}:\s*(.+?)(?:\n[A-Z_]+:|$)',r,re.DOTALL); return m.group(1).strip() if m else ""
