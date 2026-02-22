"""
Karoo v2.0 Master Orchestrator
11 agents: 8 core + Interview Coach + Salary Intelligence + CV Rewriter
Supports Groq (free) + OpenAI + Anthropic. Auto-detects API key.
"""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime 

from src.agents.algorithm_breaker import AlgorithmBreaker
from src.agents.sa_specialist import SASpecialist
from src.agents.global_setter import GlobalSetter
from src.agents.recruiter_scanner import RecruiterScanner
from src.agents.hiring_manager_whisperer import HiringManagerWhisperer
from src.agents.semantic_matcher import SemanticMatcher
from src.agents.compliance_guardian import ComplianceGuardian
from src.agents.future_architect import FutureArchitect
from src.agents.cover_letter_agent import CoverLetterAgent
from src.agents.interview_coach import InterviewCoach
from src.agents.salary_intelligence import SalaryIntelligence
from src.agents.cv_rewriter_agent import CVRewriterAgent
from src.agents.base_agent import AgentOutput

logger = logging.getLogger(__name__)


def create_llm():
    """
    Auto-detect and create LLM. Priority: Groq → OpenAI → Anthropic → Rule-Based
    """
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key and not groq_key.startswith("gsk_your"):
        try:
            from langchain_groq import ChatGroq
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            llm = ChatGroq(api_key=groq_key, model=model, temperature=0.3, max_tokens=2000)
            logger.info(f"✓ Groq LLM: {model}")
            return llm, "Groq", model
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-your"):
        try:
            from langchain_openai import ChatOpenAI
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(api_key=openai_key, model=model, temperature=0.3, max_tokens=2000)
            logger.info(f"✓ OpenAI LLM: {model}")
            return llm, "OpenAI", model
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key and not anthropic_key.startswith("sk-ant-your"):
        try:
            from langchain_anthropic import ChatAnthropic
            model = "claude-haiku-4-5-20251001"
            llm = ChatAnthropic(api_key=anthropic_key, model=model, temperature=0.3, max_tokens=2000)
            logger.info(f"✓ Anthropic LLM: {model}")
            return llm, "Anthropic", model
        except Exception as e:
            logger.warning(f"Anthropic init failed: {e}")

    logger.info("No API key — rule-based mode. Add GROQ_API_KEY for AI analysis.")
    return None, "Rule-Based", "None"


class KarooOrchestrator:
    """v2 Master Coordinator — 11 agents, full AI CV rewrite, interview prep, salary intel."""

    AGENT_META = {
        "algorithm_breaker": {"icon": "🎯", "label": "Algorithm Breaker", "weight_sa": 1.8, "weight_intl": 1.8},
        "sa_specialist":     {"icon": "🇿🇦", "label": "SA Specialist",      "weight_sa": 2.0, "weight_intl": 0.8},
        "global_setter":     {"icon": "🌍", "label": "Global Setter",      "weight_sa": 0.8, "weight_intl": 2.0},
        "recruiter_scanner": {"icon": "👁️", "label": "6-Second Scanner",   "weight_sa": 1.3, "weight_intl": 1.3},
        "hiring_manager":    {"icon": "💼", "label": "Hiring Manager",     "weight_sa": 1.2, "weight_intl": 1.2},
        "semantic_matcher":  {"icon": "📊", "label": "Semantic Matcher",   "weight_sa": 1.1, "weight_intl": 1.3},
        "compliance_guardian": {"icon": "⚖️", "label": "Compliance Guardian", "weight_sa": 1.2, "weight_intl": 1.0},
        "future_architect":  {"icon": "🚀", "label": "Future Architect",   "weight_sa": 0.9, "weight_intl": 1.0},
        "interview_coach":   {"icon": "🎤", "label": "Interview Coach",    "weight_sa": 1.0, "weight_intl": 1.0},
        "salary_intelligence": {"icon": "💰", "label": "Salary Intelligence", "weight_sa": 0.8, "weight_intl": 0.7},
    }

    def __init__(self):
        self.llm, self.llm_provider, self.llm_model = create_llm()
        self.ai_mode = self.llm is not None

        self.agents = {
            "algorithm_breaker":  AlgorithmBreaker(self.llm),
            "sa_specialist":      SASpecialist(self.llm),
            "global_setter":      GlobalSetter(self.llm),
            "recruiter_scanner":  RecruiterScanner(self.llm),
            "hiring_manager":     HiringManagerWhisperer(self.llm),
            "semantic_matcher":   SemanticMatcher(self.llm),
            "compliance_guardian": ComplianceGuardian(self.llm),
            "future_architect":   FutureArchitect(self.llm),
            "interview_coach":    InterviewCoach(self.llm),
            "salary_intelligence": SalaryIntelligence(self.llm),
        }
        self.cover_agent = CoverLetterAgent(self.llm)
        self.rewriter = CVRewriterAgent(self.llm)

        mode = f"🧠 {self.llm_provider} ({self.llm_model})" if self.ai_mode else "📐 Rule-Based"
        logger.info(f"Karoo v2 Orchestrator — {mode}")

    async def optimize(
        self,
        cv_text: str,
        job_description: str,
        context: Dict[str, Any],
        generate_cover_letter: bool = True,
        rewrite_cv: bool = True,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Full v2 pipeline: 10 agents + cover letter + AI CV rewrite."""
        start = datetime.now()

        def _p(pct: float, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        _p(0.03, f"🚀 Launching 10 specialist agents ({self.llm_provider} mode)...")

        # Phase 1: Run 10 analysis agents in parallel
        agent_results = await self._run_parallel(cv_text, job_description, context, _p)

        _p(0.82, "📊 Synthesizing results...")
        summary = self._build_summary(agent_results, context)

        # Pass insights to rewriter
        algo = agent_results.get('algorithm_breaker', AgentOutput())
        missing_kw = []
        for f in algo.findings:
            if 'Missing' in f:
                missing_kw = [k.strip() for k in f.split(':')[-1].split(',') if k.strip()]

        rewriter_ctx = {**context, '_missing_keywords': missing_kw, '_agent_insights': {
            'ats_score': summary.get('overall_score', 0),
            'top_fixes': summary.get('top_action_items', [])[:5],
        }}

        # Phase 2: Cover letter
        cover_letter = ""
        if generate_cover_letter:
            _p(0.86, "📝 Writing cover letter...")
            try:
                cl_result = await asyncio.wait_for(
                    self.cover_agent.analyze(cv_text, job_description, context), timeout=75
                )
                cover_letter = cl_result.optimized_content
            except Exception as e:
                logger.error(f"Cover letter failed: {e}")
                cover_letter = "[Cover letter generation failed — ensure API key is set]"

        # Phase 3: AI CV Rewrite
        cv_variants = {"ats_max": "", "balanced": "", "creative": ""}
        if rewrite_cv and self.ai_mode:
            _p(0.90, "✍️ AI rewriting 3 CV variants...")
            try:
                rw_result = await asyncio.wait_for(
                    self.rewriter.analyze(cv_text, job_description, rewriter_ctx), timeout=180
                )
                raw = rw_result.optimized_content
                from src.agents.cv_rewriter_agent import CVRewriterAgent as CRA
                cra = CRA(self.llm)
                for variant in ['ats_max', 'balanced', 'creative']:
                    cv_variants[variant] = cra.get_variant(raw, variant)
            except Exception as e:
                logger.error(f"CV rewrite failed: {e}")
                cv_variants = self._fallback_variants(cv_text, agent_results, summary)
        else:
            cv_variants = self._fallback_variants(cv_text, agent_results, summary)

        _p(0.97, "🔍 Compiling priority action items...")
        action_items = self._compile_actions(agent_results)

        elapsed = round((datetime.now() - start).total_seconds(), 1)
        _p(1.0, f"✅ Done in {elapsed}s!")

        return {
            "summary": summary,
            "agent_results": {k: v.dict() for k, v in agent_results.items()},
            "cv_variants": cv_variants,
            "cover_letter": cover_letter,
            "action_items": action_items,
            "ai_mode": self.ai_mode,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "metadata": {
                "execution_seconds": elapsed,
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "agents_run": len(agent_results),
                "ai_rewrite": rewrite_cv and self.ai_mode,
                "cover_letter_generated": generate_cover_letter,
            }
        }

    async def _run_parallel(self, cv, jd, ctx, progress_cb):
        tasks = {
            name: asyncio.create_task(self._safe_run(agent, cv, jd, ctx))
            for name, agent in self.agents.items()
        }
        results = {}
        completed = 0
        for name, task in tasks.items():
            try:
                result = await asyncio.wait_for(asyncio.shield(task), timeout=90)
                results[name] = result
                logger.info(f"✓ [{name}]: {result.score}/100 ({result.execution_ms}ms)")
            except asyncio.TimeoutError:
                logger.error(f"✗ [{name}] timed out")
                results[name] = AgentOutput(agent_name=name, score=50,
                    findings=["⚠️ Agent timed out"], recommendations=["Re-run for complete analysis"])
            except Exception as e:
                logger.error(f"✗ [{name}] error: {e}")
                results[name] = AgentOutput(agent_name=name, score=50,
                    findings=[f"⚠️ Error: {str(e)[:80]}"], recommendations=["Check API key"])
            completed += 1
            meta = self.AGENT_META.get(name, {})
            icon = meta.get("icon", "🤖")
            label = meta.get("label", name)
            pct = 0.03 + (completed / len(tasks)) * 0.77
            progress_cb(pct, f"{icon} {label} complete ({completed}/{len(tasks)})")
        return results

    async def _safe_run(self, agent, cv, jd, ctx):
        return await agent.analyze(cv, jd, ctx)

    def _build_summary(self, results: Dict, context: Dict) -> Dict:
        market = context.get('target_market', 'Both')
        weight_key = 'weight_sa' if market == 'South Africa' else 'weight_intl' if market == 'International' else None

        total_w, weighted_sum = 0.0, 0.0
        scores = {}

        for name, result in results.items():
            meta = self.AGENT_META.get(name, {})
            w = meta.get(weight_key, result.weight) if weight_key else result.weight
            weighted_sum += result.score * w
            total_w += w
            scores[name] = result.score

        overall = round(weighted_sum / total_w, 1) if total_w else 0

        if overall >= 85:
            variant, verdict = "BALANCED", "Excellent profile — optimised for maximum impact."
        elif overall >= 70:
            variant, verdict = "BALANCED", "Strong foundation — targeted improvements will push to 85+."
        elif overall >= 55:
            variant, verdict = "ATS-MAX", "Good base — prioritise ATS keyword optimisation and metrics."
        else:
            variant, verdict = "ATS-MAX", "Significant gaps identified — work through all action items systematically."

        action_items = self._compile_actions(results)

        return {
            "overall_score": overall,
            "recommended_variant": variant,
            "verdict": verdict,
            "interview_probability": min(97, int(overall * 0.90 + 7)),
            "agent_scores": scores,
            "weakest_area": min(scores, key=scores.get) if scores else "",
            "strongest_area": max(scores, key=scores.get) if scores else "",
            "target_market": market,
            "top_action_items": action_items[:5],
            "ai_powered_count": sum(1 for r in results.values() if r.ai_powered),
        }

    def _compile_actions(self, results: Dict) -> List[str]:
        weighted = []
        for name, result in results.items():
            urgency = 1.0 + (100 - result.score) / 35
            for rec in result.recommendations[:5]:
                if rec and len(rec) > 12:
                    weighted.append((urgency, rec))
        weighted.sort(key=lambda x: x[0], reverse=True)
        seen, unique = set(), []
        for _, rec in weighted:
            norm = rec.lower()[:65]
            if norm not in seen:
                seen.add(norm)
                unique.append(rec)
        return unique[:18]

    def _fallback_variants(self, original_cv, results, summary) -> Dict:
        score = summary.get('overall_score', 0)
        ts = datetime.now().strftime('%d %B %Y')
        algo = results.get('algorithm_breaker', AgentOutput())
        missing_kw = next((f for f in algo.findings if 'Missing' in f), "")
        career_narrative = results.get('future_architect', AgentOutput()).optimized_content
        semantic_bridge = results.get('semantic_matcher', AgentOutput()).optimized_content
        clean_summary = results.get('compliance_guardian', AgentOutput()).optimized_content
        improved_bullet = results.get('recruiter_scanner', AgentOutput()).optimized_content
        sa_summary = results.get('sa_specialist', AgentOutput()).optimized_content

        header = f"╔══════════════════════════════════════════════════════╗\n║  Karoo v2 OPTIMIZED — {ts}  ║\n║             Overall Score: {score}/100                   ║\n╚══════════════════════════════════════════════════════╝\n\n"

        ats = f"{header}═══ ATS-MAX VARIANT (Maximum Parse Rate) ═══\n\nOPTIMIZED SUMMARY:\n{algo.optimized_content or clean_summary or '[Apply the ATS-optimized summary from the Algorithm Breaker agent above]'}\n\nMISSING KEYWORDS TO ADD:\n{missing_kw}\n\nSEMANTIC CONTEXT:\n{semantic_bridge or '[Add JD language throughout your experience section]'}\n\n══════════════ YOUR ORIGINAL CV ══════════════\n{original_cv}"
        bal = f"{header}═══ BALANCED VARIANT ⭐ RECOMMENDED ═══\n\nCOMPELLING SUMMARY:\n{career_narrative or clean_summary or '[Apply the career narrative from the Future Architect agent]'}\n\nSTRONGEST ACHIEVEMENT EXAMPLE:\n{improved_bullet or '[Apply the rewritten bullet from the 6-Second Scanner agent]'}\n\n══════════════ YOUR ORIGINAL CV ══════════════\n{original_cv}"
        cre = f"{header}═══ CREATIVE VARIANT (Human-First) ═══\n\nCAREER NARRATIVE:\n{career_narrative or '[Build your story around progression and impact]'}\n\nSA MARKET ANGLE:\n{sa_summary or '[Add market-specific positioning]'}\n\n══════════════ YOUR ORIGINAL CV ══════════════\n{original_cv}"

        return {"ats_max": ats, "balanced": bal, "creative": cre}
