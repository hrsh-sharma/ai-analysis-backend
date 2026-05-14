import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = Path(__file__).parent.parent / "static" / "screenshots"
SCREENSHOT_TIMEOUT = 18  # seconds — hard kill if browser hangs


def _capture(url: str, file_path: Path, result: dict) -> None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
            page    = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(800)
            page.screenshot(path=str(file_path), full_page=False)
            browser.close()
            result["ok"] = True
    except Exception:
        result["ok"] = False


def take_screenshot(url: str) -> str | None:
    try:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c if c.isalnum() else "_" for c in url)[:60]
        filename  = f"{safe_name}_{abs(hash(url)) % 100000}.png"
        file_path = SCREENSHOTS_DIR / filename

        result: dict = {}
        t = threading.Thread(target=_capture, args=(url, file_path, result), daemon=True)
        t.start()
        t.join(timeout=SCREENSHOT_TIMEOUT)

        if t.is_alive() or not result.get("ok"):
            return None

        return f"/static/screenshots/{filename}"

    except Exception:
        return None
