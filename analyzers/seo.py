import httpx
from bs4 import BeautifulSoup


def analyze_seo(url: str) -> dict:
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (compatible; SiteAuditBot/1.0)"})
        soup = BeautifulSoup(response.text, "lxml")

        title_tag   = soup.find("title")
        title_text  = title_tag.get_text(strip=True) if title_tag else ""
        meta_desc   = soup.find("meta", attrs={"name": "description"})
        meta_content = meta_desc.get("content", "") if meta_desc else ""
        h1_tags     = soup.find_all("h1")
        images      = soup.find_all("img")
        imgs_no_alt = [i for i in images if not i.get("alt") or not i.get("alt", "").strip()]

        headings = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])[:20]:
            headings.append(f"{tag.name.upper()}: {tag.get_text(strip=True)[:60]}")

        robots_meta = soup.find("meta", attrs={"name": "robots"})

        return {
            "has_title":                bool(title_text),
            "title_text":               title_text,
            "title_length":             len(title_text),
            "title_ok":                 10 <= len(title_text) <= 60,
            "has_meta_description":     bool(meta_content),
            "meta_description_length":  len(meta_content),
            "meta_description_ok":      50 <= len(meta_content) <= 160,
            "has_h1":                   len(h1_tags) > 0,
            "h1_count":                 len(h1_tags),
            "has_canonical":            bool(soup.find("link", attrs={"rel": "canonical"})),
            "has_og_title":             bool(soup.find("meta", attrs={"property": "og:title"})),
            "has_og_description":       bool(soup.find("meta", attrs={"property": "og:description"})),
            "has_og_image":             bool(soup.find("meta", attrs={"property": "og:image"})),
            "images_missing_alt":       len(imgs_no_alt),
            "total_images":             len(images),
            "heading_structure":        headings,
            "has_structured_data":      bool(soup.find("script", attrs={"type": "application/ld+json"})),
            "robots_meta":              robots_meta.get("content") if robots_meta else None,
            "status_code":              response.status_code,
        }
    except Exception as e:
        return {"error": str(e)}
