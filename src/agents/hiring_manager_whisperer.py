"""Agent 5: Hiring Manager Whisperer v2"""
import re, time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Hiring Manager Whisperer v2 — you think exactly like a senior hiring manager doing a technical deep-dive.

Respond in EXACTLY this format:

HM_SCORE: [0-100]
TECHNICAL_CLAIMS: [count]
EVIDENCED_CLAIMS: [count with evidence]
VAGUE_SKILLS: [comma-separated OR NONE]
PORTFOLIO_PRESENT: [YES/NO]
CULTURE_FIT_SIGNALS: [positive culture indicators found OR NONE]
SENIORITY_MATCH: [UNDER/MATCH/OVER-qualified — with reason]
CONVERSATION_STARTERS:
- [interview question from CV]
- [interview question from CV]
- [interview question from CV]
FIXES:
- [fix 1]
- [fix 2]
- [fix 3]
EVIDENCE_REWRITE: [Rewrite their weakest technical claim with full context: what built, what tools, what scale, what outcome]"""

VAGUE_PATTERNS = [r'experienced? in ([A-Za-z\s\.\/\+]{3,25})',r'knowledge of ([A-Za-z\s\.\/\+]{3,25})',r'familiar with ([A-Za-z\s\.\/\+]{3,25})',r'proficient in ([A-Za-z\s\.\/\+]{3,25})',r'understanding of ([A-Za-z\s\.\/\+]{3,25})',r'exposure to ([A-Za-z\s\.\/\+]{3,25})',r'worked with ([A-Za-z\s\.\/\+]{3,25})']


class HiringManagerWhisperer(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Hiring Manager Whisperer", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0=time.time()
        vague=self._find_vague(cv_text)
        has_portfolio=bool(re.search(r'github|gitlab|portfolio|bitbucket|behance|dribbble',cv_text,re.IGNORECASE))
        has_metrics=bool(re.search(r'\d+%|\$\d+|R\s?\d+|saved|reduced|increased|achieved',cv_text,re.IGNORECASE))
        seniority=self._check_seniority(cv_text,context)

        user_prompt=f"""CV:\n{cv_text[:4000]}\n\nJD:\n{job_description[:2000]}\n\nContext:\n- Level: {context.get('experience_level','Mid')}\n- Industry: {context.get('industry','N/A')}\n\nPre-analysis:\n- Vague: {', '.join(vague) if vague else 'None'}\n- Portfolio: {has_portfolio}\n- Metrics: {has_metrics}\n- Seniority match: {seniority}"""

        llm_response=self._get_llm_response(SYSTEM_PROMPT,user_prompt)
        score=self._extract_int(llm_response,'HM_SCORE',60)

        return AgentOutput(
            agent_name=self.name, score=score,
            findings=[
                f"Hiring Manager Appeal: {score}/100",
                f"Vague Skill Claims: {len(vague)} — {', '.join(vague[:3]) if vague else 'None ✓'}",
                f"Portfolio/GitHub: {'✓ Present' if has_portfolio else '✗ Missing — critical for technical roles'}",
                f"Quantified Metrics: {'✓ Present' if has_metrics else '✗ Missing — add numbers'}",
                f"Seniority Alignment: {seniority}",
                f"Technical Claims: {self._extract_line(llm_response,'TECHNICAL_CLAIMS')} total, {self._extract_line(llm_response,'EVIDENCED_CLAIMS')} evidenced",
                f"Culture Signals: {self._extract_line(llm_response,'CULTURE_FIT_SIGNALS')}",
            ],
            recommendations=self._extract_fixes(llm_response,vague,has_portfolio),
            optimized_content=self._extract_section(llm_response,'EVIDENCE_REWRITE'),
            raw_analysis=llm_response, weight=1.2,
            execution_ms=int((time.time()-t0)*1000), ai_powered=self.llm is not None,
        )

    def _find_vague(self, t):
        found=[]
        for p in VAGUE_PATTERNS:
            found.extend([m.strip() for m in re.findall(p,t,re.IGNORECASE) if len(m.strip())>2])
        return list(set(found))[:8]
    def _check_seniority(self, cv, ctx):
        level=ctx.get('experience_level','Mid').lower()
        m=re.search(r'(\d+)\+?\s*years?',cv,re.IGNORECASE)
        if m:
            yrs=int(m.group(1)); exp={'entry':2,'mid':5,'senior':10,'executive':18}.get(level.split()[0],5)
            if yrs<exp-2: return f"Under-experienced ({yrs}yr vs {exp}yr expected for {level})"
            if yrs>exp+6: return f"Potentially overqualified ({yrs}yr) — address proactively"
        return "Seniority appears well-matched"
    def _extract_int(self, t, k, d): m=re.search(rf'{k}:\s*(\d+)',t); return int(m.group(1)) if m else d
    def _extract_line(self, t, k): m=re.search(rf'{k}:\s*(.+?)(?:\n|$)',t); return m.group(1).strip()[:80] if m else "N/A"
    def _extract_fixes(self, r, vague, portfolio):
        fixes=[]
        m=re.search(r'FIXES:(.*?)(?:EVIDENCE_REWRITE:|$)',r,re.DOTALL)
        if m: fixes=[l.strip().lstrip('- ') for l in m.group(1).strip().split('\n') if l.strip() and l.strip()!='-'][:5]
        if not portfolio: fixes.insert(0,"Add GitHub/portfolio URL — hiring managers verify technical claims immediately")
        for skill in vague[:2]: fixes.append(f'Expand "{skill.strip()}" — add project context, scale, outcome')
        return fixes[:8]
    def _extract_section(self, r, k): m=re.search(rf'{k}:\s*(.+?)(?:\n[A-Z_]+:|$)',r,re.DOTALL); return m.group(1).strip() if m else ""
