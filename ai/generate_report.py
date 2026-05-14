import json
import re
import threading
from ai.client import ai_client, AI_MODEL
from ai.prompts import build_analysis_prompt

AI_TIMEOUT_SECONDS = 30


def _fix_json(s: str) -> str:
    return re.sub(r'\\(?!["\\/bfnrtux])', r'\\\\', s)


def _parse(content: str) -> dict:
    for attempt in [
        lambda s: json.loads(s),
        lambda s: json.loads(re.sub(r'^```(?:json)?\s*', '', re.sub(r'\s*```$', '', s.strip()))),
        lambda s: json.loads(_fix_json(re.sub(r'^```(?:json)?\s*', '', re.sub(r'\s*```$', '', s.strip())))),
        lambda s: json.loads(_fix_json(re.search(r'\{[\s\S]*\}', s).group())) if re.search(r'\{[\s\S]*\}', s) else (_ for _ in ()).throw(ValueError()),
    ]:
        try:
            return attempt(content)
        except Exception:
            continue
    raise ValueError(f"Could not parse AI response: {content[:300]}")


def _fallback_report(findings: dict) -> dict:
    """
    Return a basic scored report when the AI call fails or times out.
    Uses the raw analyzer data to produce scores without calling Groq.
    """
    seo = findings.get("seo", {})
    acc = findings.get("accessibility", {})
    perf = findings.get("performance", {})
    sec = findings.get("security", {})
    ux  = findings.get("ux", {})

    def seo_score() -> int:
        s = 100
        if not seo.get("has_title"):           s -= 20
        if not seo.get("has_meta_description"): s -= 15
        if seo.get("h1_count", 0) != 1:       s -= 10
        if not seo.get("has_canonical"):       s -= 5
        if not seo.get("has_og_title"):        s -= 5
        if seo.get("images_missing_alt", 0) > 0: s -= 5
        return max(0, s)

    def acc_score() -> int:
        v = acc.get("total_violations", 0)
        if v == 0: return 95
        if v <= 2: return 80
        if v <= 5: return 65
        if v <= 10: return 50
        return 30

    def perf_score() -> int:
        return perf.get("estimated_score", 60)

    def sec_score() -> int:
        missing = sec.get("missing_count", 0)
        if not sec.get("is_https"): return 20
        s = 100 - (missing * 12)
        return max(0, s)

    def ux_score() -> int:
        s = 70
        if ux.get("has_cta"):        s += 10
        if ux.get("has_navigation"): s += 10
        if ux.get("has_footer"):     s += 5
        if ux.get("has_mobile_viewport"): s += 5
        return min(100, s)

    cats = {
        "seo":           seo_score(),
        "accessibility": acc_score(),
        "performance":   perf_score(),
        "ux":            ux_score(),
        "design":        65,
        "security":      sec_score(),
    }

    return {
        "categories": {
            name: {
                "score":        score,
                "summary":      f"Automated score based on raw analysis data. AI report generation was unavailable.",
                "what_is_good": ["Analysis data was collected successfully"],
                "issues": [{
                    "severity":    "minor",
                    "title":       "AI analysis unavailable",
                    "description": "The AI report generator timed out. Raw scores are shown based on automated checks.",
                    "how_to_fix":  "Try analyzing the site again for a full AI-generated report.",
                }],
            }
            for name, score in cats.items()
        },
        "overall_summary": "Automated analysis completed. AI-generated insights were unavailable this time — try again for detailed recommendations.",
        "top_priorities": [
            "Re-run the analysis to get AI-generated recommendations",
            "Review the raw score data for quick insights",
        ],
    }


def _call_groq(prompt: str, result: dict) -> None:
    try:
        completion = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role":    "system",
                    "content": "You are a professional web auditor. Respond with valid JSON only. No markdown fences.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        result["content"] = completion.choices[0].message.content or ""
    except Exception as e:
        result["error"] = str(e)


def generate_ai_report(url: str, findings: dict) -> dict:
    prompt = build_analysis_prompt(url, findings)

    result: dict = {}
    thread = threading.Thread(target=_call_groq, args=(prompt, result), daemon=True)
    thread.start()
    thread.join(timeout=AI_TIMEOUT_SECONDS)

    # If AI timed out or errored → return fallback scores instead of failing
    if thread.is_alive() or "error" in result:
        return _fallback_report(findings)

    try:
        return _parse(result["content"])
    except Exception:
        return _fallback_report(findings)
