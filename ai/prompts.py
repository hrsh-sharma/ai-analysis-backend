import json


def _trim_findings(findings: dict) -> dict:
    """Keep all important signals. Only trim excessively long lists."""
    trimmed = {}

    if "seo" in findings:
        seo = dict(findings["seo"])
        seo["heading_structure"] = seo.get("heading_structure", [])[:12]
        trimmed["seo"] = seo

    if "accessibility" in findings:
        acc = dict(findings["accessibility"])
        acc["violations"] = acc.get("violations", [])[:10]
        trimmed["accessibility"] = acc

    if "performance" in findings:
        trimmed["performance"] = findings["performance"]

    if "security" in findings:
        sec = dict(findings["security"])
        ph = sec.get("present_headers", {})
        sec["present_headers"] = list(ph.keys()) if isinstance(ph, dict) else ph
        trimmed["security"] = sec

    if "ux" in findings:
        trimmed["ux"] = findings["ux"]

    return trimmed


def build_analysis_prompt(url: str, findings: dict) -> str:
    trimmed = _trim_findings(findings)

    return f"""You are a senior web development consultant writing a detailed, professional website audit report.

Website being audited: {url}

Raw data from automated analysis tools:
{json.dumps(trimmed, indent=2)}

Generate a thorough, expert-level audit report. Return ONLY a valid JSON object — no markdown fences, no explanation text outside the JSON.

Required JSON structure:
{{
  "categories": {{
    "seo": {{
      "score": <integer 0-100, be precise based on the data>,
      "summary": "<3-4 sentences describing the SEO state, specific to this site>",
      "what_is_good": [
        "<specific positive finding 1>",
        "<specific positive finding 2>",
        "<specific positive finding 3>"
      ],
      "issues": [
        {{
          "severity": "critical",
          "title": "<concise issue title>",
          "description": "<2-3 sentences: what is wrong, why it matters, what impact it has>",
          "how_to_fix": "<specific, technical, actionable fix — include actual HTML/code examples where relevant>"
        }},
        {{
          "severity": "major",
          "title": "...",
          "description": "...",
          "how_to_fix": "..."
        }},
        {{
          "severity": "minor",
          "title": "...",
          "description": "...",
          "how_to_fix": "..."
        }}
      ]
    }},
    "accessibility": {{
      "score": <integer 0-100>,
      "summary": "<3-4 specific sentences about accessibility state>",
      "what_is_good": ["<finding 1>", "<finding 2>"],
      "issues": [
        <3-5 issues minimum if score < 80, each with severity, title, description, how_to_fix>
      ]
    }},
    "performance": {{
      "score": <integer 0-100, use estimated_score and load_time_ms as primary signals>,
      "summary": "<3-4 sentences — mention actual load time, page size, compression status>",
      "what_is_good": ["<finding 1>", "<finding 2>"],
      "issues": [
        <3-5 detailed issues with specific fixes>
      ]
    }},
    "ux": {{
      "score": <integer 0-100>,
      "summary": "<3-4 sentences about navigation, CTAs, forms, user flow>",
      "what_is_good": ["<finding 1>", "<finding 2>"],
      "issues": [
        <3-5 detailed issues>
      ]
    }},
    "design": {{
      "score": <integer 0-100, infer from heading structure, content density, UX data>,
      "summary": "<3-4 sentences about visual design quality, typography, layout structure>",
      "what_is_good": ["<finding 1>", "<finding 2>"],
      "issues": [
        <2-4 design issues inferred from available data>
      ]
    }},
    "security": {{
      "score": <integer 0-100, based on HTTPS, missing headers, CSP etc>,
      "summary": "<3-4 sentences about security posture — name specific missing headers>",
      "what_is_good": ["<finding 1>", "<finding 2>"],
      "issues": [
        <list each missing security header as a separate issue with exact HTTP header fix>
      ]
    }}
  }},
  "overall_summary": "<4-5 sentences executive summary: overall health, biggest strengths, most critical problems, recommended focus areas>",
  "top_priorities": [
    "<Priority 1: most impactful fix — be specific, include the actual change needed>",
    "<Priority 2: second most impactful fix>",
    "<Priority 3: third most impactful fix>",
    "<Priority 4: fourth fix>",
    "<Priority 5: fifth fix>"
  ]
}}

Scoring guide:
- 90-100: Excellent — very few or no issues
- 75-89: Good — minor issues only
- 60-74: Needs Work — several issues affecting user experience
- 40-59: Poor — significant problems
- 0-39: Critical — serious failures

Critical rules:
1. Return ONLY the JSON object — nothing before or after it
2. Every category MUST have at least 3 issues if score < 85
3. how_to_fix MUST be specific and technical — include actual code/HTML/header examples
4. Descriptions MUST reference the actual data (mention real numbers, real values found)
5. what_is_good MUST have at least 2 items per category
6. Do NOT use generic advice — every recommendation must be specific to this website
"""
