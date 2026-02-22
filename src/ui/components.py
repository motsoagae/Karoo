"""
Karoo v2.0 — Reusable UI Components
"""

def score_color(score: int) -> str:
    if score >= 80: return "#2E7D32"
    if score >= 60: return "#E65C00"
    return "#C62828"

def score_emoji(score: int) -> str:
    if score >= 85: return "🟢"
    if score >= 70: return "🟡"
    if score >= 55: return "🟠"
    return "🔴"

def format_bar(score: int, width: int = 10) -> str:
    filled = score // (100 // width)
    return "█" * filled + "░" * (width - filled)
