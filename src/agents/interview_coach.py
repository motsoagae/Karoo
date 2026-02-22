"""
Agent 10 (NEW): The Interview Coach
Generates likely interview questions, STAR answer frameworks, curveball prep.
"""
import re
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Interview Coach — world-class career coach who predicts interview questions with uncanny accuracy.

You analyse the gaps between a CV and job description and predict:
1. Questions the interviewer WILL ask about gaps/discrepancies
2. Behavioural questions based on the role requirements
3. Technical questions based on stated skills vs JD requirements
4. Curveball questions unique to this company/industry
5. Questions about career transitions, progression, salary expectations

For each question, provide a STAR framework starter (Situation, Task, Action, Result).

Respond in EXACTLY this format:

INTERVIEW_SCORE: [0-100] (candidate's estimated interview readiness based on CV)
LIKELY_QUESTIONS:
Q1: [Most likely question — usually about biggest gap or transition]
STAR: S:[situation setup] T:[task framing] A:[action keyword] R:[result type]
Q2: [Second most likely]
STAR: S:[setup] T:[task] A:[action] R:[result]
Q3: [Behavioural question]
STAR: S:[setup] T:[task] A:[action] R:[result]
Q4: [Technical/skills question]
STAR: S:[setup] T:[task] A:[action] R:[result]
Q5: [Culture/motivation question]
STAR: S:[setup] T:[task] A:[action] R:[result]
Q6: [Curveball — industry or company specific]
STAR: S:[setup] T:[task] A:[action] R:[result]
SALARY_TALK: [How to handle the salary question for this role/market]
RED_FLAGS_TO_ADDRESS: [CV weaknesses the interviewer WILL probe — comma-separated]
CLOSING_QUESTIONS: [3 smart questions to ask the interviewer, comma-separated]
PREP_SUMMARY: [2-3 sentences on top interview prep priorities for this specific role]"""


class InterviewCoach(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Interview Coach", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        gaps = self._identify_gaps(cv_text, job_description)
        transitions = self._detect_transitions(cv_text)
        seniority_mismatch = self._check_seniority(cv_text, context)

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
- Skill gaps vs JD: {gaps}
- Career transitions detected: {transitions}
- Seniority alignment: {seniority_mismatch}

Generate interview questions that WILL be asked. Be specific to this exact role and CV combination.
Focus on the gaps, transitions, and areas the interviewer will probe hardest."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'INTERVIEW_SCORE', 60)
        questions = self._extract_questions(llm_response)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Interview Readiness: {score}/100",
                f"Questions Generated: {len(questions)}",
                f"Skill Gaps That Will Be Probed: {gaps[:100]}",
                f"Career Transitions: {transitions}",
                f"Seniority Alignment: {seniority_mismatch}",
                f"Red Flags to Address: {self._extract_line(llm_response, 'RED_FLAGS_TO_ADDRESS')}",
            ],
            recommendations=questions + self._extract_closing(llm_response),
            optimized_content=self._format_qa_output(llm_response),
            raw_analysis=llm_response,
            weight=1.0,
            execution_ms=int((time.time() - t0) * 1000),
            ai_powered=self.llm is not None,
        )

    def _identify_gaps(self, cv: str, jd: str) -> str:
        stop = {'and','the','for','with','you','are','this','that','have','will'}
        jd_terms = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', jd)
                    if w.lower() not in stop]
        cv_lower = cv.lower()
        missing = list(set([w for w in jd_terms if w not in cv_lower]))[:8]
        return ', '.join(missing) if missing else 'Minimal gaps detected'

    def _detect_transitions(self, cv: str) -> str:
        roles = re.findall(r'(?:senior|lead|manager|director|head|principal|junior|graduate)\s+\w+',
                           cv, re.IGNORECASE)
        if len(roles) > 1:
            return f"Multiple role levels: {', '.join(list(set(roles))[:3])}"
        gaps = re.findall(r'(20\d\d)\s*[-–]\s*(20\d\d)', cv)
        if gaps:
            for start, end in gaps:
                if int(end) - int(start) > 2:
                    return f"Extended tenure periods — progression narrative needed"
        return "Stable career progression"

    def _check_seniority(self, cv: str, context: Dict) -> str:
        level = context.get('experience_level', 'Mid')
        years_match = re.search(r'(\d+)\+?\s*years?', cv, re.IGNORECASE)
        if years_match:
            years = int(years_match.group(1))
            expected = {'Entry': 2, 'Mid': 5, 'Senior': 10, 'Executive': 18}
            exp = expected.get(level, 5)
            if years < exp - 2:
                return f"Under-experienced for {level} role ({years} years vs {exp} expected)"
            elif years > exp + 5:
                return f"May be overqualified — address potential concern proactively"
        return "Seniority appears well-matched"

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:150] if m else "See full analysis"

    def _extract_questions(self, response: str) -> List[str]:
        questions = re.findall(r'Q\d+:\s*(.+?)(?:\nSTAR:|$)', response, re.DOTALL)
        return [f"Prep: {q.strip()[:120]}" for q in questions[:6]]

    def _extract_closing(self, response: str) -> List[str]:
        m = re.search(r'CLOSING_QUESTIONS:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        if m:
            questions = [q.strip() for q in m.group(1).split(',') if q.strip()]
            return [f"Ask interviewer: {q}" for q in questions[:3]]
        return ["Ask interviewer: What does success look like in the first 90 days?"]

    def _format_qa_output(self, response: str) -> str:
        sections = []
        questions = re.findall(r'(Q\d+:\s*.+?STAR:\s*.+?)(?=Q\d+:|SALARY_TALK:|$)',
                               response, re.DOTALL)
        for q in questions[:6]:
            sections.append(q.strip())
        salary = re.search(r'SALARY_TALK:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        if salary:
            sections.append(f"\n💰 SALARY DISCUSSION:\n{salary.group(1).strip()}")
        closing = re.search(r'CLOSING_QUESTIONS:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        if closing:
            sections.append(f"\n❓ SMART QUESTIONS TO ASK:\n{closing.group(1).strip()}")
        return '\n\n'.join(sections) if sections else response[:2000]
