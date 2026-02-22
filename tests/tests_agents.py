"""
Karoo v2.0 Test Suite
All tests run in rule-based mode (no API key needed).
Run: pytest tests/ -v
"""
import asyncio
import pytest

CV = """
Jane Smith
jane.smith@email.com | +27 82 123 4567 | linkedin.com/in/janesmith | github.com/janesmith

PROFESSIONAL SUMMARY
Senior Software Engineer with 9 years in fintech. Led teams of 8-12. Delivered 4 platform migrations.
Reduced system downtime by 45% through proactive monitoring and automated alerting.

EXPERIENCE

Senior Software Engineer | ABC Bank | Cape Town | 2020 – Present
- Spearheaded migration to microservices, reducing deployment time by 60%
- Led team of 10 engineers, improving sprint velocity by 35%
- Implemented CI/CD pipeline (GitHub Actions, Docker, Kubernetes) saving 25h/sprint
- Architected fraud detection processing R2.3B daily transactions

Software Engineer | XYZ FinTech | Johannesburg | 2016 – 2020
- Built Python FastAPI backend for 80,000 daily active users
- Reduced API response time from 1.8s to 180ms (90% improvement)
- Delivered 3 major releases, increasing user retention by 22%

Junior Developer | StartupCo | 2014 – 2016
- Developed React.js frontend for SaaS product with 5,000 users

EDUCATION
BSc Computer Science (NQF Level 7) | University of Cape Town | 2014

SKILLS
Python, Java, React.js, AWS, Docker, Kubernetes, PostgreSQL, Redis,
GitHub Actions, Terraform, Agile/Scrum, SQL, machine learning, automation
"""

JD = """
Senior Software Engineer — FinTech Innovation

We need a Senior Software Engineer for our Cape Town team.

Requirements:
- 5+ years software engineering
- Python, AWS, Docker, Kubernetes
- Microservices architecture experience
- Team leadership and mentoring
- Agile/Scrum methodology
- B-BBEE awareness preferred
- Financial systems experience
"""

CTX = {
    "target_market": "South Africa",
    "experience_level": "Senior",
    "industry": "FinTech",
    "target_role": "Senior Software Engineer"
}

def run(coro):
    loop = asyncio.new_event_loop()
    try: return loop.run_until_complete(coro)
    finally: loop.close()


def test_all_imports():
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
    from src.core.orchestrator import ATSGodOrchestrator
    from src.core.exporter import export_to_txt
    from src.core.job_scraper import is_valid_url
    print("✓ All 12 modules imported")


def test_algorithm_breaker():
    from src.agents.algorithm_breaker import AlgorithmBreaker
    r = run(AlgorithmBreaker(llm=None).analyze(CV, JD, CTX))
    assert r.agent_name == "The Algorithm Breaker"
    assert 0 <= r.score <= 100
    assert len(r.findings) >= 5
    assert len(r.recommendations) >= 1


def test_sa_specialist_nqf():
    from src.agents.sa_specialist import SASpecialist
    r = run(SASpecialist(llm=None).analyze(CV, JD, CTX))
    assert r.agent_name == "The South African Specialist"
    assert 0 <= r.score <= 100
    assert any("NQF" in f or "7" in f for f in r.findings)


def test_global_setter_clean():
    from src.agents.global_setter import GlobalSetter
    r = run(GlobalSetter(llm=None).analyze(CV, JD, CTX))
    assert r.score >= 40
    assert not any("NON-COMPLIANT" in f for f in r.findings)


def test_global_setter_gdpr_violation():
    from src.agents.global_setter import GlobalSetter
    dirty = CV + "\nMarital Status: Married | Religion: Christian | DOB: 1985-01-15"
    r = run(GlobalSetter(llm=None).analyze(dirty, JD, CTX))
    all_text = " ".join(r.findings + r.recommendations).lower()
    assert any(w in all_text for w in ["marital","religion","remove","gdpr"])


def test_recruiter_scanner():
    from src.agents.recruiter_scanner import RecruiterScanner
    killer_cv = CV + "\nResponsible for managing teams. Duties included reporting."
    r = run(RecruiterScanner(llm=None).analyze(killer_cv, JD, CTX))
    all_text = " ".join(r.findings + r.recommendations).lower()
    assert "responsible for" in all_text or "duties" in all_text or "replace" in all_text


def test_compliance_clean():
    from src.agents.compliance_guardian import ComplianceGuardian
    r = run(ComplianceGuardian(llm=None).analyze(CV, JD, CTX))
    assert r.score >= 50
    assert any("COMPLIANT" in f for f in r.findings)


def test_compliance_catches_id():
    from src.agents.compliance_guardian import ComplianceGuardian
    id_cv = CV + "\nID Number: 8501015000082\nMarried with 2 children"
    r = run(ComplianceGuardian(llm=None).analyze(id_cv, JD, CTX))
    all_text = " ".join(r.findings + r.recommendations).lower()
    assert any(w in all_text for w in ["id","popia","remove","sensitive","marital"])
    assert r.score < 90


def test_semantic_matcher():
    from src.agents.semantic_matcher import SemanticMatcher
    r = run(SemanticMatcher(llm=None).analyze(CV, JD, CTX))
    assert 0 <= r.score <= 100
    assert any("Cosine" in f for f in r.findings)


def test_future_architect():
    from src.agents.future_architect import FutureArchitect
    r = run(FutureArchitect(llm=None).analyze(CV, JD, CTX))
    assert 0 <= r.score <= 100
    assert any("Emerging" in f for f in r.findings)
    assert any("AI Readiness" in f for f in r.findings)  # v2 addition


def test_interview_coach():
    from src.agents.interview_coach import InterviewCoach
    r = run(InterviewCoach(llm=None).analyze(CV, JD, CTX))
    assert r.agent_name == "The Interview Coach"
    assert 0 <= r.score <= 100
    assert len(r.findings) >= 3


def test_salary_intelligence():
    from src.agents.salary_intelligence import SalaryIntelligence
    r = run(SalaryIntelligence(llm=None).analyze(CV, JD, CTX))
    assert r.agent_name == "The Salary Intelligence Agent"
    assert 0 <= r.score <= 100
    assert any("Market Rate" in f for f in r.findings)
    assert any("Industry Premium" in f for f in r.findings)


def test_job_scraper_url_validation():
    from src.core.job_scraper import is_valid_url
    assert is_valid_url("https://www.linkedin.com/jobs/view/123")
    assert is_valid_url("https://pnet.co.za/job/123")
    assert not is_valid_url("not-a-url")
    assert not is_valid_url("ftp://invalid.com")


def test_orchestrator_full_run():
    from src.core.orchestrator import ATSGodOrchestrator
    orch = ATSGodOrchestrator()
    results = run(orch.optimize(CV, JD, CTX, generate_cover_letter=False, rewrite_cv=False))
    assert "summary" in results
    assert "agent_results" in results
    assert "cv_variants" in results
    assert "action_items" in results
    assert len(results["agent_results"]) >= 8


def test_orchestrator_summary():
    from src.core.orchestrator import ATSGodOrchestrator
    orch = ATSGodOrchestrator()
    results = run(orch.optimize(CV, JD, CTX, generate_cover_letter=False, rewrite_cv=False))
    s = results["summary"]
    assert 0 <= s["overall_score"] <= 100
    assert 0 <= s["interview_probability"] <= 100
    assert s["recommended_variant"] in ["BALANCED", "ATS-MAX", "CREATIVE"]
    assert "weakest_area" in s
    assert "strongest_area" in s


def test_orchestrator_3_variants():
    from src.core.orchestrator import ATSGodOrchestrator
    orch = ATSGodOrchestrator()
    results = run(orch.optimize(CV, JD, CTX, generate_cover_letter=False, rewrite_cv=False))
    v = results["cv_variants"]
    assert all(k in v for k in ["ats_max","balanced","creative"])
    assert all(len(v[k]) > 50 for k in v)


def test_exporter_txt():
    from src.core.orchestrator import ATSGodOrchestrator
    from src.core.exporter import export_to_txt
    orch = ATSGodOrchestrator()
    results = run(orch.optimize(CV, JD, CTX, generate_cover_letter=False, rewrite_cv=False))
    txt = export_to_txt(results)
    assert "Karoo v2.0" in txt
    assert "OVERALL SCORE" in txt
    assert "PRIORITY ACTION ITEMS" in txt
    assert len(txt) > 1000


def test_agent_output_has_v2_fields():
    """v2-specific: verify execution_ms and ai_powered fields exist."""
    from src.agents.algorithm_breaker import AlgorithmBreaker
    r = run(AlgorithmBreaker(llm=None).analyze(CV, JD, CTX))
    assert hasattr(r, 'execution_ms')
    assert hasattr(r, 'ai_powered')
    assert r.ai_powered == False  # no API key in test
    assert r.execution_ms >= 0
