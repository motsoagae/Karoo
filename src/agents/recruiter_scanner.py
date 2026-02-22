"""Agent 4: The 6-Second Scanner v2"""
import re, time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The 6-Second Scanner v2 — expert in recruiter psychology, f-pattern scanning, CV first impression.

Respond in EXACTLY this format:

RECRUITER_SCORE: [0-100]
F_PATTERN_SCORE: [0-100]
ACHIEVEMENT_DENSITY: [X metrics per role average]
CV_KILLERS_FOUND: [comma-separated OR NONE]
POWER_VERBS_COUNT: [number]
OPENING_IMPACT: [STRONG/MODERATE/WEAK — what recruiter sees in first 3 seconds]
FIRST_IMPRESSION: [honest 1-sentence recruiter reaction]
SCANNABILITY: [HIGH/MEDIUM/LOW — ease of quick reading]
FIXES:
- [fix 1]
- [fix 2]
- [fix 3]
- [fix 4]
IMPROVED_BULLET: [Take the weakest bullet and rewrite with power verb + context + metric]"""

CV_KILLERS = ["responsible for","duties included","worked on","involved in","helped with",
              "assisted with","contributed to","participated in","tasked with","was responsible",
              "my responsibilities","my duties","i was","i have","i am"]
POWER_VERBS = ["spearheaded","delivered","transformed","exceeded","optimized","engineered",
               "architected","scaled","generated","reduced","led","launched","built","drove",
               "achieved","increased","decreased","saved","negotiated","established",
               "implemented","pioneered","accelerated","overhauled","revolutionized","secured"]


class RecruiterScanner(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The 6-Second Scanner", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        killers = self._find_killers(cv_text)
        verbs = self._count_power_verbs(cv_text)
        metrics = self._count_metrics(cv_text)
        reading_ease = self._reading_ease(cv_text)
        opening = self._score_opening(cv_text)

        user_prompt = f"""CV (first 2500 chars = what recruiter sees first):\n{cv_text[:2500]}\n\nRest:\n{cv_text[2500:5000]}\n\nJD:\n{job_description[:1500]}\n\nPre-analysis:\n- CV killers: {', '.join(killers) if killers else 'None'}\n- Power verbs: {verbs}\n- Metrics: {metrics}\n- Reading ease: {reading_ease}\n- Opening impact: {opening}"""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._calc_score(llm_response, killers, metrics, verbs)

        return AgentOutput(
            agent_name=self.name, score=score,
            findings=[
                f"6-Second Scan Score: {score}/100",
                f"F-Pattern Score: {self._extract_int(llm_response, 'F_PATTERN_SCORE', score)}",
                f"CV Killer Phrases: {len(killers)} — {', '.join(killers[:3]) if killers else 'None ✓'}",
                f"Power Verbs Used: {verbs}",
                f"Quantified Achievements: {metrics}",
                f"Opening Impact: {opening}",
                f"First Impression: {self._extract_line(llm_response, 'FIRST_IMPRESSION')}",
                f"Scannability: {self._extract_line(llm_response, 'SCANNABILITY')}",
            ],
            recommendations=self._extract_fixes(llm_response, killers),
            optimized_content=self._extract_section(llm_response, 'IMPROVED_BULLET'),
            raw_analysis=llm_response, weight=1.3,
            execution_ms=int((time.time()-t0)*1000), ai_powered=self.llm is not None,
        )

    def _find_killers(self, t):
        tl=t.lower(); return [k for k in CV_KILLERS if k in tl]
    def _count_power_verbs(self, t):
        tl=t.lower(); return sum(1 for v in POWER_VERBS if v in tl)
    def _count_metrics(self, t):
        patterns=[r'\d+%',r'\$[\d,]+',r'£[\d,]+',r'R\s?[\d,]+',r'\d+x\b',r'\d+\s*(million|billion|thousand|k)\b',r'\d+\s*(people|staff|team|clients|users)']
        return sum(len(re.findall(p,t,re.IGNORECASE)) for p in patterns)
    def _score_opening(self, t):
        first=t[:500].lower()
        if any(v in first for v in POWER_VERBS[:10]): return "STRONG — power verb in opening"
        if re.search(r'\d+', first): return "MODERATE — numbers visible early"
        return "WEAK — no hooks in first 500 chars"
    def _reading_ease(self, t):
        try:
            import textstat; s=textstat.flesch_reading_ease(t)
            if s>70: return f"{s:.0f} — Easy ✓"
            if s>50: return f"{s:.0f} — Moderate"
            return f"{s:.0f} — Complex (simplify)"
        except: return "Not calculated"
    def _calc_score(self, r, killers, metrics, verbs):
        m=re.search(r'RECRUITER_SCORE:\s*(\d+)',r)
        if m: return int(m.group(1))
        s=55; s-=len(killers)*8; s+=min(25,metrics*3); s+=min(15,verbs*2)
        return max(10,min(100,s))
    def _extract_int(self, t, k, d):
        m=re.search(rf'{k}:\s*(\d+)',t); return int(m.group(1)) if m else d
    def _extract_line(self, t, k):
        m=re.search(rf'{k}:\s*(.+?)(?:\n|$)',t); return m.group(1).strip()[:100] if m else "N/A"
    def _extract_fixes(self, r, killers):
        fixes=[]
        m=re.search(r'FIXES:(.*?)(?:IMPROVED_BULLET:|$)',r,re.DOTALL)
        if m: fixes=[l.strip().lstrip('- ') for l in m.group(1).strip().split('\n') if l.strip() and l.strip()!='-'][:5]
        for k in killers[:3]: fixes.insert(0,f'Replace "{k}" with power verb + quantified result')
        return fixes[:8] if fixes else ["Add metrics to every role (%, ZAR, time, team size)"]
    def _extract_section(self, r, k):
        m=re.search(rf'{k}:\s*(.+?)(?:\n[A-Z_]+:|$)',r,re.DOTALL); return m.group(1).strip() if m else ""
