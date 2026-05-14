import time
import httpx
from bs4 import BeautifulSoup


def analyze_performance(url: str) -> dict:
    """
    Fast performance analysis without Lighthouse.
    Measures real HTTP metrics + resource counts from the HTML.
    Runs in ~2-3 seconds instead of 30-60s.
    """
    try:
        start = time.time()
        response = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SiteAuditBot/1.0)"},
        )
        load_time_ms = round((time.time() - start) * 1000)

        html        = response.text
        soup        = BeautifulSoup(html, "lxml")
        headers     = {k.lower(): v for k, v in response.headers.items()}
        page_size_kb = round(len(html.encode("utf-8")) / 1024, 1)

        # Resources
        scripts       = soup.find_all("script", src=True)
        stylesheets   = soup.find_all("link", rel=lambda r: r and "stylesheet" in r)
        images        = soup.find_all("img")
        images_no_lazy = [i for i in images if not i.get("loading") == "lazy"]

        # Render-blocking: sync scripts in <head>
        head = soup.find("head")
        blocking_scripts = []
        if head:
            for s in head.find_all("script", src=True):
                if not s.get("defer") and not s.get("async"):
                    blocking_scripts.append(s.get("src", ""))

        # Caching
        has_cache_control = "cache-control" in headers
        has_etag          = "etag" in headers
        cache_control     = headers.get("cache-control", "none")

        # Compression
        encoding = headers.get("content-encoding", "none")
        compressed = encoding in ("gzip", "br", "zstd", "deflate")

        # CDN hint
        cdn_headers = ("cf-ray", "x-cache", "x-cdn", "x-amz-cf-id", "x-vercel-id")
        uses_cdn = any(h in headers for h in cdn_headers)

        # Inline styles / scripts (signals poor separation)
        inline_styles   = len(soup.find_all("style"))
        inline_scripts  = len([s for s in soup.find_all("script") if not s.get("src")])

        # Score estimate
        score = 100
        if load_time_ms > 3000:  score -= 25
        elif load_time_ms > 1500: score -= 10
        if page_size_kb > 500:   score -= 15
        elif page_size_kb > 200: score -= 5
        if len(blocking_scripts) > 3: score -= 15
        elif len(blocking_scripts) > 0: score -= 5
        if not compressed:        score -= 10
        if not has_cache_control: score -= 5
        if len(images_no_lazy) > 5: score -= 10
        score = max(0, min(100, score))

        return {
            "estimated_score":        score,
            "load_time_ms":           load_time_ms,
            "page_size_kb":           page_size_kb,
            "total_scripts":          len(scripts),
            "total_stylesheets":      len(stylesheets),
            "total_images":           len(images),
            "images_without_lazy":    len(images_no_lazy),
            "render_blocking_scripts": blocking_scripts[:5],
            "render_blocking_count":  len(blocking_scripts),
            "uses_compression":       compressed,
            "compression_type":       encoding,
            "has_cache_control":      has_cache_control,
            "has_etag":               has_etag,
            "cache_control":          cache_control,
            "uses_cdn":               uses_cdn,
            "inline_style_blocks":    inline_styles,
            "inline_script_blocks":   inline_scripts,
            "redirect_count":         len(response.history),
            "final_url":              str(response.url),
            "status_code":            response.status_code,
        }

    except Exception as e:
        return {"error": str(e)}
