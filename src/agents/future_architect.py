"""Agent 8: Future Architect v2"""
import re, time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Future-Proof Architect v2 — 2025 career strategist positioning candidates for next-level roles.

2025 differentiating skills: GenAI, LLM integration, Prompt Engineering, AI tools (Copilot/Claude/GPT), Power BI, Python, API integration, automation, cloud-native, ESG reporting, OKRs, psychological safety, design thinking, neurodiversity awareness.

Respond in EXACTLY this format:

FUTURE_SCORE: [0-100]
CAREER_TRAJECTORY: [honest assessment — direction and velocity]
NEXT_ROLE_READINESS: [X]% ready for [next logical role title]
SKILL_GAPS: [skills needed for next role, comma-separated]
EMERGING_SKILLS_PRESENT: [2025 trending skills already in CV, comma-separated OR NONE]
EMERGING_SKILLS_MISSING: [top 3 to add based on trajectory]
AI_READINESS: [LOW/MEDIUM/HIGH — position in AI-augmented future of work]
LEARNING_PATH: [3 prioritized skills with timeline]
FIXES:
- [future-proofing fix 1]
- [future-proofing fix 2]
- [future-proofing fix 3]
CAREER_NARRATIVE: [2-3 sentences showing compelling upward trajectory for their next role]"""

EMERGING_2025 = ["generative ai","llm","prompt engineering","ai tools","github copilot","power bi","tableau","looker","esg","sustainability","okr","okrs","remote leadership","async","python","automation","api integration","no-code","low-code","data-driven","cloud native","kubernetes","terraform","devsecops","platform engineering","mlops","rag","vector database"]


class FutureArchitect(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Future-Proof Architect", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0=time.time()
        cvl=cv_text.lower()
        present=[s for s in EMERGING_2025 if s in cvl]
        progression=self._assess_progression(cv_text)
        ai_readiness=self._assess_ai_readiness(cv_text)

        user_prompt=f"""CV:\n{cv_text[:4000]}\n\nJD:\n{job_description[:1500]}\n\nContext:\n- Level: {context.get('experience_level','Mid')}\n- Target: {context.get('target_role','Similar to current')}\n- Industry: {context.get('industry','N/A')}\n\nPre-analysis:\n- Emerging skills present: {', '.join(present) if present else 'None'}\n- Coverage: {len(present)}/{len(EMERGING_2025)} tracked skills\n- Progression: {progression}\n- AI Readiness: {ai_readiness}\n\nDesign future-proof positioning."""

        llm_response=self._get_llm_response(SYSTEM_PROMPT,user_prompt)
        score=self._extract_int(llm_response,'FUTURE_SCORE',60)

        return AgentOutput(
            agent_name=self.name, score=score,
            findings=[
                f"Future-Proof Score: {score}/100",
                f"Career Trajectory: {self._extract_line(llm_response,'CAREER_TRAJECTORY')}",
                f"Next Role Readiness: {self._extract_line(llm_response,'NEXT_ROLE_READINESS')}",
                f"Emerging Skills: {len(present)}/{len(EMERGING_2025)} — {', '.join(present[:4]) if present else 'None'}",
                f"AI Readiness: {ai_readiness}",
                f"Progression Signal: {progression}",
            ],
            recommendations=self._extract_fixes(llm_response,present),
            optimized_content=self._extract_section(llm_response,'CAREER_NARRATIVE'),
            raw_analysis=llm_response, weight=0.9,
            execution_ms=int((time.time()-t0)*1000), ai_powered=self.llm is not None,
        )

    def _assess_progression(self, t):
        words=['promoted','advanced','progressed','grew','scaled','elevated','appointed']
        count=sum(1 for w in words if w in t.lower())
        if count>=3: return "Strong upward progression ✓"
        if count>=1: return "Some progression signals"
        return "Progression unclear — strengthen career arc"
    def _assess_ai_readiness(self, t):
        ai_tools=['chatgpt','copilot','claude','gemini','midjourney','stable diffusion','dall-e','llm','gpt','ai ','machine learning','automation']
        count=sum(1 for tool in ai_tools if tool in t.lower())
        if count>=4: return "HIGH — AI-native candidate"
        if count>=2: return "MEDIUM — AI-aware"
        return "LOW — no AI tools mentioned (critical gap for 2025)"
    def _extract_int(self, t, k, d): m=re.search(rf'{k}:\s*(\d+)',t); return int(m.group(1)) if m else d
    def _extract_line(self, t, k): m=re.search(rf'{k}:\s*(.+?)(?:\n|$)',t); return m.group(1).strip()[:100] if m else "N/A"
    def _extract_fixes(self, r, present):
        fixes=[]
        m=re.search(r'FIXES:(.*?)(?:CAREER_NARRATIVE:|$)',r,re.DOTALL)
        if m: fixes=[l.strip().lstrip('- ') for l in m.group(1).strip().split('\n') if l.strip() and l.strip()!='-'][:5]
        if len(present)<3: fixes.append("Add 2-3 emerging skills: GenAI tools, data-driven decision making, automation")
        return fixes[:8]
    def _extract_section(self, r, k): m=re.search(rf'{k}:\s*(.+?)(?:\n[A-Z_]+:|$)',r,re.DOTALL); return m.group(1).strip() if m else ""
