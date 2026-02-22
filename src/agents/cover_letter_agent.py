"""Agent 9: Cover Letter Composer v2"""
import re, time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Cover Letter Composer v2 — elite career writer. 90% of cover letters are ignored. Yours get interviews.

Rules: Open with INSIGHT not "I am writing to apply". 3 paragraphs MAX. 280-350 words. Reference specific JD elements.
P1 — Hook (company/industry insight or challenge)
P2 — Proof (2-3 specific achievements matching their needs)
P3 — Confident close (no "I hope to hear from you")

SA version: slightly more formal, B-BBEE mention if relevant.
International: punchy, direct, results-first.

Respond in EXACTLY this format:

COVER_LETTER_START
[Full cover letter — 3 paragraphs, 280-350 words]
COVER_LETTER_END

QUALITY_SCORE: [0-100]
PERSONALIZATION: [Generic/Basic/Good/Excellent]
WORD_COUNT: [actual count]
HOOK_TYPE: [Industry insight/Company challenge/Provocative stat/Direct value prop]
TIPS:
- [personalization tip]
- [improvement tip]"""


class CoverLetterAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Cover Letter Composer", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0=time.time()
        company=self._extract_company(job_description)
        role=self._extract_role(job_description)

        user_prompt=f"""CV (extract 3 strongest achievements with metrics):\n{cv_text[:3500]}\n\nJD:\n{job_description[:2500]}\n\nContext:\n- Market: {context.get('target_market','South Africa')}\n- Level: {context.get('experience_level','Mid')}\n- Industry: {context.get('industry','N/A')}\n- Company: {company}\n- Role: {role}\n\nWrite a compelling, personalized cover letter that earns an interview.\nNEVER start with "I am writing to apply". Reference specific JD elements."""

        llm_response=self._get_llm_response(SYSTEM_PROMPT,user_prompt)
        letter=self._extract_letter(llm_response)
        score=self._extract_int(llm_response,'QUALITY_SCORE',70)

        return AgentOutput(
            agent_name=self.name, score=score,
            findings=[
                f"Cover Letter Quality: {score}/100",
                f"Word Count: {len(letter.split())} words",
                f"Personalization: {self._extract_line(llm_response,'PERSONALIZATION')}",
                f"Hook Type: {self._extract_line(llm_response,'HOOK_TYPE')}",
                f"Company Detected: {company}",
                f"Role Detected: {role}",
            ],
            recommendations=self._extract_tips(llm_response),
            optimized_content=letter,
            raw_analysis=llm_response, weight=0.8,
            execution_ms=int((time.time()-t0)*1000), ai_powered=self.llm is not None,
        )

    def _extract_company(self, jd):
        patterns=[r'(?:at|join|company|organisation|organization):\s*([A-Z][A-Za-z\s&]{2,30})',r'^([A-Z][A-Za-z\s&]{2,30})\s+(?:is|are)\s+(?:looking|seeking|hiring)']
        for p in patterns:
            m=re.search(p,jd,re.MULTILINE)
            if m: return m.group(1).strip()[:40]
        return "[Company Name]"
    def _extract_role(self, jd):
        patterns=[r'(?:position|role|job title|vacancy):\s*(.+?)(?:\n|$)',r'^([\w\s/]{5,40})\n']
        for p in patterns:
            m=re.search(p,jd,re.IGNORECASE|re.MULTILINE)
            if m: return m.group(1).strip()[:60]
        return "[Role]"
    def _extract_letter(self, r):
        m=re.search(r'COVER_LETTER_START\s*\n(.*?)\nCOVER_LETTER_END',r,re.DOTALL)
        if m: return m.group(1).strip()
        m2=re.search(r'COVER_LETTER_START\s*\n(.+)',r,re.DOTALL)
        return m2.group(1).strip()[:2000] if m2 else r[:1500]
    def _extract_int(self, t, k, d): m=re.search(rf'{k}:\s*(\d+)',t); return int(m.group(1)) if m else d
    def _extract_line(self, t, k): m=re.search(rf'{k}:\s*(.+?)(?:\n|$)',t); return m.group(1).strip()[:60] if m else "N/A"
    def _extract_tips(self, r):
        m=re.search(r'TIPS:(.*?)(?:$)',r,re.DOTALL)
        if m: return [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n') if l.strip() and l.strip()!='-'][:3]
        return ["Add hiring manager's name if you can find it","Reference a recent company news item"]
