import httpx

SECURITY_HEADERS = [
    ("strict-transport-security",  "HSTS"),
    ("x-frame-options",            "X-Frame-Options"),
    ("x-content-type-options",     "X-Content-Type-Options"),
    ("content-security-policy",    "Content-Security-Policy"),
    ("referrer-policy",            "Referrer-Policy"),
    ("permissions-policy",         "Permissions-Policy"),
]


def analyze_security(url: str) -> dict:
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (compatible; SiteAuditBot/1.0)"})
        headers = {k.lower(): v for k, v in response.headers.items()}

        present, missing = {}, []
        for key, name in SECURITY_HEADERS:
            if key in headers:
                present[name] = headers[key]
            else:
                missing.append(name)

        return {
            "is_https":           url.startswith("https://"),
            "redirects_to_https": str(response.url).startswith("https://"),
            "present_headers":    present,
            "missing_headers":    missing,
            "missing_count":      len(missing),
            "has_hsts":           "strict-transport-security" in headers,
            "has_csp":            "content-security-policy" in headers,
            "has_x_frame":        "x-frame-options" in headers,
            "server_header":      headers.get("server"),
            "x_powered_by":       headers.get("x-powered-by"),
            "status_code":        response.status_code,
        }
    except Exception as e:
        return {"error": str(e)}
