import httpx
from bs4 import BeautifulSoup
import re


TECH_PATTERNS = [
    # Frameworks / Meta-frameworks
    {"name": "Next.js",      "category": "Framework",    "check": lambda h, html, _: "__NEXT_DATA__" in html or "/_next/" in html},
    {"name": "Nuxt.js",      "category": "Framework",    "check": lambda h, html, _: "__nuxt" in html or "/_nuxt/" in html},
    {"name": "Gatsby",       "category": "Framework",    "check": lambda h, html, _: "___gatsby" in html or "/gatsby-" in html},
    {"name": "React",        "category": "Framework",    "check": lambda h, html, _: "data-reactroot" in html or "react.development.js" in html or "__react" in html},
    {"name": "Vue.js",       "category": "Framework",    "check": lambda h, html, _: "data-v-app" in html or "vue.min.js" in html or "__vue_app__" in html},
    {"name": "Angular",      "category": "Framework",    "check": lambda h, html, _: "ng-version" in html or "angular.min.js" in html},
    {"name": "Svelte",       "category": "Framework",    "check": lambda h, html, _: "svelte-" in html or "__svelte" in html},
    {"name": "Remix",        "category": "Framework",    "check": lambda h, html, _: '"/build/manifest-' in html or "remix-" in html},

    # CMS
    {"name": "WordPress",    "category": "CMS",          "check": lambda h, html, _: "/wp-content/" in html or "/wp-includes/" in html},
    {"name": "Shopify",      "category": "E-commerce",   "check": lambda h, html, _: "cdn.shopify.com" in html or "Shopify.theme" in html},
    {"name": "Webflow",      "category": "CMS",          "check": lambda h, html, _: "webflow.com" in html or "wf-" in html},
    {"name": "Wix",          "category": "CMS",          "check": lambda h, html, _: "static.wixstatic.com" in html or "X-Wix-Published-Version" in h},
    {"name": "Squarespace",  "category": "CMS",          "check": lambda h, html, _: "squarespace.com" in html or "static1.squarespace.com" in html},
    {"name": "Ghost",        "category": "CMS",          "check": lambda h, html, _: "ghost.io" in html or "/ghost/api/" in html},

    # Analytics & Tracking
    {"name": "Google Analytics","category": "Analytics", "check": lambda h, html, _: "google-analytics.com" in html or "gtag(" in html or "UA-" in html},
    {"name": "Google Tag Manager","category": "Analytics","check": lambda h, html, _: "googletagmanager.com" in html or "GTM-" in html},
    {"name": "Hotjar",       "category": "Analytics",    "check": lambda h, html, _: "hotjar.com" in html or "hjSiteSettings" in html},
    {"name": "Mixpanel",     "category": "Analytics",    "check": lambda h, html, _: "mixpanel.com" in html or "mixpanel.track" in html},
    {"name": "Clarity",      "category": "Analytics",    "check": lambda h, html, _: "clarity.ms" in html or "clarity(" in html},
    {"name": "Segment",      "category": "Analytics",    "check": lambda h, html, _: "segment.com" in html or "analytics.js" in html},

    # CDN / Hosting
    {"name": "Cloudflare",   "category": "CDN",          "check": lambda h, html, _: "CF-Ray" in h or "cloudflare" in h.get("server","").lower()},
    {"name": "Vercel",       "category": "Hosting",      "check": lambda h, html, _: "x-vercel-id" in h or "vercel.app" in html},
    {"name": "Netlify",      "category": "Hosting",      "check": lambda h, html, _: "x-nf-request-id" in h or "netlify" in h.get("server","").lower()},
    {"name": "AWS",          "category": "Hosting",      "check": lambda h, html, _: "x-amz-cf-id" in h or "amazonaws.com" in html},
    {"name": "GitHub Pages", "category": "Hosting",      "check": lambda h, html, _: "github.io" in html or "github.com/pages" in h.get("x-github-request-id","")},

    # CSS Frameworks
    {"name": "Tailwind CSS", "category": "CSS",          "check": lambda h, html, soup: bool(soup.find(class_=re.compile(r'^(flex|grid|bg-|text-|p-|m-|w-|h-)')))},
    {"name": "Bootstrap",    "category": "CSS",          "check": lambda h, html, _: "bootstrap.min.css" in html or 'class="container' in html},
    {"name": "Bulma",        "category": "CSS",          "check": lambda h, html, _: "bulma.min.css" in html or "bulma.io" in html},

    # Fonts
    {"name": "Google Fonts", "category": "Fonts",        "check": lambda h, html, _: "fonts.googleapis.com" in html or "fonts.gstatic.com" in html},

    # Marketing / Support
    {"name": "Intercom",     "category": "Support",      "check": lambda h, html, _: "intercom.io" in html or "intercomcdn.com" in html},
    {"name": "HubSpot",      "category": "Marketing",    "check": lambda h, html, _: "hubspot.com" in html or "hs-scripts.com" in html},
    {"name": "Stripe",       "category": "Payments",     "check": lambda h, html, _: "js.stripe.com" in html},
    {"name": "reCAPTCHA",    "category": "Security",     "check": lambda h, html, _: "recaptcha" in html or "grecaptcha" in html},
]

CATEGORY_COLORS: dict[str, str] = {
    "Framework":  "#a78bfa",
    "CMS":        "#f472b6",
    "E-commerce": "#fb923c",
    "Analytics":  "#38bdf8",
    "CDN":        "#4ade80",
    "Hosting":    "#4ade80",
    "CSS":        "#fbbf24",
    "Fonts":      "#e879f9",
    "Support":    "#60a5fa",
    "Marketing":  "#f87171",
    "Payments":   "#34d399",
    "Security":   "#94a3b8",
}


def detect_tech_stack(url: str) -> list[dict]:
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (compatible; SiteAuditBot/1.0)"})
        html  = response.text
        headers = {k.lower(): v for k, v in response.headers.items()}
        soup  = BeautifulSoup(html, "lxml")

        detected = []
        for tech in TECH_PATTERNS:
            try:
                if tech["check"](headers, html, soup):
                    detected.append({
                        "name":     tech["name"],
                        "category": tech["category"],
                        "color":    CATEGORY_COLORS.get(tech["category"], "#94a3b8"),
                    })
            except Exception:
                continue

        return detected

    except Exception as e:
        return [{"name": "Detection failed", "category": "Error", "color": "#f87171", "error": str(e)}]
