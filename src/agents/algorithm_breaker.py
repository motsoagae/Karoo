"""
Agent 1: The Algorithm Breaker v2
Enhanced: deeper ATS parser simulation, format scoring, keyword density analysis.
"""
import re
import time
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Algorithm Breaker v2 — the world's foremost expert in ATS parsing algorithms.

You reverse-engineer: Taleo, Workday, Greenhouse, Lever, SmartRecruiters, iCIMS, BambooHR, Jobvite, SAP SuccessFactors.

Analyze the CV against the job description and respond in EXACTLY this format:

ATS_SCORE: [0-100]
PARSER_RATES: Taleo:[X]% Workday:[X]% Greenhouse:[X]% Lever:[X]% SmartRecruiters:[X]%
FORMAT_SCORE: [0-100]
KEYWORD_DENSITY: [X]% (ideal is 2-4%)
KEYWORD_MATCH: [X]%
MISSING_KEYWORDS: [top 10 most critical missing keywords, comma-separated]
BLACK_FLAGS: [comma-separated list OR NONE]
SECTION_SCORES: Contact:[X] Summary:[X] Experience:[X] Education:[X] Skills:[X]
FIXES:
- [fix 1]
- [fix 2]
- [fix 3]
- [fix 4]
- [fix 5]
OPTIMIZED_SUMMARY: [Rewrite the professional summary for maximum ATS compatibility, 2-3 sentences, keyword-rich]"""


class AlgorithmBreaker(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Algorithm Breaker", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        t0 = time.time()
        black_flags = self._detect_black_flags(cv_text)
        keyword_data = self._analyze_keywords(cv_text, job_description)
        format_score = self._format_score(cv_text)
        section_scores = self._score_sections(cv_text)

        user_prompt = f"""CV TEXT:
{cv_text[:4000]}

JOB DESCRIPTION:
{job_description[:2500]}

TARGET MARKET: {context.get('target_market', 'Both')}
EXPERIENCE LEVEL: {context.get('experience_level', 'Mid')}

Pre-analysis results:
- Black flags detected: {', '.join(black_flags) if black_flags else 'None'}
- Keyword match rate: {keyword_data['match_pct']:.1f}%
- Keyword density: {keyword_data['density']:.1f}%
- Missing critical keywords: {', '.join(keyword_data['missing'][:12])}
- Format score: {format_score}/100
- Section integrity: {section_scores}

Perform exhaustive ATS analysis. Be specific and actionable."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_score(llm_response, keyword_data)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"ATS Score: {score}/100",
                f"Keyword Match Rate: {keyword_data['match_pct']:.1f}%",
                f"Keyword Density: {keyword_data['density']:.1f}% (ideal: 2-4%)",
                f"Format Score: {format_score}/100",
                f"Black Flags: {', '.join(black_flags) if black_flags else 'None detected ✓'}",
                f"Missing Critical Keywords: {len(keyword_data['missing'])}",
                f"Parser Rates: {self._extract_parser_rates(llm_response)}",
                f"Section Scores: {section_scores}",
            ],
            recommendations=self._extract_fixes(llm_response, black_flags, keyword_data),
            optimized_content=self._extract_section(llm_response, 'OPTIMIZED_SUMMARY'),
            raw_analysis=llm_response,
            weight=1.8,
            execution_ms=int((time.time() - t0) * 1000),
            ai_powered=self.llm is not None,
        )

    def _detect_black_flags(self, text: str) -> List[str]:
        flags = []
        if re.search(r'\|.{3,}\|', text): flags.append("markdown_tables")
        if text.count('\t') > 5: flags.append("excessive_tabs")
        if len(re.findall(r'[^\x00-\x7F]', text)) > 15: flags.append("unicode_characters")
        if re.search(r'(?i)(header text|footer text|\[image\]|\[photo\])', text): flags.append("image_placeholders")
        if len(re.findall(r'[●■▪►✓✗]', text)) > 8: flags.append("special_bullet_chars")
        if re.search(r'(?i)curriculum vitae|c\.v\.|cv:', text): flags.append("redundant_cv_label")
        word_count = len(text.split())
        if word_count < 200: flags.append("too_short")
        elif word_count > 1500: flags.append("too_long")
        if not re.search(r'[\w.]+@[\w.]+', text): flags.append("no_email_detected")
        return flags

    def _analyze_keywords(self, cv: str, jd: str) -> Dict:
        stop = {'and','the','for','with','that','are','will','you','have','this',
                'from','they','been','has','was','our','your','their','but','not',
                'all','can','its','who','may','also','any','use','one','two','new'}
        jd_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', jd)
                    if w.lower() not in stop]
        unique_jd = list(set(jd_words))
        cv_lower = cv.lower()
        matched = [w for w in unique_jd if w in cv_lower]
        missing = [w for w in unique_jd if w not in cv_lower]
        pct = (len(matched) / max(len(unique_jd), 1)) * 100

        cv_total_words = max(len(cv.split()), 1)
        keyword_count = sum(cv_lower.count(w) for w in matched)
        density = (keyword_count / cv_total_words) * 100

        return {
            'match_pct': pct,
            'density': min(density, 15.0),
            'matched': matched[:15],
            'missing': missing[:20],
        }

    def _format_score(self, text: str) -> int:
        score = 100
        if re.search(r'\|.{3,}\|', text): score -= 20
        if text.count('\t') > 5: score -= 15
        if len(re.findall(r'[^\x00-\x7F]', text)) > 15: score -= 10
        wc = len(text.split())
        if wc < 200: score -= 20
        elif wc > 1500: score -= 10
        if not re.search(r'[\w.]+@[\w.]+', text): score -= 15
        return max(0, min(100, score))

    def _score_sections(self, text: str) -> str:
        t = text.lower()
        def s(pattern): return 100 if re.search(pattern, t) else 0
        contact = 100 if re.search(r'@|phone|\+\d', t) else 0
        summary = 100 if re.search(r'summary|objective|profile|professional', t) else 0
        exp = 100 if re.search(r'experience|employment|work history', t) else 0
        edu = 100 if re.search(r'education|degree|qualification|university|college', t) else 0
        skills = 100 if re.search(r'skills|competencies|technologies', t) else 0
        return f"Contact:{contact} Summary:{summary} Exp:{exp} Edu:{edu} Skills:{skills}"

    def _extract_score(self, response: str, kw: Dict) -> int:
        m = re.search(r'ATS_SCORE:\s*(\d+)', response)
        if m: return min(100, max(0, int(m.group(1))))
        return min(100, int(kw['match_pct'] * 0.7 + 15))

    def _extract_parser_rates(self, response: str) -> str:
        m = re.search(r'PARSER_RATES:\s*(.+?)(?:\n|$)', response)
        return m.group(1).strip() if m else "N/A"

    def _extract_fixes(self, response: str, flags: List, kw: Dict) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:OPTIMIZED_SUMMARY:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:6]
        flag_map = {
            'markdown_tables': 'Remove all tables — replace with plain bullet-point lists.',
            'excessive_tabs': 'Replace tab indentation with spaces throughout.',
            'unicode_characters': 'Replace all special/unicode characters with ASCII equivalents.',
            'special_bullet_chars': 'Replace fancy bullet symbols (●►✓) with standard hyphens or asterisks.',
            'too_short': 'CV under 200 words — expand experience descriptions with metrics.',
            'too_long': 'CV exceeds 1500 words — trim to 2 pages max for ATS.',
            'no_email_detected': 'Ensure email address is in plain text format, not an image.',
            'redundant_cv_label': 'Remove "Curriculum Vitae" header — wastes prime ATS real estate.',
        }
        for flag in flags:
            if flag in flag_map:
                fixes.insert(0, flag_map[flag])
        if kw['missing']:
            fixes.append(f"Integrate missing keywords naturally: {', '.join(kw['missing'][:8])}")
        return fixes[:10]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
