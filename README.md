# 🤖 Karoo v2.0 — AI-Powered CV Optimizer

> **11 AI agents. Full CV rewrite. Interview prep. Salary intelligence. Job URL scraper.**
> Built for South Africa + International markets. Free with Groq.

[![CI](https://github.com/your-username/ats-god-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/ats-god-optimizer/actions)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.32+-red)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🆕 What's New in v2.0

| Feature | v1 | v2 |
|---|---|---|
| AI Agents | 9 agents | **11 agents** |
| CV Output | Suggestions only | **Full AI rewrite (3 variants)** |
| Interview Prep | ❌ | **✅ 6 questions + STAR frameworks** |
| Salary Intelligence | ❌ | **✅ SA + International benchmarks** |
| Job URL Scraper | ❌ | **✅ LinkedIn, PNet, Indeed, Careers24** |
| Export Formats | TXT + DOCX | **TXT + DOCX + PDF** |
| Visualisations | Basic | **Radar chart + gauge + bar charts** |
| Agent Weights | Static | **Market-adaptive (SA vs International)** |
| Retry Logic | None | **Exponential backoff on LLM failures** |

---

## 🤖 The 11 Agents

| # | Agent | Role | Weight |
|---|---|---|---|
| 1 | 🎯 Algorithm Breaker | ATS parser simulation (Taleo/Workday/Greenhouse) | 1.8× |
| 2 | 🇿🇦 SA Specialist | B-BBEE, NQF, EE Act, PNet/Careers24 | 2.0× SA |
| 3 | 🌍 Global Setter | US/UK/EU/APAC/ME markets, GDPR | 2.0× Intl |
| 4 | 👁️ 6-Second Scanner | Recruiter psychology, F-pattern, CV killers | 1.3× |
| 5 | 💼 Hiring Manager | Technical depth, evidence trails, vague claims | 1.2× |
| 6 | 📊 Semantic Matcher | TF-IDF cosine similarity, skill ontology | 1.1× |
| 7 | ⚖️ Compliance Guardian | GDPR, POPIA, truth verification | 1.2× |
| 8 | 🚀 Future Architect | 2025 skills, career trajectory, AI readiness | 0.9× |
| 9 | ✉️ Cover Letter Composer | Personalized, 3-paragraph, ATS-optimized letters | — |
| 10 | 🎤 Interview Coach | **NEW** — 6 questions, STAR, curveballs, closing Qs | 1.0× |
| 11 | 💰 Salary Intelligence | **NEW** — SA/Intl market rates, negotiation script | 0.8× |
| 12 | ✍️ CV Rewriter | **NEW** — Full AI rewrite in 3 styles | — |

---

## 🚀 Quick Start

### Option 1: GitHub Codespaces (zero setup)
1. Click **Code → Open with Codespaces**
2. Add `GROQ_API_KEY` to Codespace Secrets
3. Run: `streamlit run app.py`
4. Open port 8501

### Option 2: Local
```bash
git clone https://github.com/your-username/ats-god-optimizer.git
cd ats-god-optimizer
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
export PYTHONPATH=.
streamlit run app.py
```

### Get Free AI (Groq — 30 seconds)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (no credit card)
3. Create API key
4. Add to `.env`: `GROQ_API_KEY=gsk_your_key_here`

---

## 🏗️ Architecture

```
karoo-v2/
├── app.py                          # Streamlit frontend
├── requirements.txt
├── .env.example
├── .devcontainer/devcontainer.json # GitHub Codespaces config
├── .github/workflows/ci.yml        # CI/CD pipeline
├── src/
│   ├── agents/
│   │   ├── base_agent.py          # BaseAgent + AgentOutput
│   │   ├── algorithm_breaker.py   # Agent 1
│   │   ├── sa_specialist.py       # Agent 2
│   │   ├── global_setter.py       # Agent 3
│   │   ├── recruiter_scanner.py   # Agent 4
│   │   ├── hiring_manager_whisperer.py # Agent 5
│   │   ├── semantic_matcher.py    # Agent 6
│   │   ├── compliance_guardian.py # Agent 7
│   │   ├── future_architect.py    # Agent 8
│   │   ├── cover_letter_agent.py  # Agent 9
│   │   ├── interview_coach.py     # Agent 10 🆕
│   │   ├── salary_intelligence.py # Agent 11 🆕
│   │   └── cv_rewriter_agent.py   # Agent 12 🆕
│   ├── core/
│   │   ├── orchestrator.py        # Master coordinator
│   │   ├── exporter.py            # TXT + DOCX + PDF export
│   │   └── job_scraper.py         # URL → JD extraction 🆕
│   └── ui/
│       ├── charts.py              # Plotly visualisations 🆕
│       └── components.py          # Reusable UI components
└── tests/
    └── test_agents.py             # Full test suite (22 tests)
```

---

## 🌍 Supported AI Providers

| Provider | Cost | Models | Context |
|---|---|---|---|
| **Groq** | **Free** | llama-3.3-70b-versatile | 128k tokens |
| OpenAI | Paid | gpt-4o-mini, gpt-4o | 128k tokens |
| Anthropic | Paid | claude-haiku-4-5 | 200k tokens |
| Rule-Based | Free | None (pattern matching) | N/A |

---

## 🧪 Running Tests

```bash
# No API key needed — rule-based mode
export PYTHONPATH=.
pytest tests/ -v
```

Expected: **22 tests passing**

---

## 🔧 GitHub Secrets (for CI)

Add these in **Settings → Secrets → Actions**:
- `GROQ_API_KEY` — for AI-powered CI (optional, tests work without it)

---

## 📄 License
MIT — use freely, contribute back.
