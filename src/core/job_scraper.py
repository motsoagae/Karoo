"""
ATS-GOD v2.0 — Job URL Scraper (NEW)
Extracts job descriptions from URLs: LinkedIn, Indeed, PNet, Careers24, Glassdoor, company sites.
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Platform-specific CSS selectors
PLATFORM_SELECTORS = {
    'linkedin.com': [
        '.job-details-jobs-unified-top-card__job-title',
        '.description__text',
        '.job-view-layout',
        'article',
    ],
    'indeed.com': [
        '#jobDescriptionText',
        '.jobsearch-JobComponent-description',
        '[data-testid="jobsearch-JobInfoHeader-title"]',
    ],
    'pnet.co.za': [
        '.job-description',
        '.job-content',
        'article.job',
    ],
    'careers24.com': [
        '.job-description',
        '.listing-detail',
        'section.description',
    ],
    'glassdoor.com': [
        '.jobDescriptionContent',
        '[data-test="jobDescriptionContent"]',
    ],
    'seek.com.au': [
        '[data-automation="jobAdDetails"]',
        '.FYwKg',
    ],
}

GENERIC_SELECTORS = [
    'article', 'main', '.job-description', '.job-details',
    '#job-description', '.description', '[class*="job-desc"]',
    '[class*="jobDesc"]', '[id*="jobDesc"]', '[class*="vacancy"]',
]


def scrape_job_url(url: str) -> Tuple[str, str]:
    """
    Scrape a job posting URL and return (extracted_text, source_platform).
    Returns ("", "") on failure.
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        logger.info(f"Scraping: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'lxml')

        # Remove noise
        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                         'iframe', 'noscript', '.cookie-banner']):
            tag.decompose()

        platform = _detect_platform(url)
        selectors = PLATFORM_SELECTORS.get(platform, []) + GENERIC_SELECTORS

        # Try platform-specific selectors first
        for selector in selectors:
            try:
                el = soup.select_one(selector)
                if el:
                    text = el.get_text(separator='\n', strip=True)
                    if len(text) > 200:
                        logger.info(f"Extracted {len(text)} chars from {platform or 'generic'}")
                        return _clean_text(text), platform or 'website'
            except Exception:
                continue

        # Fallback: largest text block
        all_text = soup.get_text(separator='\n', strip=True)
        cleaned = _clean_text(all_text)
        if len(cleaned) > 300:
            return cleaned[:8000], 'website (fallback)'

        return "", "failed"

    except ImportError:
        return "", "requests/beautifulsoup4 not installed — pip install requests beautifulsoup4 lxml"
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        return "", f"failed: {str(e)[:80]}"


def _detect_platform(url: str) -> str:
    platforms = list(PLATFORM_SELECTORS.keys())
    for p in platforms:
        if p in url:
            return p
    return ""


def _clean_text(text: str) -> str:
    # Collapse whitespace runs
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove cookie/legal boilerplate
    for pattern in [r'cookie[s]?\s+policy', r'privacy policy', r'terms of use',
                    r'©\s*\d{4}', r'all rights reserved']:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text.strip()[:8000]


def is_valid_url(url: str) -> bool:
    return bool(re.match(r'https?://', url.strip()))
