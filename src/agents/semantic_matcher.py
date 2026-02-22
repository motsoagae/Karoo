"""Agent 6: Semantic Matcher v2"""
import re, time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Semantic Matcher v2 — NLP expert using cosine similarity, TF-IDF, and skill ontology mapping.

Respond in EXACTLY this format:

SEMANTIC_SCORE: [0-100]
COSINE_ESTIMATE: [X]%
SEMANTIC_GAPS: [concepts in JD not semantically covered by CV, comma-separated]
HIDDEN_MATCHES: [CV_term→JD_term semantic bridges, comma-separated]
TONE_ALIGNMENT: [Startup/Corporate/Government/Academic] [X]% aligned
IMPLICIT_REQUIREMENTS: [unstated JD requirements inferred from context, comma-separated]
DOMAIN_FLUENCY: [X]% — how native the candidate sounds in this domain
FIXES:
- [semantic improvement 1]
- [semantic improvement 2]
- [semantic improvement 3]
SEMANTIC_BRIDGE: [2-3 sentences bridging candidate's experience into JD language and concepts]"""

SKILL_ONTOLOGY = {
    'agile': ['scrum','kanban','sprint','backlog','standup','retro','velocity','jira'],
    'leadership': ['managed','led','mentored','coached','directed','supervised','head of','oversaw'],
    'data analysis': ['analytics','insights','reporting','dashboards','kpi','metrics','tableau','power bi','looker'],
    'cloud': ['aws','azure','gcp','cloud','kubernetes','docker','devops','terraform','lambda'],
    'communication': ['presentation','stakeholder','negotiation','briefing','reporting','c-suite'],
    'project management': ['pmp','prince2','jira','ms project','delivery','milestones','governance','waterfall'],
    'ai ml': ['machine learning','deep learning','tensorflow','pytorch','scikit','llm','neural','nlp'],
    'finance': ['fpa','p&l','variance','budget','forecast','excel','sap','oracle','erp'],
}


class SemanticMatcher(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Semantic Matcher", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0=time.time()
        cosine=self._cosine_similarity(cv_text,job_description)
        hidden=self._find_hidden_matches(cv_text,job_description)
        tone=self._tone_analysis(cv_text,job_description)

        user_prompt=f"""CV:\n{cv_text[:3500]}\n\nJD:\n{job_description[:2000]}\n\nPre-metrics:\n- TF-IDF Cosine: {cosine:.3f}\n- Hidden matches: {hidden}\n- Tone: {tone}\n\nDeep semantic analysis."""

        llm_response=self._get_llm_response(SYSTEM_PROMPT,user_prompt)
        score=self._extract_int(llm_response,'SEMANTIC_SCORE',int(cosine*100))

        return AgentOutput(
            agent_name=self.name, score=score,
            findings=[
                f"Semantic Match Score: {score}/100",
                f"Cosine Similarity: {cosine:.3f} (>0.75 = strong match)",
                f"Hidden Semantic Matches: {hidden}",
                f"Tone Alignment: {tone}",
                f"Semantic Gaps: {self._extract_line(llm_response,'SEMANTIC_GAPS')}",
                f"Domain Fluency: {self._extract_line(llm_response,'DOMAIN_FLUENCY')}",
            ],
            recommendations=self._extract_fixes(llm_response),
            optimized_content=self._extract_section(llm_response,'SEMANTIC_BRIDGE'),
            raw_analysis=llm_response, weight=1.1,
            execution_ms=int((time.time()-t0)*1000), ai_powered=self.llm is not None,
        )

    def _cosine_similarity(self, cv, jd):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            vec=TfidfVectorizer(stop_words='english',max_features=600,ngram_range=(1,2))
            mat=vec.fit_transform([cv[:6000],jd[:6000]])
            return float(cosine_similarity(mat[0:1],mat[1:2])[0][0])
        except: return 0.5
    def _find_hidden_matches(self, cv, jd):
        cvl,jdl=cv.lower(),jd.lower()
        matches=[]
        for concept,syns in SKILL_ONTOLOGY.items():
            jd_needs=any(s in jdl for s in syns+[concept])
            cv_has=any(s in cvl for s in syns)
            if jd_needs and cv_has and concept not in cvl:
                syn=next((s for s in syns if s in cvl),None)
                if syn: matches.append(f"{syn}→{concept}")
        return ', '.join(matches[:5]) if matches else 'None'
    def _tone_analysis(self, cv, jd):
        startup=['disrupt','scale','startup','agile','iterate','pivot','lean','mvp']
        corp=['stakeholder','governance','compliance','enterprise','policy','strategy','C-suite']
        govt=['public sector','government','municipality','department','regulation','audit','tender']
        jdl,cvl=jd.lower(),cv.lower()
        sc={(t,(sum(1 for w in ws if w in jdl),sum(1 for w in ws if w in cvl))) for t,ws in [('Startup',startup),('Corporate',corp),('Government',govt)]}
        dom=max(sc,key=lambda x:x[1][0])
        jdn,cvn=dom[1]; pct=min(100,int((cvn/max(jdn,1))*100))
        return f"{dom[0]} — {pct}% aligned"
    def _extract_int(self, t, k, d): m=re.search(rf'{k}:\s*(\d+)',t); return int(m.group(1)) if m else d
    def _extract_line(self, t, k): m=re.search(rf'{k}:\s*(.+?)(?:\n|$)',t); return m.group(1).strip()[:100] if m else "N/A"
    def _extract_fixes(self, r):
        m=re.search(r'FIXES:(.*?)(?:SEMANTIC_BRIDGE:|$)',r,re.DOTALL)
        if m: return [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n') if l.strip() and l.strip()!='-'][:6]
        return ["Mirror JD language more closely in your experience descriptions"]
    def _extract_section(self, r, k): m=re.search(rf'{k}:\s*(.+?)(?:\n[A-Z_]+:|$)',r,re.DOTALL); return m.group(1).strip() if m else ""
