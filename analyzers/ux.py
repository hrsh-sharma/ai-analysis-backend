import httpx
from bs4 import BeautifulSoup

CTA_KEYWORDS = [
    "get started", "sign up", "try free", "buy now", "learn more",
    "contact us", "book", "order", "subscribe", "download", "start now",
    "get a quote", "request demo", "try it", "shop now",
]


def analyze_ux(url: str) -> dict:
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (compatible; SiteAuditBot/1.0)"})
        soup = BeautifulSoup(response.text, "lxml")

        # CTA detection
        cta_count = 0
        for el in soup.find_all(["a", "button"]):
            if any(kw in el.get_text(strip=True).lower() for kw in CTA_KEYWORDS):
                cta_count += 1

        # Navigation
        nav_tags  = soup.find_all("nav")
        nav_links = soup.select("nav a")

        # Forms
        forms  = soup.find_all("form")
        inputs = soup.find_all("input", type=lambda t: t not in ["hidden", "submit", "button"])
        inputs_no_label = [
            i for i in inputs
            if not i.get("aria-label")
            and not i.get("placeholder")
            and not (i.get("id") and soup.find("label", attrs={"for": i.get("id")}))
        ]

        # Readability
        paragraphs = soup.find_all("p")

        # Mobile
        viewport = soup.find("meta", attrs={"name": "viewport"})

        # Links
        all_links    = soup.find_all("a", href=True)
        ext_new_tab  = [a for a in all_links if a.get("target") == "_blank"]

        return {
            "has_cta":                 cta_count > 0,
            "cta_count":               cta_count,
            "has_navigation":          len(nav_tags) > 0,
            "nav_link_count":          len(nav_links),
            "has_search":              bool(
                soup.find("input", attrs={"type": "search"}) or
                soup.find("input", attrs={"name": "q"})
            ),
            "form_count":              len(forms),
            "inputs_without_label":    len(inputs_no_label),
            "total_inputs":            len(inputs),
            "has_footer":              bool(soup.find("footer")),
            "paragraph_count":         len(paragraphs),
            "has_mobile_viewport":     bool(viewport),
            "viewport_content":        viewport.get("content") if viewport else None,
            "external_links_new_tab":  len(ext_new_tab),
            "total_links":             len(all_links),
        }
    except Exception as e:
        return {"error": str(e)}
