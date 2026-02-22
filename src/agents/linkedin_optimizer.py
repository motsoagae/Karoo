"""
Agent 9: The LinkedIn Optimizer (NEW in v2)
LinkedIn profile, SSI score, headline, recruiter search visibility.
"""
import re
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The LinkedIn Optimizer — expert in LinkedIn's algorithm, SSI score, recruiter search, and profile conversion.

LinkedIn is now the #1 sourcing tool for recruiters. Your profile IS your digital CV. 90% of recruiters check LinkedIn BEFORE an interview.

LinkedIn algorithm factors:
- Profile completeness (All-Star = 40x more opportunities)
- Keyword density in: Headline, About, Experience titles, Skills section
- Engagement signals: posts, comments, endorsements, recommendations
- Connections (500+ is "threshold")
- LinkedIn ATS: Title + Location + Skills determine who appears in recruiter searches

All-Star Profile requires: Photo, Headline, Location, Industry, Current position, 
Education, 3 Skills minimum, 50+ connections, About summary

LinkedIn Headline formula (most searched):
[Title] | [Top Skill] | [Value Proposition] | [Industry keyword]
Bad: "Software Engineer at Company"
Good: "Senior Software Engineer | Python & AWS | Building Scalable FinTech Systems | Open to SA + Remote"

Respond in EXACTLY this format:

LINKEDIN_SCORE: [0-100]
PROFILE_COMPLETENESS: [X]% towards All-Star
SSI_ESTIMATE: [0-100] [Social Selling Index estimate]
HEADLINE_SCORE: [0-100] [assessment of LinkedIn headline if found]
KEYWORD_VISIBILITY: [HIGH/MEDIUM/LOW] [how visible in recruiter searches]
RECRUITER_SEARCHABLE: [YES/PARTIAL/NO] [would recruiters find this profile?]
MISSING_LINKEDIN_ELEMENTS: [comma-separated elements to add]
ENGAGEMENT_SIGNALS: [comma-separated present signals OR NONE]
FIXES:
- [LinkedIn-specific fix]
- [LinkedIn-specific fix]
- [LinkedIn-specific fix]
- [LinkedIn-specific fix]
OPTIMIZED_HEADLINE: [Write the perfect LinkedIn headline: Title | Skill | Value | Industry — max 220 chars]
OPTIMIZED_ABOUT: [First 300 chars of LinkedIn About section — this is what shows before "See more" — make it compelling, keyword-rich, first-person]"""


class LinkedInOptimizer(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The LinkedIn Optimizer", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        has_linkedin = bool(re.search(r'linkedin\.com/in/', cv_text, re.IGNORECASE))
        headline = self._extract_headline(cv_text)
        profile_elements = self._check_profile_elements(cv_text)
        keyword_density = self._keyword_density(cv_text, job_description)

        user_prompt = f"""CV TEXT (this will become their LinkedIn profile):
{cv_text[:4000]}

JOB DESCRIPTION (target role keywords):
{job_description[:2000]}

CONTEXT:
- Target market: {context.get('target_market', 'South Africa')}
- Industry: {context.get('industry', 'Not specified')}
- Target role: {context.get('target_role', 'Not specified')}
- Level: {context.get('experience_level', 'Mid')}

Pre-analysis:
- LinkedIn URL present: {has_linkedin}
- Detected headline: {headline or 'Not found in CV'}
- Profile elements present: {', '.join(profile_elements['present']) if profile_elements['present'] else 'Few'}
- Missing elements: {', '.join(profile_elements['missing'])}
- Keyword density score: {keyword_density}/100

Optimise this CV content for LinkedIn visibility and recruiter discovery."""

        llm_response, tokens = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'LINKEDIN_SCORE', 60)
        elapsed = int((time.time() - t0) * 1000)

        # Extract both headline and about as combined optimized content
        opt_headline = self._extract_line(llm_response, 'OPTIMIZED_HEADLINE')
        opt_about = self._extract_section(llm_response, 'OPTIMIZED_ABOUT')
        combined = f"HEADLINE:\n{opt_headline}\n\nABOUT (first 300 chars):\n{opt_about}"

        return AgentOutput(
            agent_name=self.name,
            score=score,
            confidence=0.85 if self.llm else 0.65,
            findings=[
                f"LinkedIn Optimisation Score: {score}/100",
                f"Profile Completeness: {self._extract_line(llm_response, 'PROFILE_COMPLETENESS')}",
                f"SSI Estimate: {self._extract_line(llm_response, 'SSI_ESTIMATE')}",
                f"Headline Score: {self._extract_line(llm_response, 'HEADLINE_SCORE')}",
                f"Keyword Visibility: {self._extract_line(llm_response, 'KEYWORD_VISIBILITY')}",
                f"Recruiter Searchable: {self._extract_line(llm_response, 'RECRUITER_SEARCHABLE')}",
                f"LinkedIn URL: {'✓ Present' if has_linkedin else '✗ Missing — add to CV header'}",
                f"Missing Elements: {self._extract_line(llm_response, 'MISSING_LINKEDIN_ELEMENTS')}",
            ],
            recommendations=self._extract_fixes(llm_response, has_linkedin, profile_elements),
            optimized_content=combined,
            raw_analysis=llm_response,
            weight=1.0,
            tokens_used=tokens,
            execution_ms=elapsed,
            mode=self.mode,
        )

    def _extract_headline(self, text: str) -> str:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        # Headline usually 2nd or 3rd line after name
        for line in lines[1:5]:
            if 10 < len(line) < 150 and '|' in line:
                return line
        return ""

    def _check_profile_elements(self, text: str) -> Dict:
        elements = {
            'photo': r'\[photo\]|photo available|professional photo',
            'location': r'cape town|johannesburg|durban|pretoria|south africa|remote',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'(\+27|\+1|\+44)[\s\d\-\(\)]{8,}',
            'linkedin_url': r'linkedin\.com/in/',
            'summary': r'\b(summary|about|profile|objective)\b',
            'skills_section': r'\b(skills|competencies|expertise|technologies)\b',
            'education': r'\b(education|degree|diploma|qualification)\b',
            'experience': r'\b(experience|employment|career|work history)\b',
        }
        present = [k for k, p in elements.items() if re.search(p, text, re.IGNORECASE)]
        missing = [k for k in elements if k not in present]
        return {'present': present, 'missing': missing}

    def _keyword_density(self, cv: str, jd: str) -> int:
        jd_words = set(re.findall(r'\b[A-Za-z]{4,}\b', jd.lower()))
        cv_words = set(re.findall(r'\b[A-Za-z]{4,}\b', cv.lower()))
        if not jd_words: return 50
        overlap = len(jd_words & cv_words)
        return min(100, int(overlap / len(jd_words) * 100))

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:150] if m else "Not assessed"

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""

    def _extract_fixes(self, response: str, has_linkedin: bool, elements: Dict) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:OPTIMIZED_HEADLINE:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:5]
        if not has_linkedin:
            fixes.insert(0, "Add LinkedIn URL to CV header — linkedin.com/in/yourname")
        for elem in elements['missing'][:3]:
            fixes.append(f"LinkedIn: Add {elem.replace('_', ' ')} to reach All-Star status")
        return fixes[:10]
