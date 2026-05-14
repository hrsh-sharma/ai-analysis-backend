import httpx
from bs4 import BeautifulSoup


def analyze_accessibility(url: str) -> dict:
    """
    HTML-based accessibility checks — no browser, no Playwright.
    Runs in < 1 second. Covers the most impactful WCAG issues.
    """
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (compatible; SiteAuditBot/1.0)"})
        soup = BeautifulSoup(response.text, "lxml")

        # Images without alt text
        images          = soup.find_all("img")
        imgs_no_alt     = [i.get("src", "")[:60] for i in images if not i.get("alt") and not i.get("role") == "presentation"]

        # Inputs without labels
        inputs = soup.find_all("input", type=lambda t: t not in ["hidden", "submit", "button", "reset"])
        inputs_no_label = []
        for inp in inputs:
            has_label = (
                inp.get("aria-label") or
                inp.get("aria-labelledby") or
                inp.get("placeholder") or
                (inp.get("id") and soup.find("label", attrs={"for": inp.get("id")})) or
                inp.find_parent("label")
            )
            if not has_label:
                inputs_no_label.append(inp.get("name") or inp.get("type") or "unknown")

        # Heading hierarchy check
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        heading_levels    = [int(h.name[1]) for h in headings]
        skipped_headings  = []
        for i in range(1, len(heading_levels)):
            if heading_levels[i] - heading_levels[i - 1] > 1:
                skipped_headings.append(f"h{heading_levels[i-1]} → h{heading_levels[i]}")

        # HTML lang attribute
        html_tag   = soup.find("html")
        has_lang   = bool(html_tag and html_tag.get("lang"))

        # Links without accessible text
        links          = soup.find_all("a")
        links_no_text  = [a.get("href", "")[:50] for a in links if not a.get_text(strip=True) and not a.get("aria-label")]

        # Buttons without text
        buttons         = soup.find_all("button")
        buttons_no_text = len([b for b in buttons if not b.get_text(strip=True) and not b.get("aria-label")])

        # iframes without title
        iframes          = soup.find_all("iframe")
        iframes_no_title = len([f for f in iframes if not f.get("title")])

        # Tables without headers
        tables            = soup.find_all("table")
        tables_no_headers = len([t for t in tables if not t.find("th")])

        # Skip link
        has_skip_link = bool(soup.find("a", href="#main") or soup.find("a", href="#content") or
                             soup.find("a", string=lambda s: s and "skip" in s.lower()))

        # Focus styles (rough check)
        style_text     = " ".join(s.get_text() for s in soup.find_all("style"))
        has_focus_style = ":focus" in style_text

        violations = []

        if imgs_no_alt:
            violations.append({"id": "image-alt", "impact": "serious",
                                "description": f"{len(imgs_no_alt)} image(s) missing alt text"})
        if inputs_no_label:
            violations.append({"id": "label", "impact": "critical",
                                "description": f"{len(inputs_no_label)} form input(s) missing labels: {inputs_no_label[:3]}"})
        if skipped_headings:
            violations.append({"id": "heading-order", "impact": "moderate",
                                "description": f"Heading hierarchy skips: {', '.join(skipped_headings[:3])}"})
        if not has_lang:
            violations.append({"id": "html-has-lang", "impact": "serious",
                                "description": "HTML element missing lang attribute"})
        if links_no_text:
            violations.append({"id": "link-name", "impact": "serious",
                                "description": f"{len(links_no_text)} link(s) have no accessible text"})
        if buttons_no_text:
            violations.append({"id": "button-name", "impact": "critical",
                                "description": f"{buttons_no_text} button(s) have no accessible text"})
        if iframes_no_title:
            violations.append({"id": "frame-title", "impact": "serious",
                                "description": f"{iframes_no_title} iframe(s) missing title attribute"})
        if tables_no_headers:
            violations.append({"id": "table-headers", "impact": "moderate",
                                "description": f"{tables_no_headers} table(s) without header cells"})

        return {
            "violations":              violations,
            "total_violations":        len(violations),
            "critical_violations":     sum(1 for v in violations if v["impact"] == "critical"),
            "serious_violations":      sum(1 for v in violations if v["impact"] == "serious"),
            "moderate_violations":     sum(1 for v in violations if v["impact"] == "moderate"),
            "has_lang_attribute":      has_lang,
            "has_skip_link":           has_skip_link,
            "has_focus_styles":        has_focus_style,
            "images_missing_alt":      len(imgs_no_alt),
            "inputs_missing_label":    len(inputs_no_label),
            "skipped_heading_levels":  skipped_headings,
        }

    except Exception as e:
        return {"violations": [], "total_violations": 0, "critical_violations": 0,
                "serious_violations": 0, "moderate_violations": 0, "error": str(e)}
